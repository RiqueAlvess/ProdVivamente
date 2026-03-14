"""
Actions views - PlanoAcao, Checklist NR-1, Evidence uploads.
"""
import logging
import os

from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import PlanoAcao, ChecklistNR1Etapa, ChecklistNR1Item, EvidenciaNR1
from .serializers import (
    PlanoAcaoSerializer, PlanoAcaoCreateSerializer,
    ChecklistNR1EtapaSerializer, ChecklistNR1ItemSerializer,
    EvidenciaNR1Serializer,
)
from apps.tenants.models import Empresa
from apps.surveys.models import Campaign
from services.audit_service import AuditService
from services.storage_service import storage_service
from django.conf import settings

logger = logging.getLogger(__name__)

# NR-1 Checklist default template
NR1_CHECKLIST_TEMPLATE = [
    {
        'numero': 1,
        'nome': 'Preparação',
        'itens': [
            {'descricao': 'Selecionar instrumento de avaliação HSE-IT', 'automatico': True, 'ordem': 1},
            {'descricao': 'Definir escopo e população-alvo da avaliação', 'automatico': False, 'ordem': 2},
            {'descricao': 'Capacitar equipe responsável pela aplicação', 'automatico': False, 'ordem': 3},
            {'descricao': 'Elaborar cronograma de aplicação', 'automatico': False, 'ordem': 4},
            {'descricao': 'Comunicar funcionários sobre a pesquisa', 'automatico': False, 'ordem': 5},
        ]
    },
    {
        'numero': 2,
        'nome': 'Identificação de Perigos',
        'itens': [
            {'descricao': 'Aplicar questionário HSE-IT', 'automatico': True, 'ordem': 1},
            {'descricao': 'Realizar entrevistas complementares com lideranças', 'automatico': False, 'ordem': 2},
            {'descricao': 'Analisar registros de afastamentos e queixas', 'automatico': False, 'ordem': 3},
            {'descricao': 'Identificar fatores de risco por setor', 'automatico': False, 'ordem': 4},
        ]
    },
    {
        'numero': 3,
        'nome': 'Avaliação de Riscos',
        'itens': [
            {'descricao': 'Calcular scores por dimensão HSE-IT', 'automatico': False, 'ordem': 1},
            {'descricao': 'Aplicar matriz de risco (Probabilidade × Severidade)', 'automatico': False, 'ordem': 2},
            {'descricao': 'Priorizar setores e dimensões críticas', 'automatico': False, 'ordem': 3},
            {'descricao': 'Documentar laudo de avaliação de riscos psicossociais', 'automatico': False, 'ordem': 4},
        ]
    },
    {
        'numero': 4,
        'nome': 'Planejamento e Controle',
        'itens': [
            {'descricao': 'Elaborar planos de ação para riscos identificados', 'automatico': False, 'ordem': 1},
            {'descricao': 'Definir responsáveis e prazos para cada ação', 'automatico': False, 'ordem': 2},
            {'descricao': 'Alocar recursos necessários para as ações', 'automatico': False, 'ordem': 3},
            {'descricao': 'Implementar medidas de controle prioritárias', 'automatico': False, 'ordem': 4},
        ]
    },
    {
        'numero': 5,
        'nome': 'Monitoramento e Revisão',
        'itens': [
            {'descricao': 'Estabelecer indicadores de acompanhamento', 'automatico': False, 'ordem': 1},
            {'descricao': 'Realizar reuniões periódicas de acompanhamento', 'automatico': False, 'ordem': 2},
            {'descricao': 'Revisar eficácia das medidas implementadas', 'automatico': False, 'ordem': 3},
            {'descricao': 'Registrar e documentar resultados obtidos', 'automatico': False, 'ordem': 4},
        ]
    },
    {
        'numero': 6,
        'nome': 'Comunicação e Cultura',
        'itens': [
            {'descricao': 'Divulgar resultados agregados para os funcionários', 'automatico': False, 'ordem': 1},
            {'descricao': 'Realizar treinamentos sobre saúde mental no trabalho', 'automatico': False, 'ordem': 2},
            {'descricao': 'Desenvolver campanhas de sensibilização interna', 'automatico': False, 'ordem': 3},
            {'descricao': 'Integrar resultados ao programa de saúde e segurança', 'automatico': False, 'ordem': 4},
        ]
    },
]


def get_user_empresas(user):
    if user.is_staff or user.is_superuser:
        return Empresa.objects.filter(ativo=True)
    if hasattr(user, 'profile'):
        return user.profile.empresas.filter(ativo=True)
    return Empresa.objects.none()


class PlanoAcaoListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PlanoAcaoCreateSerializer
        return PlanoAcaoSerializer

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        qs = PlanoAcao.objects.filter(empresa__in=empresas).select_related(
            'empresa', 'campaign', 'dimensao', 'created_by'
        )
        campaign_id = self.request.query_params.get('campaign_id')
        status_filter = self.request.query_params.get('status')
        empresa_id = self.request.query_params.get('empresa_id')
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        return qs

    def perform_create(self, serializer):
        plano = serializer.save(created_by=self.request.user)
        AuditService.log(
            self.request.user, plano.empresa, 'update_action',
            f'Plano de ação criado: #{plano.id}', self.request
        )


class PlanoAcaoDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PlanoAcaoCreateSerializer
        return PlanoAcaoSerializer

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        return PlanoAcao.objects.filter(empresa__in=empresas)

    def perform_update(self, serializer):
        plano = serializer.save()
        AuditService.log(
            self.request.user, plano.empresa, 'update_action',
            f'Plano de ação atualizado: #{plano.id}', self.request
        )


class GenerateAIActionPlanView(APIView):
    """POST /api/actions/planos/generate-ai/ - Generate action plan via AI"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        campaign_id = request.data.get('campaign_id')
        dimensao_id = request.data.get('dimensao_id')

        if not campaign_id or not dimensao_id:
            return Response(
                {'error': 'campaign_id e dimensao_id são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.core.models import TaskQueue
        from apps.surveys.models import Campaign as CampaignModel
        campaign = get_object_or_404(CampaignModel, pk=campaign_id)

        task = TaskQueue.objects.create(
            task_type='generate_action_plan',
            payload={'campaign_id': campaign_id, 'dimensao_id': dimensao_id},
            user=request.user,
            empresa=campaign.empresa,
        )

        from tasks.ai_analysis_tasks import generate_action_plan
        generate_action_plan.delay(task.id)

        return Response(
            {'task_id': task.id, 'status_url': f'/api/core/tasks/{task.id}/'},
            status=status.HTTP_202_ACCEPTED,
        )


class ChecklistNR1View(APIView):
    """
    GET /api/actions/checklist/{campaign_id}/
    Auto-creates checklist if it doesn't exist.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, campaign_id):
        empresas = get_user_empresas(request.user)
        campaign = get_object_or_404(Campaign, pk=campaign_id, empresa__in=empresas)

        etapas = ChecklistNR1Etapa.objects.filter(
            campaign=campaign
        ).prefetch_related('itens__evidencias').order_by('numero_etapa')

        if not etapas.exists():
            # Auto-create checklist from template
            etapas = self._create_default_checklist(campaign)
            # Auto-mark items that are automatically done
            self._auto_mark_items(campaign, etapas)

        serializer = ChecklistNR1EtapaSerializer(etapas, many=True)

        total_items = sum(e.itens.count() for e in etapas)
        concluidos = sum(e.itens.filter(concluido=True).count() for e in etapas)
        percentual_geral = round(concluidos / total_items * 100, 1) if total_items > 0 else 0

        return Response({
            'campaign_id': campaign_id,
            'percentual_geral': percentual_geral,
            'total_items': total_items,
            'concluidos': concluidos,
            'etapas': serializer.data,
        })

    def _create_default_checklist(self, campaign):
        """Create NR-1 checklist from template."""
        created_etapas = []
        for etapa_data in NR1_CHECKLIST_TEMPLATE:
            etapa = ChecklistNR1Etapa.objects.create(
                campaign=campaign,
                empresa=campaign.empresa,
                numero_etapa=etapa_data['numero'],
                nome=etapa_data['nome'],
            )
            for item_data in etapa_data['itens']:
                ChecklistNR1Item.objects.create(
                    etapa=etapa,
                    descricao=item_data['descricao'],
                    automatico=item_data['automatico'],
                    ordem=item_data['ordem'],
                )
            created_etapas.append(etapa)
        return ChecklistNR1Etapa.objects.filter(
            campaign=campaign
        ).prefetch_related('itens').order_by('numero_etapa')

    def _auto_mark_items(self, campaign, etapas):
        """Auto-mark automatic items based on campaign state."""
        has_responses = campaign.respostas.exists()

        for etapa in etapas:
            for item in etapa.itens.filter(automatico=True):
                if 'HSE-IT' in item.descricao and 'Selecionar' in item.descricao:
                    item.marcar_concluido(responsavel='Sistema')
                elif 'Aplicar questionário' in item.descricao and has_responses:
                    item.marcar_concluido(responsavel='Sistema')


class ChecklistItemUpdateView(APIView):
    """PATCH /api/actions/checklist/items/{item_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, item_id):
        empresas = get_user_empresas(request.user)
        item = get_object_or_404(
            ChecklistNR1Item,
            pk=item_id,
            etapa__empresa__in=empresas,
        )

        serializer = ChecklistNR1ItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if request.data.get('concluido') and not item.concluido:
            item.marcar_concluido(responsavel=request.data.get('responsavel', ''))
        elif 'concluido' in request.data and not request.data['concluido']:
            item.concluido = False
            item.data_conclusao = None
            item.save(update_fields=['concluido', 'data_conclusao'])

        serializer.save()
        return Response(serializer.data)


class EvidenceUploadView(APIView):
    """POST /api/actions/checklist/items/{item_id}/evidencias/"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, item_id):
        empresas = get_user_empresas(request.user)
        item = get_object_or_404(
            ChecklistNR1Item, pk=item_id, etapa__empresa__in=empresas
        )

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'Arquivo é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        tipo = request.data.get('tipo', 'documento')
        descricao = request.data.get('descricao', '')

        # Determine storage path
        empresa = item.etapa.empresa
        campaign_id = item.etapa.campaign_id
        ext = os.path.splitext(file.name)[1].lower()
        storage_path = f'{empresa.id}/nr1/{campaign_id}/item-{item_id}/{file.name}'

        try:
            content_type = file.content_type or 'application/octet-stream'
            storage_service.upload(
                bucket=settings.SUPABASE_BUCKET_EVIDENCIAS,
                path=storage_path,
                file_content=file.read(),
                content_type=content_type,
            )
            public_url = storage_service.get_public_url(
                settings.SUPABASE_BUCKET_EVIDENCIAS, storage_path
            )
        except Exception as e:
            logger.error('Storage upload failed: %s', e)
            return Response(
                {'error': 'Erro ao enviar arquivo. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        evidencia = EvidenciaNR1.objects.create(
            checklist_item=item,
            empresa=empresa,
            nome_original=file.name,
            storage_path=storage_path,
            storage_url=public_url,
            tipo=tipo,
            tamanho_bytes=file.size,
            descricao=descricao,
            uploaded_by=request.user,
        )

        AuditService.log(
            request.user, empresa, 'upload_evidence',
            f'Evidência enviada: {file.name} para item #{item_id}', request
        )

        return Response(EvidenciaNR1Serializer(evidencia).data, status=status.HTTP_201_CREATED)


class EvidenceDeleteView(APIView):
    """DELETE /api/actions/evidencias/{evidencia_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, evidencia_id):
        empresas = get_user_empresas(request.user)
        evidencia = get_object_or_404(EvidenciaNR1, pk=evidencia_id, empresa__in=empresas)

        try:
            storage_service.delete(
                settings.SUPABASE_BUCKET_EVIDENCIAS,
                [evidencia.storage_path]
            )
        except Exception as e:
            logger.warning('Storage delete failed: %s', e)

        AuditService.log(
            request.user, evidencia.empresa, 'delete_evidence',
            f'Evidência removida: {evidencia.nome_original}', request
        )

        evidencia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
