from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, AuditLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    filter_horizontal = ['empresas', 'unidades_permitidas', 'setores_permitidos']
    extra = 1


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_role']
    list_filter = ['is_staff', 'is_active', 'profile__role']

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'
    get_role.short_description = 'Papel'


# Re-register UserAdmin with inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'get_empresas', 'telefone', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['empresas', 'unidades_permitidas', 'setores_permitidos']

    def get_empresas(self, obj):
        return ', '.join(obj.empresas.values_list('nome', flat=True))
    get_empresas.short_description = 'Empresas'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'empresa', 'acao', 'ip', 'created_at']
    list_filter = ['acao', 'created_at', 'empresa']
    search_fields = ['user__username', 'descricao', 'ip']
    readonly_fields = ['user', 'empresa', 'acao', 'descricao', 'ip', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
