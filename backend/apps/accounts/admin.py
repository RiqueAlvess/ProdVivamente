from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, AuditLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    filter_horizontal = ['unidades_permitidas', 'setores_permitidos']
    extra = 1


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_role', 'get_empresa']
    inlines = [UserProfileInline]
    list_filter = ['is_staff', 'is_active', 'profile__role']

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except (UserProfile.DoesNotExist, AttributeError):
            return '-'
    get_role.short_description = 'Papel'

    def get_empresa(self, obj):
        try:
            return obj.profile.empresa.nome if obj.profile.empresa else '-'
        except (UserProfile.DoesNotExist, AttributeError):
            return '-'
    get_empresa.short_description = 'Empresa'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'empresa', 'role', 'telefone', 'created_at']
    list_filter = ['role', 'empresa']
    search_fields = ['user__username', 'user__email', 'empresa__nome']
    filter_horizontal = ['unidades_permitidas', 'setores_permitidos']
    raw_id_fields = ['empresa']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'empresa', 'acao', 'ip', 'created_at']
    list_filter = ['acao', 'empresa', 'created_at']
    search_fields = ['user__username', 'descricao', 'ip']
    readonly_fields = ['user', 'empresa', 'acao', 'descricao', 'ip', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
