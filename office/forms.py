from .models import UserPosition, UserOffice, Schedule
from django import forms
from django.conf import settings


class UserPositionForm(forms.ModelForm):
    class Meta:
        model = UserPosition
        fields = ('type_action',)
        widgets = {
            'type_action': forms.HiddenInput()
        }


class UserOfficeFilter(forms.Form):
    date_created_gte = forms.DateTimeField(widget=forms.DateInput())
    date_created_lte = forms.DateTimeField(widget=forms.DateInput())
    id__in = forms.ModelMultipleChoiceField(
        queryset=UserOffice.objects.filter(user__groups__name__in=settings.USERS_GROUPS),
        widget=forms.SelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key, field in self.fields.items():
            field.required = False
            field.label = ''
            field.widget.attrs['placeholder'] = field.label


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = '__all__'
