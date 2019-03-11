from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

ACTIONS = (
    (0, _("Join")),
    (1, _("Disconnect")),
    (2, _("Pause")),
    (3, _("Restore"))
)


class UserOffice(models.Model):
    number = models.IntegerField(unique=True, blank=False, null=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_action = models.IntegerField(default=ACTIONS[1][0])

    def __str__(self):
        return str(self.number)

    class Meta:
        ordering = ['id']


class UserPosition(models.Model):
    ACTIONS = ACTIONS
    user = models.ForeignKey(UserOffice, on_delete=models.CASCADE, related_name='user_position')
    date_created = models.DateTimeField(auto_now_add=True)
    type_action = models.IntegerField(choices=ACTIONS)

    class Meta:
        ordering = ['id']


class Schedule(models.Model):
    POSITIONS = (
        ('', "----"),
        (0, _("Off")),
        (1, 8),
        (2, 9),
        (3, 11),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedule')
    date = models.DateField()
    position = models.IntegerField(choices=POSITIONS)

    def __str__(self):
        return str(self.user.id)

    class Meta:
        ordering = ['id']
