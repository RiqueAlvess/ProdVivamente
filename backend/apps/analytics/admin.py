from django.contrib import admin
from .models import (
    DimTempo, DimEstrutura, DimDemografia, DimDimensaoHSE,
    FactScoreDimensao, FactIndicadorCampanha, FactRespostaPergunta,
    SectorAnalysis,
)


@admin.register(DimEstrutura)
class DimEstruturaAdmin(admin.ModelAdmin):
    list_display = ['unidade_nome', 'setor_nome']
    list_filter = ['unidade']
    search_fields = ['unidade_nome', 'setor_nome']


@admin.register(FactScoreDimensao)
class FactScoreDimensaoAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'dim_dimensao', 'dim_estrutura', 'score_medio', 'nivel_risco', 'total_respostas']
    list_filter = ['campaign', 'nivel_risco', 'dim_dimensao']


@admin.register(FactIndicadorCampanha)
class FactIndicadorCampanhaAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'total_convidados', 'total_respondidos', 'taxa_adesao', 'igrp', 'nivel_risco_geral']
    list_filter = ['nivel_risco_geral']


@admin.register(SectorAnalysis)
class SectorAnalysisAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'setor', 'status', 'modelo_ia', 'created_at']
    list_filter = ['status', 'campaign']
    readonly_fields = ['pontos_criticos', 'recomendacoes', 'analise_completa', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
