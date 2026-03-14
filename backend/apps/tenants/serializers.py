from rest_framework import serializers
from .models import Empresa, Domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'domain', 'tenant', 'is_primary']
        read_only_fields = ['id']


class EmpresaSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)

    class Meta:
        model = Empresa
        fields = [
            'id', 'schema_name', 'nome', 'cnpj', 'slug',
            'total_funcionarios', 'cnae', 'cnae_descricao',
            'logo_url', 'favicon_url', 'cor_primaria', 'cor_secundaria',
            'cor_fonte', 'nome_app', 'ativo', 'created_at', 'updated_at',
            'domains',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'domains']


class EmpresaPublicSerializer(serializers.ModelSerializer):
    """Minimal public info for branding/tenant detection."""
    class Meta:
        model = Empresa
        fields = [
            'id', 'nome', 'slug', 'logo_url', 'favicon_url',
            'cor_primaria', 'cor_secundaria', 'cor_fonte', 'nome_app',
        ]


class CurrentTenantSerializer(serializers.ModelSerializer):
    """Serializer for the current tenant context (from connection.tenant)."""
    class Meta:
        model = Empresa
        fields = [
            'id', 'schema_name', 'nome', 'cnpj', 'slug',
            'total_funcionarios', 'cnae', 'cnae_descricao',
            'logo_url', 'favicon_url', 'cor_primaria', 'cor_secundaria',
            'cor_fonte', 'nome_app', 'ativo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'schema_name', 'slug', 'created_at', 'updated_at']
