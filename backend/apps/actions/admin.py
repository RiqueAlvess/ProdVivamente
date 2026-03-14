from django.contrib import admin
from .models import PlanoAcao, ChecklistNR1Etapa, ChecklistNR1Item, EvidenciaNR1


@admin.register(PlanoAcao)
class PlanoAcaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'empresa', 'campaign', 'dimensao', 'nivel_risco', 'status', 'responsavel', 'prazo']
    list_filter = ['status', 'empresa', 'dimensao', 'nivel_risco']
    search_fields = ['acao_proposta', 'responsavel', 'descricao_risco']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    date_hierarchy = 'created_at'


class ChecklistNR1ItemInline(admin.TabularInline):
    model = ChecklistNR1Item
    extra = 0
    readonly_fields = ['automatico', 'data_conclusao']


@admin.register(ChecklistNR1Etapa)
class ChecklistNR1EtapaAdmin(admin.ModelAdmin):
    list_display = ['numero_etapa', 'nome', 'campaign', 'empresa', 'percentual_conclusao']
    list_filter = ['empresa', 'campaign']
    inlines = [ChecklistNR1ItemInline]


@admin.register(ChecklistNR1Item)
class ChecklistNR1ItemAdmin(admin.ModelAdmin):
    list_display = ['descricao_curta', 'etapa', 'automatico', 'concluido', 'responsavel', 'prazo']
    list_filter = ['concluido', 'automatico', 'etapa__empresa']

    def descricao_curta(self, obj):
        return obj.descricao[:60]
    descricao_curta.short_description = 'Descrição'


@admin.register(EvidenciaNR1)
class EvidenciaNR1Admin(admin.ModelAdmin):
    list_display = ['nome_original', 'empresa', 'tipo', 'tamanho_bytes', 'uploaded_by', 'created_at']
    list_filter = ['tipo', 'empresa']
    search_fields = ['nome_original', 'descricao']
    readonly_fields = ['storage_path', 'storage_url', 'created_at']
