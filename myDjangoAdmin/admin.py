# myDjangoAdmin/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import Admin, Staff, LibraryUser, Genre, Book, LibraryUserOutstandingToken
from myserver.models import FavoriteBook, RecentlyViewed, BookingCart, BorrowedBook, ReservedBook
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

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

class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)  
    search_fields = ('name',) 

admin.site.register(Genre, GenreAdmin)

class BookAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'short_title', 'author', 'publisher', 'copies', 'short_description',
        'created_at', 'isbn', 'published_date', 'barcode_code',  'display_genres',
        'display_cover_image', 'display_barcode_image', 'display_extra_images'
    )
    list_filter = ('genres', 'publisher', 'published_date')
    search_fields = ('id', 'title', 'author', 'isbn', 'publisher')
    readonly_fields = ('id', 'display_cover_image', 'display_barcode_image', 'display_extra_images')

    fieldsets = (
        (None, {
            'fields': (
                'title', 'author', 'isbn', 'publisher', 'published_date',
                'copies', 'description', 'barcode_code',
                'cover_image', 'display_cover_image',
                'barcode_image', 'display_barcode_image',
                'extra_image_1', 'extra_image_2', 'extra_image_3', 'extra_image_4', 'extra_image_5',
                'display_extra_images',
                'genres',
            )
        }),
    )
    ordering = ('-created_at',)

    def short_title(self, obj):
        return Truncator(obj.title).chars(40)
    short_title.short_description = 'Title'

    def short_description(self, obj):
        return Truncator(obj.description).chars(60)
    short_description.short_description = 'Description'

    def display_genres(self, obj):
        return obj.genres.name if obj.genres else "N/A"
    display_genres.short_description = 'Genre'

    def display_cover_image(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="height: 100px;" />', obj.cover_image.url)
        return "No Cover"
    display_cover_image.short_description = "Cover Image"

    def display_barcode_image(self, obj):
        if obj.barcode_image:
            return format_html('<img src="{}" style="height: 100px;" />', obj.barcode_image.url)
        return "No Barcode"
    display_barcode_image.short_description = "Barcode Image"

    def display_extra_images(self, obj):
        extra_images = [obj.extra_image_1, obj.extra_image_2, obj.extra_image_3, obj.extra_image_4, obj.extra_image_5]
        images_html = "".join([
            f'<img src="{image.url}" style="height: 75px; margin-right: 5px;" />' 
            for image in extra_images if image
        ])
        return mark_safe(images_html if images_html else "No Extra Images")
    display_extra_images.short_description = "Extra Images"

admin.site.register(Book, BookAdmin)

class FavoriteBookAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'added_at')
    search_fields = ('user__email', 'book__title')
    list_filter = ('added_at',)

admin.site.register(FavoriteBook, FavoriteBookAdmin)

class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'viewed_at')
    search_fields = ('user__email', 'book__title')
    list_filter = ('viewed_at',)
    ordering = ('-viewed_at',)

admin.site.register(RecentlyViewed, RecentlyViewedAdmin)

class BookingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'added_at')
    search_fields = ('user__email', 'book__title')
    list_filter = ('added_at',)
    ordering = ('-added_at',)

admin.site.register(BookingCart, BookingCartAdmin)

class BorrowedBookAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'borrowed_at',)
    search_fields = ('user__email', 'book__title')
    list_filter = ('borrowed_at',)
    ordering = ('-borrowed_at',)

admin.site.register(BorrowedBook, BorrowedBookAdmin)

class ReservedBookAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'reserved_at',)
    search_fields = ('user__email', 'book__title')
    list_filter = ('reserved_at',)
    ordering = ('-reserved_at',)

admin.site.register(ReservedBook, ReservedBookAdmin)

# @admin.register(LibraryUserOutstandingToken)
# class LibraryUserOutstandingTokenAdmin(admin.ModelAdmin):
#     list_display = ('user', 'token', 'created_at', 'blacklisted')
#     search_fields = ('user__email', 'token')
#     list_filter = ('blacklisted', 'created_at')

# Register other models here if needed
