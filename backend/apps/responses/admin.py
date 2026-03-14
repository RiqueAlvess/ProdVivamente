from django.contrib import admin
from .models import SurveyResponse


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'campaign', 'unidade', 'setor', 'faixa_etaria', 'genero', 'created_at']
    list_filter = ['campaign', 'unidade', 'setor', 'faixa_etaria', 'genero']
    readonly_fields = [
        'campaign', 'unidade', 'setor', 'faixa_etaria', 'tempo_empresa', 'genero',
        'respostas', 'comentario_livre', 'sentimento_score', 'sentimento_categorias',
        'lgpd_aceito', 'lgpd_aceito_em', 'created_at',
    ]
    date_hierarchy = 'created_at'
    search_fields = []  # No PII searchable

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
