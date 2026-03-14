import logging

from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Unidade, Setor, Cargo
from .serializers import UnidadeSerializer, UnidadeSimpleSerializer, SetorSerializer, CargoSerializer
from apps.tenants.models import Empresa

logger = logging.getLogger(__name__)


def get_user_empresas(user):
    if user.is_staff or user.is_superuser:
        return Empresa.objects.filter(ativo=True)
    if hasattr(user, 'profile'):
        return user.profile.empresas.filter(ativo=True)
    return Empresa.objects.none()


class UnidadeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UnidadeSerializer
        return UnidadeSimpleSerializer

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        qs = Unidade.objects.filter(empresa__in=empresas).select_related('empresa')
        empresa_id = self.request.query_params.get('empresa_id')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        return qs

    def perform_create(self, serializer):
        serializer.save()


class UnidadeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UnidadeSimpleSerializer

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        return Unidade.objects.filter(empresa__in=empresas)


class SetorListCreateView(generics.ListCreateAPIView):
    serializer_class = SetorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        qs = Setor.objects.filter(unidade__empresa__in=empresas).select_related('unidade__empresa')
        unidade_id = self.request.query_params.get('unidade_id')
        empresa_id = self.request.query_params.get('empresa_id')
        if unidade_id:
            qs = qs.filter(unidade_id=unidade_id)
        if empresa_id:
            qs = qs.filter(unidade__empresa_id=empresa_id)
        return qs


class SetorDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SetorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        return Setor.objects.filter(unidade__empresa__in=empresas)


class CargoListCreateView(generics.ListCreateAPIView):
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        qs = Cargo.objects.filter(empresa__in=empresas).select_related('empresa')
        empresa_id = self.request.query_params.get('empresa_id')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        return qs


class CargoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        return Cargo.objects.filter(empresa__in=empresas)
