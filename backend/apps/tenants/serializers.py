from rest_framework import serializers
from .models import Empresa


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            'id', 'nome', 'cnpj', 'slug', 'total_funcionarios',
            'cnae', 'cnae_descricao', 'logo_url', 'favicon_url',
            'cor_primaria', 'cor_secundaria', 'cor_fonte', 'nome_app',
            'ativo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class EmpresaPublicSerializer(serializers.ModelSerializer):
    """Minimal public info for branding/tenant detection."""
    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'slug', 'logo_url', 'favicon_url',
                  'cor_primaria', 'cor_secundaria', 'cor_fonte', 'nome_app']
