from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from office.models import UserOffice

admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserOffice
    fields = ('number', )

class UserProfileAdmin(UserAdmin):
    inlines = [ UserProfileInline, ]

admin.site.register(User, UserProfileAdmin)
