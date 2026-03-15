import secrets
import string

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
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
    list_display = ['nome', 'schema_name', 'cnpj', 'admin_email', 'ativo', 'status_admin', 'acoes_tenant', 'created_at']
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

    # ------------------------------------------------------------------
    # List display helpers
    # ------------------------------------------------------------------

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

    @admin.display(description='Usuários')
    def acoes_tenant(self, obj):
        url = reverse('admin:tenants_empresa_usuarios', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="white-space:nowrap">👥 Gerenciar Usuários</a>',
            url,
        )

    # ------------------------------------------------------------------
    # save_model: auto-provision admin on create
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

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
                    f'[{empresa.nome}] Admin {action}: {empresa.admin_email} | Senha: {password}',
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

    # ------------------------------------------------------------------
    # Custom URLs for tenant user management
    # ------------------------------------------------------------------

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                '<int:pk>/usuarios/',
                self.admin_site.admin_view(self.usuarios_view),
                name='tenants_empresa_usuarios',
            ),
            path(
                '<int:pk>/usuarios/novo/',
                self.admin_site.admin_view(self.novo_usuario_view),
                name='tenants_empresa_usuario_novo',
            ),
            path(
                '<int:pk>/usuarios/<int:user_id>/senha/',
                self.admin_site.admin_view(self.resetar_senha_view),
                name='tenants_empresa_usuario_senha',
            ),
            path(
                '<int:pk>/usuarios/<int:user_id>/toggle/',
                self.admin_site.admin_view(self.toggle_ativo_view),
                name='tenants_empresa_usuario_toggle',
            ),
            path(
                '<int:pk>/usuarios/<int:user_id>/excluir/',
                self.admin_site.admin_view(self.excluir_usuario_view),
                name='tenants_empresa_usuario_excluir',
            ),
        ]
        return extra + urls

    # ------------------------------------------------------------------
    # Custom views
    # ------------------------------------------------------------------

    def usuarios_view(self, request, pk):
        empresa = get_object_or_404(Empresa, pk=pk)

        from django.db import ProgrammingError

        users = []
        with tenant_context(empresa):
            from apps.accounts.models import UserProfile

            # Fetch users and profiles in separate queries to avoid a
            # cross-schema LEFT OUTER JOIN that fails on public schema context.
            raw_users = list(
                User.objects.filter(is_superuser=False).order_by('email')
            )
            try:
                profiles = {
                    p.user_id: p
                    for p in UserProfile.objects.filter(
                        user_id__in=[u.id for u in raw_users]
                    )
                }
            except ProgrammingError:
                profiles = {}

            for user in raw_users:
                user._profile_obj = profiles.get(user.id)
            users = raw_users

        context = {
            **self.admin_site.each_context(request),
            'empresa': empresa,
            'users': users,
            'title': f'Usuários — {empresa.nome}',
            'novo_url': reverse('admin:tenants_empresa_usuario_novo', args=[pk]),
            'voltar_url': reverse('admin:tenants_empresa_changelist'),
            'opts': self.model._meta,
        }
        return render(request, 'admin/tenants/usuarios.html', context)

    def novo_usuario_view(self, request, pk):
        empresa = get_object_or_404(Empresa, pk=pk)
        lista_url = reverse('admin:tenants_empresa_usuarios', args=[pk])

        if request.method == 'POST':
            email = request.POST.get('email', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            role = request.POST.get('role', 'rh')
            password = request.POST.get('password', '').strip() or _generate_password()
            is_staff = request.POST.get('is_staff') == 'on'

            if not email:
                messages.error(request, 'E-mail é obrigatório.')
            else:
                try:
                    with tenant_context(empresa):
                        from apps.accounts.models import UserProfile

                        if User.objects.filter(email=email).exists():
                            messages.error(request, f'Já existe um usuário com o e-mail {email}.')
                        else:
                            base_username = email.split('@')[0]
                            username = base_username
                            n = 1
                            while User.objects.filter(username=username).exists():
                                username = f'{base_username}{n}'
                                n += 1

                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                password=password,
                                first_name=first_name,
                                last_name=last_name,
                                is_staff=is_staff,
                                is_active=True,
                            )
                            UserProfile.objects.create(user=user, role=role)

                            messages.success(
                                request,
                                f'✓ Usuário {email} criado! Senha: {password} — Anote agora, não será exibida novamente.',
                            )
                            return redirect(lista_url)
                except Exception as e:
                    messages.error(request, f'Erro ao criar usuário: {e}')

        context = {
            **self.admin_site.each_context(request),
            'empresa': empresa,
            'title': f'Novo Usuário — {empresa.nome}',
            'voltar_url': lista_url,
            'opts': self.model._meta,
        }
        return render(request, 'admin/tenants/novo_usuario.html', context)

    def resetar_senha_view(self, request, pk, user_id):
        empresa = get_object_or_404(Empresa, pk=pk)

        if request.method == 'POST':
            nova_senha = _generate_password()
            with tenant_context(empresa):
                try:
                    user = User.objects.get(pk=user_id)
                    user.set_password(nova_senha)
                    user.save()
                    messages.success(
                        request,
                        f'Nova senha de {user.email}: {nova_senha} — Anote agora, não será exibida novamente.',
                    )
                except User.DoesNotExist:
                    messages.error(request, 'Usuário não encontrado.')

        return redirect(reverse('admin:tenants_empresa_usuarios', args=[pk]))

    def toggle_ativo_view(self, request, pk, user_id):
        empresa = get_object_or_404(Empresa, pk=pk)

        if request.method == 'POST':
            with tenant_context(empresa):
                try:
                    user = User.objects.get(pk=user_id)
                    user.is_active = not user.is_active
                    user.save()
                    estado = 'ativado' if user.is_active else 'desativado'
                    messages.success(request, f'Usuário {user.email} {estado}.')
                except User.DoesNotExist:
                    messages.error(request, 'Usuário não encontrado.')

        return redirect(reverse('admin:tenants_empresa_usuarios', args=[pk]))

    def excluir_usuario_view(self, request, pk, user_id):
        empresa = get_object_or_404(Empresa, pk=pk)

        if request.method == 'POST':
            with tenant_context(empresa):
                try:
                    user = User.objects.get(pk=user_id)
                    email = user.email
                    user.delete()
                    messages.success(request, f'Usuário {email} removido.')
                except User.DoesNotExist:
                    messages.error(request, 'Usuário não encontrado.')

        return redirect(reverse('admin:tenants_empresa_usuarios', args=[pk]))


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__nome']
    raw_id_fields = ['tenant']
