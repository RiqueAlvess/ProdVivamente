import secrets
import string

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django_tenants.admin import TenantAdminMixin
from django_tenants.utils import tenant_context

from .models import Domain, Empresa


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + '!@#$'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _provision_admin_user(empresa, email, password=None):
    """
    Create (or reset) an RH admin user inside the tenant's schema.
    Returns (user, created, password).
    """
    if password is None:
        password = _generate_password()

    with tenant_context(empresa):
        from apps.accounts.models import UserProfile

        base_username = email.split('@')[0]
        username = base_username
        n = 1
        while User.objects.exclude(email=email).filter(username=username).exists():
            username = f'{base_username}{n}'
            n += 1

        try:
            user = User.objects.get(email=email)
            created = False
        except User.DoesNotExist:
            user = User(username=username, email=email, is_staff=True, is_active=True)
            created = True

        user.set_password(password)
        user.save()

        UserProfile.objects.get_or_create(user=user, defaults={'role': 'rh'})

    return user, created, password


@admin.register(Empresa)
class EmpresaAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['nome', 'schema_name', 'cnpj', 'admin_email', 'ativo', 'status_admin', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'cnpj', 'schema_name', 'admin_email']
    prepopulated_fields = {'slug': ('nome',)}
    readonly_fields = ['created_at', 'updated_at']
    actions = ['provisionar_admin', 'ativar_tenants', 'desativar_tenants']

    fieldsets = (
        ('Tenant', {
            'fields': ('schema_name', 'slug', 'ativo'),
        }),
        ('Informações Básicas', {
            'fields': ('nome', 'cnpj', 'total_funcionarios', 'cnae', 'cnae_descricao'),
        }),
        ('Administrador RH', {
            'fields': ('admin_email',),
            'description': (
                'Informe o e-mail do usuário RH que gerenciará esta empresa. '
                'Ao salvar um novo tenant, o usuário será provisionado automaticamente '
                'e as credenciais exibidas aqui.'
            ),
        }),
        ('Personalização', {
            'fields': ('logo_url', 'favicon_url', 'cor_primaria', 'cor_secundaria', 'cor_fonte', 'nome_app'),
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Admin RH')
    def status_admin(self, obj):
        if not obj.admin_email:
            return '⚠ Sem e-mail'
        try:
            with tenant_context(obj):
                exists = User.objects.filter(email=obj.admin_email, is_active=True).exists()
            return '✓ Provisionado' if exists else '✗ Não criado'
        except Exception:
            return '? Schema não encontrado'

    def save_model(self, request, obj, form, change):
        is_new = not change
        super().save_model(request, obj, form, change)

        if is_new and obj.admin_email:
            try:
                user, created, password = _provision_admin_user(obj, obj.admin_email)
                action = 'criado' if created else 'senha atualizada para'
                self.message_user(
                    request,
                    (
                        f'✓ Tenant "{obj.nome}" criado. '
                        f'Usuário admin {action}: {obj.admin_email} | Senha: {password} '
                        f'— Anote agora, não será exibida novamente.'
                    ),
                    level=messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Tenant criado, mas falha ao provisionar admin: {e}',
                    level=messages.WARNING,
                )

    @admin.action(description='Provisionar / Resetar senha do Admin RH')
    def provisionar_admin(self, request, queryset):
        erros = []
        for empresa in queryset:
            if not empresa.admin_email:
                erros.append(f'{empresa.nome}: sem admin_email configurado.')
                continue
            try:
                user, created, password = _provision_admin_user(empresa, empresa.admin_email)
                action = 'criado' if created else 'senha resetada'
                self.message_user(
                    request,
                    (
                        f'[{empresa.nome}] Admin {action}: '
                        f'{empresa.admin_email} | Senha: {password}'
                    ),
                    level=messages.SUCCESS,
                )
            except Exception as e:
                erros.append(f'{empresa.nome}: {e}')

        if erros:
            self.message_user(request, 'Erros: ' + ' | '.join(erros), level=messages.ERROR)

    @admin.action(description='Ativar tenants selecionados')
    def ativar_tenants(self, request, queryset):
        updated = queryset.update(ativo=True)
        self.message_user(request, f'{updated} tenant(s) ativado(s).', level=messages.SUCCESS)

    @admin.action(description='Desativar tenants selecionados')
    def desativar_tenants(self, request, queryset):
        updated = queryset.update(ativo=False)
        self.message_user(request, f'{updated} tenant(s) desativado(s).', level=messages.WARNING)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__nome']
    raw_id_fields = ['tenant']
