from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('location','points', 'profile_pics', 'total_harvest', 'total_waste')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('location','points', 'profile_pics', 'total_harvest', 'total_waste')}),
    )
    list_display = ('email', 'points', 'profile_pics', 'total_harvest', 'total_waste')

admin.site.register(CustomUser, CustomUserAdmin)
