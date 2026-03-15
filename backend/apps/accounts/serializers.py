"""
Accounts serializers - JWT auth, user profile.
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserProfile, AuditLog
from apps.tenants.serializers import EmpresaPublicSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that accepts email login and adds user info to token response."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace the default username field with email
        del self.fields[self.username_field]
        self.fields['email'] = serializers.EmailField()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        if hasattr(user, 'profile'):
            token['role'] = user.profile.role
        return token

    def validate(self, attrs):
        email = attrs.pop('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'email': 'Nenhuma conta encontrada com este e-mail.'}
            )
        attrs[self.username_field] = user.username

        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
        }
        if hasattr(user, 'profile'):
            data['user']['role'] = user.profile.role
            data['user']['empresas'] = list(
                user.profile.empresas.values_list('id', flat=True)
            )
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    empresas = EmpresaPublicSerializer(many=True, read_only=True)
    empresas_ids = serializers.PrimaryKeyRelatedField(
        source='empresas',
        many=True,
        read_only=True,
    )

    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'empresas', 'empresas_ids', 'telefone', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_staff', 'is_active', 'profile',
        ]
        read_only_fields = ['id', 'is_staff', 'is_active']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class AuditLogSerializer(serializers.ModelSerializer):
    user_display = serializers.StringRelatedField(source='user')
    empresa_display = serializers.StringRelatedField(source='empresa')

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_display', 'empresa', 'empresa_display',
            'acao', 'descricao', 'ip', 'created_at',
        ]
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'As senhas não coincidem.'})
        return attrs
