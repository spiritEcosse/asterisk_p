from __future__ import absolute_import, unicode_literals

import datetime
import subprocess

from celery import task
from django.conf import settings

from office.models import UserPosition


@task
def disconnect_users():
    now = datetime.datetime.now()
    print('datetime.date.today() ====', now)

    if tuple(settings.CRONTAB_TASK.values()) == (now.hour, now.minute):
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

            user_pos = UserPosition.objects.create(user=user_pos.user, type_action=UserPosition.ACTIONS[1][0])
            date_created = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=23, minute=59)
            user_pos.date_created = date_created
            user_pos.save()

            bashCommand = ["asterisk", "-rx",
                           "queue remove member Local/{}@from-queue/n from 228".format(
                               user_pos.user.number
                           )]
            subprocess.Popen(bashCommand, stdout=subprocess.PIPE)
