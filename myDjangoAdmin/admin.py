# myDjangoAdmin/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from .models import Admin, Staff, LibraryUser

class LastSeenMixin:
    def time_since_last_seen(self, obj):
        if hasattr(obj, 'last_seen') and obj.last_seen:
            time_diff = timezone.now() - obj.last_seen
            if time_diff < timezone.timedelta(seconds=60):
                return format_html('<span style="color: green;">Online</span>')
            elif time_diff < timezone.timedelta(hours=1):
                return format_html('<span style="color: red;">Offline {} minute(s) ago</span>', time_diff.seconds // 60)
            elif time_diff < timezone.timedelta(days=1):
                return format_html('<span style="color: red;">Offline {} hour(s) ago</span>', time_diff.seconds // 3600)
            else:
                return format_html('<span style="color: red;">Offline {} day(s) ago</span>', time_diff.days)
        else:
            return format_html('<span style="color: red;">Offline</span>')

    time_since_last_seen.short_description = 'Online Status'

class AdminAdmin(UserAdmin):
    model = Admin
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'created_at', 'updated_at')
    search_fields = ('email', 'first_name', 'last_name', 'role')
    list_filter = ('is_active', 'role', 'is_staff', 'is_superuser')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(Admin, AdminAdmin)

class StaffAdmin(UserAdmin, LastSeenMixin):
    model = Staff
    list_display = ('staff_id', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'time_since_last_seen')
    search_fields = ('email', 'first_name', 'last_name', 'role')
    list_filter = ('is_active', 'role')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'middle_name', 'age', 'birthday', 'address', 'role', 'staff_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'middle_name', 'age', 'birthday', 'address', 'role', 'is_staff', 'is_superuser'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and obj.password:
            obj.set_password(obj.password)
        elif 'password' in form.changed_data:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)

    actions = ['delete_selected']

    def has_change_permission(self, request, obj=None):
        return True

admin.site.register(Staff, StaffAdmin)

class UserAdminCustom(UserAdmin, LastSeenMixin):
    model = LibraryUser
    list_display = ('email', 'full_name', 'id_number', 'is_staff', 'is_superuser', 'time_since_last_seen')
    search_fields = ('email', 'full_name', 'id_number')
    list_filter = ('is_active',)
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'id_number', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'id_number', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(LibraryUser, UserAdminCustom)

# Register other models here if needed
