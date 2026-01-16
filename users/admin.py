from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'avatar_display', 'projects_count', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'avatar_preview')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'avatar', 'avatar_preview')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    # === КАСТОМНЫЕ МЕТОДЫ ===
    @admin.display(description='Аватар')
    def avatar_display(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return '🖼️'
    avatar_display.short_description = 'Аватар'

    @admin.display(description='Превью аватара')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; border-radius: 8px; object-fit: cover; margin-top: 10px;" />',
                obj.avatar.url
            )
        return 'Аватар не загружен'
    avatar_preview.short_description = 'Предпросмотр'

    @admin.display(description='Проектов', ordering='projects_count')
    def projects_count(self, obj):
        return obj.projects.count()