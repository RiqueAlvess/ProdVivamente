from rest_framework import serializers
from .models import PlanoAcao, ChecklistNR1Etapa, ChecklistNR1Item, EvidenciaNR1


class EvidenciaNR1Serializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.StringRelatedField(source='uploaded_by')

    class Meta:
        model = EvidenciaNR1
        fields = [
            'id', 'checklist_item', 'empresa', 'nome_original', 'storage_path',
            'storage_url', 'tipo', 'tamanho_bytes', 'descricao',
            'uploaded_by', 'uploaded_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'storage_path', 'storage_url', 'created_at']


class ChecklistNR1ItemSerializer(serializers.ModelSerializer):
    evidencias = EvidenciaNR1Serializer(many=True, read_only=True)
    percentual_conclusao = serializers.SerializerMethodField()

    class Meta:
        model = ChecklistNR1Item
        fields = [
            'id', 'etapa', 'descricao', 'automatico', 'concluido',
            'data_conclusao', 'responsavel', 'prazo', 'observacoes', 'ordem',
            'evidencias', 'percentual_conclusao',
        ]
        read_only_fields = ['id', 'automatico']

    def get_percentual_conclusao(self, obj):
        return 100 if obj.concluido else 0


class ChecklistNR1EtapaSerializer(serializers.ModelSerializer):
    itens = ChecklistNR1ItemSerializer(many=True, read_only=True)
    percentual_conclusao = serializers.ReadOnlyField()

    class Meta:
        model = ChecklistNR1Etapa
        fields = ['id', 'campaign', 'empresa', 'numero_etapa', 'nome', 'percentual_conclusao', 'itens', 'created_at']
        read_only_fields = ['id', 'created_at']


class PlanoAcaoSerializer(serializers.ModelSerializer):
    created_by_name = serializers.StringRelatedField(source='created_by')
    dimensao_nome = serializers.StringRelatedField(source='dimensao')
    empresa_nome = serializers.StringRelatedField(source='empresa')
    campaign_nome = serializers.StringRelatedField(source='campaign')

    class Meta:
        model = PlanoAcao
        fields = [
            'id', 'empresa', 'empresa_nome', 'campaign', 'campaign_nome',
            'dimensao', 'dimensao_nome', 'nivel_risco', 'descricao_risco',
            'acao_proposta', 'responsavel', 'prazo', 'recursos_necessarios',
            'indicadores', 'status', 'conteudo_estruturado', 'conteudo_html',
            'gerado_por_ia', 'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'gerado_por_ia']


class PlanoAcaoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanoAcao
        fields = [
            'empresa', 'campaign', 'dimensao', 'nivel_risco', 'descricao_risco',
            'acao_proposta', 'responsavel', 'prazo', 'recursos_necessarios',
            'indicadores', 'status', 'conteudo_estruturado', 'conteudo_html',
        ]
