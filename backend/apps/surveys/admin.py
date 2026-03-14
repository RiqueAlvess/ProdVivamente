from django.contrib import admin
from .models import Dimensao, Pergunta, Campaign, CategoriaFatorRisco, FatorRisco, SeveridadePorCNAE


@admin.register(Dimensao)
class DimensaoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'tipo', 'ordem']
    list_filter = ['tipo']
    search_fields = ['codigo', 'nome']
    ordering = ['ordem']


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'dimensao', 'texto_curto', 'ativo']
    list_filter = ['dimensao', 'ativo']
    search_fields = ['numero', 'texto']
    ordering = ['numero']

    def texto_curto(self, obj):
        return obj.texto[:80] + '...' if len(obj.texto) > 80 else obj.texto
    texto_curto.short_description = 'Texto'


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['nome', 'status', 'data_inicio', 'data_fim', 'taxa_adesao', 'created_at']
    list_filter = ['status']
    search_fields = ['nome']
    readonly_fields = ['created_at', 'updated_at', 'closed_at']
    date_hierarchy = 'created_at'
    actions = ['activar_campanhas', 'encerrar_campanhas']

    def activar_campanhas(self, request, queryset):
        for c in queryset.filter(status='draft'):
            c.activate()
        self.message_user(request, 'Campanhas ativadas.')
    activar_campanhas.short_description = 'Ativar campanhas selecionadas'

    def encerrar_campanhas(self, request, queryset):
        for c in queryset.filter(status='active'):
            c.encerrar()
        self.message_user(request, 'Campanhas encerradas.')
    encerrar_campanhas.short_description = 'Encerrar campanhas selecionadas'


class SeveridadePorCNAEInline(admin.TabularInline):
    model = SeveridadePorCNAE
    extra = 1


@admin.register(FatorRisco)
class FatorRiscoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'dimensao', 'probabilidade_base', 'severidade_base', 'nivel_risco_base']
    list_filter = ['categoria', 'dimensao']
    search_fields = ['nome', 'descricao']
    inlines = [SeveridadePorCNAEInline]


@admin.register(CategoriaFatorRisco)
class CategoriaFatorRiscoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'get_fator_count', 'ordem']
    search_fields = ['nome']

    def get_fator_count(self, obj):
        return obj.fatores.count()
    get_fator_count.short_description = 'Fatores'
