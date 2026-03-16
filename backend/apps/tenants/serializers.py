from rest_framework import serializers
from .models import Empresa


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            'id', 'nome', 'cnpj', 'slug',
            'total_funcionarios', 'cnae', 'cnae_descricao',
            'admin_email', 'ativo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def validate_cnpj(self, value):
        qs = Empresa.objects.filter(cnpj=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('CNPJ já cadastrado.')
        return value


class EmpresaCreateSerializer(serializers.Serializer):
    """Cria empresa e provisiona o usuário admin RH inicial."""
    nome = serializers.CharField(max_length=255)
    cnpj = serializers.CharField(max_length=18)
    total_funcionarios = serializers.IntegerField(default=0, required=False)
    cnae = serializers.CharField(max_length=10, default='', required=False)
    cnae_descricao = serializers.CharField(max_length=255, default='', required=False)

    admin_email = serializers.EmailField()
    admin_first_name = serializers.CharField(max_length=150, default='Admin', required=False)
    admin_last_name = serializers.CharField(max_length=150, default='', required=False)
    admin_password = serializers.CharField(
        min_length=8,
        required=False,
        write_only=True,
        help_text='Deixe em branco para gerar automaticamente.',
    )

    def validate_cnpj(self, value):
        if Empresa.objects.filter(cnpj=value).exists():
            raise serializers.ValidationError('CNPJ já cadastrado.')
        return value
