from django.contrib import admin

from .models import (
    User, Subscription
)


class SubscriptionAdmin(admin.TabularInline):
    model = Subscription
    fk_name = 'follower'
    fields = ['author']
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['pk', 'email', 'username', 'first_name', 'last_name']
    inlines = [SubscriptionAdmin]
    readonly_fields = ['pk', 'groups', 'user_permissions', 'last_login']

