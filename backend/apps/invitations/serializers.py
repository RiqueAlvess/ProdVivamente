from rest_framework import serializers
from .models import SurveyInvitation


class SurveyInvitationSerializer(serializers.ModelSerializer):
    """
    LGPD-compliant serializer: exposes email_hash instead of actual email.
    The actual email is NEVER sent to the frontend.
    """
    email_display = serializers.SerializerMethodField()
    unidade_nome = serializers.CharField(source='unidade.nome', read_only=True)
    setor_nome = serializers.CharField(source='setor.nome', read_only=True)
    cargo_nome = serializers.CharField(source='cargo.nome', read_only=True, default=None)
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = SurveyInvitation
        fields = [
            'id', 'hash_token', 'email_hash', 'email_display',
            'empresa', 'campaign', 'unidade', 'unidade_nome', 'setor', 'setor_nome',
            'cargo', 'cargo_nome',
            'status', 'expires_at', 'sent_at', 'used_at', 'is_valid',
            'created_at',
        ]
        read_only_fields = ['id', 'hash_token', 'email_hash', 'created_at']

    def get_email_display(self, obj):
        """Return anonymized display: first 16 chars of HMAC-SHA256 hash."""
        if obj.email_hash:
            return obj.email_hash
        # Fallback: compute from hash_token prefix for existing records without hash
        return str(obj.hash_token)[:16]


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
