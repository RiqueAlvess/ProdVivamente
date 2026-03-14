from rest_framework import serializers
from .models import Unidade, Setor, Cargo


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'empresa', 'nome', 'created_at']
        read_only_fields = ['id', 'created_at']


class SetorSerializer(serializers.ModelSerializer):
    unidade_nome = serializers.StringRelatedField(source='unidade')

    class Meta:
        model = Setor
        fields = ['id', 'unidade', 'unidade_nome', 'nome', 'created_at']
        read_only_fields = ['id', 'created_at']


class UnidadeSerializer(serializers.ModelSerializer):
    setores = SetorSerializer(many=True, read_only=True)

    class Meta:
        model = Unidade
        fields = ['id', 'empresa', 'nome', 'setores', 'created_at']
        read_only_fields = ['id', 'created_at']


class UnidadeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = ['id', 'empresa', 'nome', 'created_at']
        read_only_fields = ['id', 'created_at']
