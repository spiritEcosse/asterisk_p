import locale

from django import template
from django.conf import settings

from office.models import Schedule

register = template.Library()

@register.filter
def day_name(date):
    locale.setlocale(locale.LC_ALL, settings.LOCALE)
    return date.strftime('%a')

@register.simple_tag(takes_context=True)
def exist_schedule(context, user, date):
    for obj in context['object_list']:
        if obj.user == user and obj.date == date:
            return obj

    if date.weekday() == 6:
        return Schedule.objects.create(date=date, user=user, position=Schedule.POSITIONS[1][0])


@register.filter
def set_time(value):
    return str(value) + ':00' if type(value) is int else value