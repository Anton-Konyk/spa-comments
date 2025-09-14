from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SpaUser


@admin.register(SpaUser)
class SpaUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_active", "avatar")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("avatar",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("avatar",)}),
    )
