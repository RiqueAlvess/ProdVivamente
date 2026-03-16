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
    """
    Frontend-compatible serializer: maps Portuguese field names to English.
    Backend: nome/data_inicio/data_fim → Frontend: name/start_date/end_date
    """
    name = serializers.CharField(source='nome')
    start_date = serializers.DateField(source='data_inicio', allow_null=True)
    end_date = serializers.DateField(source='data_fim', allow_null=True)
    response_count = serializers.ReadOnlyField(source='total_respostas')
    response_rate = serializers.ReadOnlyField(source='taxa_adesao')
    invitation_count = serializers.SerializerMethodField()
    company = serializers.IntegerField(source='empresa_id', read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'company', 'name', 'start_date', 'end_date',
            'status', 'response_count', 'invitation_count', 'response_rate',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_invitation_count(self, obj):
        return obj.invitations.count()


class CampaignCreateSerializer(serializers.ModelSerializer):
    """
    Accepts both English (frontend) and Portuguese (legacy) field names.
    The 'empresa' field is optional — set from tenant context in perform_create.
    """
    name = serializers.CharField(source='nome', required=False)
    start_date = serializers.DateField(source='data_inicio', required=False, allow_null=True)
    end_date = serializers.DateField(source='data_fim', required=False, allow_null=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'empresa',
            # English aliases
            'name', 'start_date', 'end_date',
            # Portuguese originals (still accepted)
            'nome', 'descricao', 'data_inicio', 'data_fim', 'meta_adesao',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'empresa': {'required': False},
            'nome': {'required': False},
            'data_inicio': {'required': False, 'allow_null': True},
            'data_fim': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        # Require at least a name (nome or via 'name' alias)
        if not attrs.get('nome'):
            raise serializers.ValidationError({'name': 'Nome da campanha é obrigatório.'})
        start = attrs.get('data_inicio')
        end = attrs.get('data_fim')
        if start and end and start >= end:
            raise serializers.ValidationError({'end_date': 'Data de fim deve ser posterior à data de início.'})
        return attrs

    def to_representation(self, instance):
        return CampaignSerializer(instance, context=self.context).data


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
