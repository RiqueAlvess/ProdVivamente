from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Domain, Empresa


@admin.register(Empresa)
class EmpresaAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['nome', 'schema_name', 'cnpj', 'cnae', 'total_funcionarios', 'ativo', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'cnpj', 'cnae', 'schema_name']
    prepopulated_fields = {'slug': ('nome',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Tenant', {
            'fields': ('schema_name', 'slug', 'ativo'),
        }),
        ('Informações Básicas', {
            'fields': ('nome', 'cnpj', 'total_funcionarios', 'cnae', 'cnae_descricao'),
        }),
        ('Personalização', {
            'fields': ('logo_url', 'favicon_url', 'cor_primaria', 'cor_secundaria', 'cor_fonte', 'nome_app'),
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__nome']
    raw_id_fields = ['tenant']
