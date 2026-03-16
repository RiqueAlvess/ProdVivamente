import secrets
import string

from django.contrib import admin, messages
from django.contrib.auth.models import User

from .models import Empresa


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + '!@#$'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _provision_admin_user(empresa, email, password=None):
    """
    Cria (ou redefine senha de) um usuário admin RH para a empresa.
    Retorna (user, created, password).
    """
    from apps.accounts.models import UserProfile

    if password is None:
        password = _generate_password()

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

    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'rh', 'empresa': empresa})
    if not profile.empresa:
        profile.empresa = empresa
        profile.save(update_fields=['empresa'])

    return user, created, password


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'admin_email', 'ativo', 'total_funcionarios', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'cnpj', 'admin_email']
    prepopulated_fields = {'slug': ('nome',)}
    readonly_fields = ['slug', 'created_at', 'updated_at']
    actions = ['provisionar_admin', 'ativar_empresas', 'desativar_empresas']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'cnpj', 'total_funcionarios', 'cnae', 'cnae_descricao', 'ativo'),
        }),
        ('Administrador RH', {
            'fields': ('admin_email',),
            'description': (
                'E-mail do usuário RH que gerenciará esta empresa. '
                'Ao salvar uma nova empresa, o usuário admin será provisionado automaticamente.'
            ),
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

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
                        f'✓ Empresa "{obj.nome}" criada. '
                        f'Usuário admin {action}: {obj.admin_email} | Senha: {password} '
                        f'— Anote agora, não será exibida novamente.'
                    ),
                    level=messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Empresa criada, mas falha ao provisionar admin: {e}',
                    level=messages.WARNING,
                )

    @admin.action(description='Provisionar / Resetar senha do Admin RH')
    def provisionar_admin(self, request, queryset):
        for empresa in queryset:
            if not empresa.admin_email:
                self.message_user(
                    request,
                    f'{empresa.nome}: sem admin_email configurado.',
                    level=messages.WARNING,
                )
                continue
            try:
                user, created, password = _provision_admin_user(empresa, empresa.admin_email)
                action = 'criado' if created else 'senha resetada'
                self.message_user(
                    request,
                    f'[{empresa.nome}] Admin {action}: {empresa.admin_email} | Senha: {password}',
                    level=messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(request, f'{empresa.nome}: {e}', level=messages.ERROR)

    @admin.action(description='Ativar empresas selecionadas')
    def ativar_empresas(self, request, queryset):
        updated = queryset.update(ativo=True)
        self.message_user(request, f'{updated} empresa(s) ativada(s).', level=messages.SUCCESS)

    @admin.action(description='Desativar empresas selecionadas')
    def desativar_empresas(self, request, queryset):
        updated = queryset.update(ativo=False)
        self.message_user(request, f'{updated} empresa(s) desativada(s).', level=messages.WARNING)
