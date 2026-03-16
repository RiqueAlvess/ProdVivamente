import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Dimensao, Pergunta, Campaign, CategoriaFatorRisco, FatorRisco
from .serializers import (
    DimensaoSerializer, PerguntaSerializer, CampaignSerializer,
    CampaignCreateSerializer, CategoriaFatorRiscoSerializer, FatorRiscoSerializer,
)

from apps.tenants.models import Empresa
from services.audit_service import AuditService

logger = logging.getLogger(__name__)


def get_user_empresas(user):
    """Retorna as empresas que o usuário pode ver."""
    if user.is_staff or user.is_superuser:
        return Empresa.objects.filter(ativo=True)
    try:
        empresa = user.profile.empresa
        if empresa and empresa.ativo:
            return Empresa.objects.filter(pk=empresa.pk)
    except Exception:
        pass
    return Empresa.objects.none()


class DimensaoListView(generics.ListAPIView):
    """GET /api/surveys/dimensoes/ — lista dimensões HSE-IT"""
    serializer_class = DimensaoSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Dimensao.objects.all()


class PerguntaListView(generics.ListAPIView):
    """GET /api/surveys/perguntas/ — lista perguntas"""
    serializer_class = PerguntaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Pergunta.objects.select_related('dimensao').filter(ativo=True)
        dimensao_id = self.request.query_params.get('dimensao_id')
        if dimensao_id:
            qs = qs.filter(dimensao_id=dimensao_id)
        return qs


class CampaignListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CampaignCreateSerializer
        return CampaignSerializer

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        qs = Campaign.objects.filter(empresa__in=empresas).select_related('empresa')
        status_filter = self.request.query_params.get('status')
        empresa_id = self.request.query_params.get('empresa_id')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        return qs

    def perform_create(self, serializer):
        empresa_id = serializer.validated_data.get('empresa')
        if not empresa_id:
            empresa = get_user_empresas(self.request.user).first()
            campaign = serializer.save(created_by=self.request.user, empresa=empresa)
        else:
            campaign = serializer.save(created_by=self.request.user)
        AuditService.log(
            self.request.user, campaign.empresa, 'create_campaign',
            f'Campanha criada: {campaign.nome}', self.request
        )


class CampaignDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CampaignCreateSerializer
        return CampaignSerializer

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        return Campaign.objects.filter(empresa__in=empresas)


class CampaignActivateView(APIView):
    """POST /api/surveys/campaigns/{id}/activate/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        empresas = get_user_empresas(request.user)
        campaign = get_object_or_404(Campaign, pk=pk, empresa__in=empresas)

        if campaign.status != 'draft':
            return Response(
                {'error': f'Campanha está em status "{campaign.status}", não pode ser ativada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campaign.activate()
        return Response(CampaignSerializer(campaign).data)


class CampaignCloseView(APIView):
    """POST /api/surveys/campaigns/{id}/close/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        empresas = get_user_empresas(request.user)
        campaign = get_object_or_404(Campaign, pk=pk, empresa__in=empresas)

        if campaign.status != 'active':
            return Response(
                {'error': f'Campanha está em status "{campaign.status}", não pode ser encerrada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campaign.encerrar()
        return Response(CampaignSerializer(campaign).data)


class FatorRiscoListView(generics.ListAPIView):
    serializer_class = FatorRiscoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = FatorRisco.objects.select_related('categoria', 'dimensao')
        dimensao_id = self.request.query_params.get('dimensao_id')
        if dimensao_id:
            qs = qs.filter(dimensao_id=dimensao_id)
        return qs


class CategoriaFatorRiscoListView(generics.ListAPIView):
    serializer_class = CategoriaFatorRiscoSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CategoriaFatorRisco.objects.prefetch_related('fatores').all()
