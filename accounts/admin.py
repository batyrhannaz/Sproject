from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ParentStudentRelation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'display_name', 'role', 'linked_gmail', 'phone', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'preferred_language', 'font_size')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'linked_gmail', 'phone')
    ordering = ('role', 'last_name', 'first_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Настройки профиля школьного портала', {
            'fields': ('role', 'phone', 'linked_gmail', 'avatar', 'preferred_language', 'font_size'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Настройки профиля школьного портала', {
            'fields': ('role', 'first_name', 'last_name', 'email', 'linked_gmail', 'phone'),
        }),
    )


@admin.register(ParentStudentRelation)
class ParentStudentRelationAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'relation_type', 'created_at')
    list_filter = ('relation_type',)
    search_fields = ('parent__first_name', 'parent__last_name', 'student__first_name', 'student__last_name')
