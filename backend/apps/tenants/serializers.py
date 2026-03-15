from rest_framework import serializers
from .models import Empresa, Domain


class TenantSetupSerializer(serializers.Serializer):
    """
    All-in-one serializer for creating a tenant with its primary domain
    and the initial RH admin user in a single API call.
    """
    # Empresa fields
    nome = serializers.CharField(max_length=255)
    cnpj = serializers.CharField(max_length=18)
    schema_name = serializers.SlugField(max_length=63)
    total_funcionarios = serializers.IntegerField(default=0, required=False)
    cnae = serializers.CharField(max_length=10, default='', required=False)
    cnae_descricao = serializers.CharField(max_length=255, default='', required=False)

    # Domain
    domain = serializers.CharField(
        max_length=253,
        help_text='Ex: empresa1.vivamente.com.br ou empresa1.localhost',
    )

    # Initial admin user
    admin_email = serializers.EmailField()
    admin_first_name = serializers.CharField(max_length=150, default='Admin', required=False)
    admin_last_name = serializers.CharField(max_length=150, default='', required=False)
    admin_password = serializers.CharField(
        min_length=8,
        required=False,
        write_only=True,
        help_text='Deixe em branco para gerar automaticamente.',
    )

    def validate_schema_name(self, value):
        if Empresa.objects.filter(schema_name=value).exists():
            raise serializers.ValidationError('schema_name já utilizado.')
        return value

    def validate_cnpj(self, value):
        if Empresa.objects.filter(cnpj=value).exists():
            raise serializers.ValidationError('CNPJ já cadastrado.')
        return value

    def validate_domain(self, value):
        from .models import Domain
        if Domain.objects.filter(domain=value).exists():
            raise serializers.ValidationError('Domínio já cadastrado.')
        return value


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
