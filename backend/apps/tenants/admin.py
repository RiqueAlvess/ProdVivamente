from django.contrib import admin
from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'cnae', 'total_funcionarios', 'ativo', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'cnpj', 'cnae']
    prepopulated_fields = {'slug': ('nome',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'cnpj', 'slug', 'total_funcionarios', 'cnae', 'cnae_descricao', 'ativo')
        }),
        ('Personalização', {
            'fields': ('logo_url', 'favicon_url', 'cor_primaria', 'cor_secundaria', 'cor_fonte', 'nome_app')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
