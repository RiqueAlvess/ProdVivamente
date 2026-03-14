from rest_framework import serializers
from .models import SurveyInvitation


class SurveyInvitationSerializer(serializers.ModelSerializer):
    """Serializer that decrypts PII fields for internal use."""
    email = serializers.SerializerMethodField()
    nome = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    survey_url = serializers.ReadOnlyField()

    class Meta:
        model = SurveyInvitation
        fields = [
            'id', 'hash_token', 'email', 'nome',
            'empresa', 'campaign', 'unidade', 'setor', 'cargo',
            'status', 'expires_at', 'sent_at', 'used_at', 'is_valid', 'survey_url',
            'created_at',
        ]
        read_only_fields = ['id', 'hash_token', 'created_at']

    def get_email(self, obj):
        try:
            from services.crypto_service import crypto_service
            return crypto_service.decrypt(obj.email_encrypted)
        except Exception:
            return '***'

    def get_nome(self, obj):
        try:
            from services.crypto_service import crypto_service
            return crypto_service.decrypt(obj.nome_encrypted)
        except Exception:
            return '***'


class SurveyInvitationAnonymousSerializer(serializers.ModelSerializer):
    """Minimal serializer without PII for token validation."""
    class Meta:
        model = SurveyInvitation
        fields = ['hash_token', 'status', 'expires_at', 'campaign']


class ImportCSVRowSerializer(serializers.Serializer):
    """Validates a single CSV row for invitation import."""
    nome = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    unidade = serializers.CharField(max_length=255)
    setor = serializers.CharField(max_length=255)
    cargo = serializers.CharField(max_length=255, required=False, allow_blank=True)
