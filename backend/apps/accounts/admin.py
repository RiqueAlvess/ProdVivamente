from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import ProgrammingError, connection
from django_tenants.admin import TenantAdminMixin

from .models import UserProfile, AuditLog


def _is_tenant_schema():
    return connection.schema_name != 'public'


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    filter_horizontal = ['unidades_permitidas', 'setores_permitidos']
    extra = 1

    def get_queryset(self, request):
        try:
            return super().get_queryset(request)
        except ProgrammingError:
            return UserProfile.objects.none()


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_role']

    def get_inlines(self, request, obj):
        if _is_tenant_schema():
            return [UserProfileInline]
        return []

    def get_list_filter(self, request):
        base = ['is_staff', 'is_active']
        if _is_tenant_schema():
            base.append('profile__role')
        return base

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except (UserProfile.DoesNotExist, ProgrammingError, AttributeError):
            return '-'
    get_role.short_description = 'Papel'


# Re-register UserAdmin with inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['user', 'role', 'telefone', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['unidades_permitidas', 'setores_permitidos']


@admin.register(AuditLog)
class AuditLogAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['user', 'acao', 'ip', 'created_at']
    list_filter = ['acao', 'created_at']
    search_fields = ['user__username', 'descricao', 'ip']
    readonly_fields = ['user', 'acao', 'descricao', 'ip', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
