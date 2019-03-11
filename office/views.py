from __future__ import absolute_import, unicode_literals

import calendar
import datetime
import json
import subprocess

from dateutil import relativedelta
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import edit
from easy_pdf.rendering import render_to_pdf_response

from asterisk.settings import ADMIN_GROUPS
from asterisk.utils import GroupRequiredMixin
from .forms import UserOfficeFilter, UserPositionForm, ScheduleForm
from .models import UserOffice, UserPosition, Schedule
from django.conf import settings
from django.views import View


class UserOfficeList(GroupRequiredMixin, edit.FormMixin, generic.ListView):
    model = UserOffice
    paginate_by = 1000
    group_required = ADMIN_GROUPS
    form_class = UserOfficeFilter
    pdf_template = "office/pdf.html"

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return render_to_pdf_response(request, self.pdf_template, self.get_context_data())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs.update({
            'data': self.request.GET,
        })

        return kwargs

    def get_dict_query(self):
        dict_query = {}
        form = self.get_form()

        if form.is_valid():
            for key, value in form.cleaned_data.items():
                if value:
                    dict_query[key] = value

        gte = dict_query.pop(
            'date_created_gte', datetime.date.today()
        )
        self.initial['date_created_gte'] = gte
        lte = dict_query.pop(
            'date_created_lte', datetime.date.today()
        )
        self.initial['date_created_lte'] = lte
        gte_min = datetime.datetime.combine(gte, datetime.time.min)
        lte_max = datetime.datetime.combine(lte, datetime.time.max)
        dict_query['user_position__date_created__range'] = (gte_min, lte_max)

        return dict_query

    def get_queryset(self):
        return super().get_queryset(). \
            filter(user_position__isnull=False, **self.get_dict_query()). \
            annotate(date=TruncDay('user_position__date_created')). \
            annotate(Count('id')). \
            order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['actions'] = UserPosition.ACTIONS
        context['get_params'] = self.request.GET.copy()
        context['get_params'].pop('page', None)
        context['form'] = self.form_class(initial=self.get_initial())

        for obj in context['object_list']:
            user_position = obj.user_position.filter(
                date_created__range=(
                    datetime.datetime.combine(obj.date, datetime.time.min),
                    datetime.datetime.combine(obj.date, datetime.time.max)
                )
            )
            obj.type_action_2_3 = user_position.filter(
                type_action__in=[2, 3]
            ).order_by('id')
            obj.type_action_0 = user_position.filter(type_action=0).first()
            obj.type_action_1 = user_position.filter(type_action=1).last()
            obj.begin_change = Schedule.objects.filter(
                date=datetime.date(obj.date.year, obj.date.month, obj.date.day),
                user=obj.user
            ).first()

        return context


class UserPositionCreate(generic.list.MultipleObjectMixin, generic.CreateView):
    form_class = UserPositionForm
    model = UserPosition
    success_url = reverse_lazy('office:create')

    def dispatch(self, request, *args, **kwargs):
        if request.user.groups.filter(name__in=ADMIN_GROUPS):
            return HttpResponseRedirect(reverse_lazy('office:list'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        self.object = None

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_queryset(self):
        return super().get_queryset().filter(
            user=self.request.user.useroffice,
            date_created__range=(
                datetime.datetime.combine(datetime.date.today(), datetime.time.min),
                datetime.datetime.combine(datetime.date.today(), datetime.time.max)
            )
        ).order_by('id')

    def form_valid(self, form):
        bashCommand = []

        type_action = form.cleaned_data['type_action']

        if type_action == 0:
            bashCommand = ["asterisk", "-rx", "queue add member Local/{}@from-queue/n to 228".format(self.request.user.useroffice.number)]
        elif type_action == 1:
            bashCommand = ["asterisk", "-rx", "queue remove member Local/{}@from-queue/n from 228".format(self.request.user.useroffice.number)]
        elif type_action == 2:
            bashCommand = ["asterisk", "-rx", "queue pause member Local/{}@from-queue/n".format(self.request.user.useroffice.number)]
        elif type_action == 3:
            bashCommand = ["asterisk", "-rx", "queue unpause member Local/{}@from-queue/n".format(self.request.user.useroffice.number)]

        subprocess.Popen(bashCommand, stdout=subprocess.PIPE)

        obj = form.save(commit=False)
        obj.user = self.request.user.useroffice
        obj.save()
        self.request.user.useroffice.current_action = obj.type_action
        self.request.user.useroffice.save()

        return super().form_valid(form)


class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return HttpResponse(self.get_data(context), content_type="application/json")

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        return json.dumps(context)


class ScheduleCreate(JSONResponseMixin, edit.CreateView):
    model = Schedule
    form_class = ScheduleForm
    success_url = reverse_lazy('office:schedule')

    def form_valid(self, form):
        super(ScheduleCreate, self).form_valid(form=form)
        return self.render_to_json_response(self.get_context_data_ajax())
    
    def get(self, request, *args, **kwargs):
        self.date = datetime.date.today()

        if 'date' in self.request.GET:
            self.date = datetime.datetime.strptime(self.request.GET['date'], '%Y-%m')

        return super(ScheduleCreate, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        return super(ScheduleCreate, self).get_queryset().filter(
            date__year=self.date.year, date__month=self.date.month
        )

    def get_context_data(self, **kwargs):
        context = super(ScheduleCreate, self).get_context_data(**kwargs)
        context['users'] = User.objects.filter(
            groups__name__in = settings.USERS_GROUPS
        )
        num_days = calendar.monthrange(self.date.year, self.date.month)[1]
        context['days'] = [datetime.date(self.date.year, self.date.month, day) for day in range(1, num_days + 1)]
        context['object_list'] = self.get_queryset()
        context['today'] = datetime.date.today()
        context['date_select'] = self.date
        context['prev'] = self.date - relativedelta.relativedelta(months=1)
        context['next'] = self.date + relativedelta.relativedelta(months=1)
        return context

    def get_context_data_ajax(self, **kwargs):
        return {'id': self.object.id}


class ScheduleUpdate(edit.UpdateView):
    model = Schedule
    form_class = ScheduleForm
    success_url = reverse_lazy('office:schedule')


class DisconnectUsers(View):
    def get(self, request, *args, **kwargs):
        users = UserPosition.objects.exclude(
            user__current_action=UserPosition.ACTIONS[1][0],
        ).filter(
            user__user__groups__name__in=settings.USERS_GROUPS,
            date_created__range=(
                datetime.datetime.combine(datetime.date.today(), datetime.time.min),
                datetime.datetime.combine(datetime.date.today(), datetime.time.max)
            )).distinct('user_id').order_by('user_id')

        print('datetime.date.today() ====', datetime.date.today())
        print('datetime.datetime.combine(datetime.date.today(), datetime.time.min) ====', datetime.datetime.combine(datetime.date.today(), datetime.time.min))
        print('datetime.datetime.combine(datetime.date.today(), datetime.time.max) ====', datetime.datetime.combine(datetime.date.today(), datetime.time.max))
        print('users ====',users)

        for user_pos in users:
            user_pos.user.current_action = UserPosition.ACTIONS[1][0]
            user_pos.user.save()

            UserPosition.objects.create(user=user_pos.user, type_action=UserPosition.ACTIONS[1][0])
            bashCommand = ["asterisk", "-rx",
                           "queue remove member Local/{}@from-queue/n from 228".format(
                               user_pos.user.number
                           )]
            subprocess.Popen(bashCommand, stdout=subprocess.PIPE)
        return HttpResponse('All users disconnected!')
