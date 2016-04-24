from django.contrib import admin
from django.contrib.auth.models import User

import sbuser.models


admin.site.register(sbuser.models.Profile)


class PlaysInline(admin.TabularInline):
    model = sbuser.models.UserPlays


class UserWithInlines(admin.ModelAdmin):
    inlines = [
        PlaysInline,
    ]


admin.site.unregister(User)
admin.site.register(User, UserWithInlines)
