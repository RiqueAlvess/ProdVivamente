from rest_framework import serializers
from .models import (
    DimEstrutura, FactScoreDimensao, FactIndicadorCampanha,
    FactRespostaPergunta, SectorAnalysis,
)


class SectorAnalysisSerializer(serializers.ModelSerializer):
    setor_nome = serializers.StringRelatedField(source='setor')
    campaign_nome = serializers.StringRelatedField(source='campaign')

    class Meta:
        model = SectorAnalysis
        fields = [
            'id', 'campaign', 'campaign_nome', 'setor', 'setor_nome',
            'status', 'pontos_criticos', 'recomendacoes', 'analise_completa',
            'modelo_ia', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class FactScoreDimensaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactScoreDimensao
        fields = [
            'id', 'campaign', 'dim_estrutura', 'dim_dimensao',
            'score_medio', 'nivel_risco', 'total_respostas', 'updated_at',
        ]


class FactIndicadorCampanhaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactIndicadorCampanha
        fields = [
            'campaign', 'total_convidados', 'total_respondidos',
            'taxa_adesao', 'igrp', 'score_geral', 'nivel_risco_geral', 'updated_at',
        ]
