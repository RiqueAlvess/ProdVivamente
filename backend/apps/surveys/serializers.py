from rest_framework import serializers
from .models import Dimensao, Pergunta, Campaign, CategoriaFatorRisco, FatorRisco, SeveridadePorCNAE


class DimensaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dimensao
        fields = ['id', 'codigo', 'nome', 'tipo', 'descricao', 'ordem']


class PerguntaSerializer(serializers.ModelSerializer):
    dimensao_nome = serializers.StringRelatedField(source='dimensao')
    dimensao_codigo = serializers.CharField(source='dimensao.codigo', read_only=True)

    class Meta:
        model = Pergunta
        fields = ['id', 'numero', 'dimensao', 'dimensao_nome', 'dimensao_codigo', 'texto', 'ativo']


class CampaignSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.StringRelatedField(source='empresa')
    total_respostas = serializers.ReadOnlyField()
    taxa_adesao = serializers.ReadOnlyField()
    total_convidados = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'empresa', 'empresa_nome', 'nome', 'descricao',
            'status', 'data_inicio', 'data_fim', 'meta_adesao',
            'total_respostas', 'taxa_adesao', 'total_convidados',
            'created_at', 'updated_at', 'closed_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'closed_at']

    def get_total_convidados(self, obj):
        return obj.invitations.count()


class CampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ['id', 'empresa', 'nome', 'descricao', 'data_inicio', 'data_fim', 'meta_adesao']
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs.get('data_inicio') and attrs.get('data_fim'):
            if attrs['data_inicio'] >= attrs['data_fim']:
                raise serializers.ValidationError({'data_fim': 'Data de fim deve ser posterior à data de início.'})
        return attrs


class FatorRiscoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.StringRelatedField(source='categoria')
    nivel_risco_base = serializers.ReadOnlyField()

    class Meta:
        model = FatorRisco
        fields = [
            'id', 'categoria', 'categoria_nome', 'dimensao', 'nome', 'descricao',
            'probabilidade_base', 'severidade_base', 'nivel_risco_base', 'acoes_preventivas',
        ]


class CategoriaFatorRiscoSerializer(serializers.ModelSerializer):
    fatores = FatorRiscoSerializer(many=True, read_only=True)

    class Meta:
        model = CategoriaFatorRisco
        fields = ['id', 'nome', 'descricao', 'ordem', 'fatores']
