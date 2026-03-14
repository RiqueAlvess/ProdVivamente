from rest_framework import serializers
from .models import SurveyResponse


FAIXA_ETARIA_CHOICES = [
    'Menos de 25 anos', '25 a 34 anos', '35 a 44 anos',
    '45 a 54 anos', '55 anos ou mais',
]

TEMPO_EMPRESA_CHOICES = [
    'Menos de 1 ano', '1 a 3 anos', '3 a 5 anos',
    '5 a 10 anos', 'Mais de 10 anos',
]

GENERO_CHOICES = [
    'Masculino', 'Feminino', 'Não-binário', 'Prefiro não informar',
]


class LGPDSerializer(serializers.Serializer):
    """Step 1: LGPD consent."""
    lgpd_aceito = serializers.BooleanField()

    def validate_lgpd_aceito(self, value):
        if not value:
            raise serializers.ValidationError('É necessário aceitar os termos LGPD para participar.')
        return value


class DemographicsSerializer(serializers.Serializer):
    """Step 2: Demographics (all optional)."""
    faixa_etaria = serializers.ChoiceField(choices=FAIXA_ETARIA_CHOICES, required=False, allow_blank=True)
    tempo_empresa = serializers.ChoiceField(choices=TEMPO_EMPRESA_CHOICES, required=False, allow_blank=True)
    genero = serializers.ChoiceField(choices=GENERO_CHOICES, required=False, allow_blank=True)


class AnswerSerializer(serializers.Serializer):
    """Step 3: Answer a single question."""
    step = serializers.IntegerField(min_value=1, max_value=35)
    value = serializers.IntegerField(min_value=0, max_value=4)


class SubmitSerializer(serializers.Serializer):
    """Final step: Submit with optional comment."""
    comentario_livre = serializers.CharField(required=False, allow_blank=True, max_length=3000)


class SurveyResponseSerializer(serializers.ModelSerializer):
    """Full response serializer for admin/analytics."""
    campaign_nome = serializers.StringRelatedField(source='campaign')
    unidade_nome = serializers.StringRelatedField(source='unidade')
    setor_nome = serializers.StringRelatedField(source='setor')

    class Meta:
        model = SurveyResponse
        fields = [
            'id', 'campaign', 'campaign_nome', 'unidade', 'unidade_nome',
            'setor', 'setor_nome', 'faixa_etaria', 'tempo_empresa', 'genero',
            'respostas', 'comentario_livre', 'sentimento_score', 'sentimento_categorias',
            'lgpd_aceito', 'lgpd_aceito_em', 'created_at',
        ]
        read_only_fields = fields
