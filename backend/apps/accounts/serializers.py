"""
Accounts serializers - JWT auth, user profile.
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserProfile, AuditLog


def _get_profile_safe(user):
    """Retorna o UserProfile do usuário, ou None se não existir."""
    try:
        return user.profile
    except (UserProfile.DoesNotExist, Exception):
        return None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer JWT customizado que aceita login por e-mail."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields[self.username_field]
        self.fields['email'] = serializers.EmailField()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        profile = _get_profile_safe(user)
        if profile:
            token['role'] = profile.role
            if profile.empresa_id:
                token['empresa_id'] = profile.empresa_id
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
        profile = _get_profile_safe(user)

        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
        }

        if profile:
            data['user']['role'] = profile.role
            if profile.empresa:
                data['user']['empresa_id'] = profile.empresa_id
                data['user']['empresa_nome'] = profile.empresa.nome

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'empresa', 'empresa_nome', 'telefone', 'created_at']
        read_only_fields = ['id', 'created_at', 'empresa_nome']


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
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

    def get_profile(self, obj):
        profile = _get_profile_safe(obj)
        if profile is None:
            return None
        return UserProfileSerializer(profile).data


class AuditLogSerializer(serializers.ModelSerializer):
    user_display = serializers.StringRelatedField(source='user')

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_display',
            'acao', 'descricao', 'ip', 'created_at',
        ]
        read_only_fields = fields


class CreateUserSerializer(serializers.Serializer):
    """Usado por admins RH para criar usuários na empresa."""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, default='', required=False)
    password = serializers.CharField(min_length=8, write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLES, default='rh')
    telefone = serializers.CharField(max_length=20, default='', required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Já existe um usuário com este e-mail.')
        return value

    def create(self, validated_data):
        role = validated_data.pop('role', 'rh')
        telefone = validated_data.pop('telefone', '')
        password = validated_data.pop('password')
        empresa = self.context.get('empresa')
        email = validated_data['email']

        base_username = email.split('@')[0]
        username = base_username
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{n}'
            n += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=False,
            is_active=True,
        )
        UserProfile.objects.create(user=user, role=role, telefone=telefone, empresa=empresa)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'As senhas não coincidem.'})
        return attrs
