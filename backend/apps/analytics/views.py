"""
Analytics views - Dashboard, Sector Analysis, Campaign Comparison, Risk Matrix.
"""
import logging
from datetime import timedelta

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import SectorAnalysis, FactIndicadorCampanha
from .serializers import SectorAnalysisSerializer
from apps.surveys.models import Campaign
from apps.surveys.serializers import CampaignSerializer
from apps.structure.serializers import SetorSerializer
from django.db import connection

from apps.tenants.models import Empresa
from apps.core.models import TaskQueue
from services.audit_service import AuditService

logger = logging.getLogger(__name__)


def get_user_empresas(user):
    if user.is_staff or user.is_superuser:
        return Empresa.objects.filter(ativo=True)
    return Empresa.objects.filter(pk=connection.tenant.pk, ativo=True)


def get_campaign_for_user(user, campaign_id):
    """Get campaign if user has access."""
    empresas = get_user_empresas(user)
    return get_object_or_404(Campaign, pk=campaign_id, empresa__in=empresas)


class DashboardView(APIView):
    """
    GET /api/analytics/dashboard/?campaign=<id>&unidade_id=<id>&setor_id=<id>
    Main dashboard with all KPIs.
    Leadership role restricts to allowed sectors only.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from db_selectors.dashboard_selectors import DashboardSelectors
        from services.risk_service import RiskService
        from services.anonymity_service import AnonymityService

        campaign_id = request.query_params.get('campaign')
        if not campaign_id:
            return Response({'error': 'campaign é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        campaign = get_campaign_for_user(request.user, campaign_id)
        empresa = campaign.empresa

        user = request.user
        role = getattr(getattr(user, 'profile', None), 'role', 'rh')

        # Leadership restrictions
        if role == 'lideranca':
            setor_id = request.query_params.get('setor_id')
            if not setor_id:
                setores_permitidos = user.profile.setores_permitidos.all()
                if not setores_permitidos.exists():
                    return Response({'error': 'Nenhum setor permitido configurado.'}, status=403)
                return Response({
                    'requires_sector_selection': True,
                    'setores': SetorSerializer(setores_permitidos, many=True).data,
                })

            allowed_ids = list(user.profile.setores_permitidos.values_list('id', flat=True))
            if int(setor_id) not in allowed_ids:
                return Response({'error': 'Acesso negado a este setor.'}, status=status.HTTP_403_FORBIDDEN)

        filters = {
            'unidade_id': request.query_params.get('unidade_id') or None,
            'setor_id': request.query_params.get('setor_id') or None,
        }
        # Clean None values
        filters = {k: v for k, v in filters.items() if v}

        risk_svc = RiskService()

        metrics = DashboardSelectors.get_metrics(campaign, filters)
        dimensoes_scores = DashboardSelectors.get_dimensoes_scores(campaign, filters)
        distribuicao = risk_svc.get_distribuicao_riscos(campaign, filters)
        igrp = risk_svc.calcular_igrp(campaign, filters)
        top5_setores = DashboardSelectors.get_scores_por_setor(campaign, filters)
        heatmap = DashboardSelectors.get_heatmap(campaign, filters)
        demographic_scores = DashboardSelectors.get_demographic_scores(campaign, filters)

        AuditService.log(
            user, empresa, 'view_dashboard',
            f'Dashboard visualizado - campanha {campaign.id}', request
        )

        return Response({
            'campaign': CampaignSerializer(campaign).data,
            'data_released': AnonymityService.is_data_released(campaign),
            'metrics': metrics,
            'dimensoes_scores': dimensoes_scores,
            'distribuicao_riscos': distribuicao,
            'igrp': igrp,
            'top5_setores_criticos': top5_setores,
            'heatmap_data': heatmap,
            'scores_demograficos': demographic_scores,
        })


class CampaignComparisonView(APIView):
    """GET /api/analytics/comparison/?campaigns=1,2,3"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        campaign_ids_str = request.query_params.get('campaigns', '')
        if not campaign_ids_str:
            return Response({'error': 'Parâmetro campaigns é obrigatório.'}, status=400)

        try:
            campaign_ids = [int(x.strip()) for x in campaign_ids_str.split(',')]
        except ValueError:
            return Response({'error': 'IDs de campanha inválidos.'}, status=400)

        from db_selectors.analytics_selectors import AnalyticsSelectors
        empresas = get_user_empresas(request.user)
        campaigns = Campaign.objects.filter(pk__in=campaign_ids, empresa__in=empresas)

        comparison = AnalyticsSelectors.compare_campaigns(campaigns)
        return Response(comparison)


class PsychosocialRiskMatrixView(APIView):
    """GET /api/analytics/risk-matrix/{campaign_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, campaign_id):
        campaign = get_campaign_for_user(request.user, campaign_id)

        from services.risk_calculation_service import RiskCalculationService
        risk_calc = RiskCalculationService()
        matriz = risk_calc.gerar_matriz_completa(campaign, campaign.empresa.cnae)

        return Response({
            'campaign': CampaignSerializer(campaign).data,
            'matriz': matriz,
        })


class GenerateSectorAnalysisView(APIView):
    """POST /api/analytics/sector-analysis/generate/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        campaign_id = request.data.get('campaign_id')
        setor_id = request.data.get('setor_id')

        if not campaign_id or not setor_id:
            return Response(
                {'error': 'campaign_id e setor_id são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campaign = get_campaign_for_user(request.user, campaign_id)

        # Check for recent completed analysis (24h)
        recent = SectorAnalysis.objects.filter(
            setor_id=setor_id,
            campaign_id=campaign_id,
            created_at__gte=timezone.now() - timedelta(hours=24),
            status='completed',
        ).first()

        if recent:
            return Response({
                'status': 'exists',
                'analysis_id': recent.id,
                'data': SectorAnalysisSerializer(recent).data,
            })

        task = TaskQueue.objects.create(
            task_type='generate_sector_analysis',
            payload={'setor_id': setor_id, 'campaign_id': campaign_id},
            user=request.user,
            empresa=campaign.empresa,
        )

        from tasks.ai_analysis_tasks import generate_sector_analysis
        generate_sector_analysis.delay(task.id)

        return Response(
            {
                'status': 'queued',
                'task_id': task.id,
                'poll_url': f'/api/core/tasks/{task.id}/',
            },
            status=status.HTTP_202_ACCEPTED,
        )


class SectorAnalysisDetailView(generics.RetrieveAPIView):
    """GET /api/analytics/sector-analysis/{id}/"""
    serializer_class = SectorAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        empresas = get_user_empresas(self.request.user)
        return SectorAnalysis.objects.filter(campaign__empresa__in=empresas)


class RebuildAnalyticsView(APIView):
    """POST /api/analytics/rebuild/ - Trigger star schema rebuild"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        campaign_id = request.data.get('campaign_id')
        if not campaign_id:
            return Response({'error': 'campaign_id é obrigatório.'}, status=400)

        campaign = get_campaign_for_user(request.user, campaign_id)

        from tasks.analytics_tasks import rebuild_star_schema
        result = rebuild_star_schema.delay(campaign_id)

        return Response({
            'status': 'queued',
            'celery_task_id': result.id,
            'message': f'Rebuild de analytics iniciado para campanha {campaign.nome}',
        })


class ExportDashboardExcelView(APIView):
    """GET /api/analytics/export/excel/{campaign_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, campaign_id):
        campaign = get_campaign_for_user(request.user, campaign_id)

        task = TaskQueue.objects.create(
            task_type='export_dashboard_excel',
            payload={'campaign_id': campaign_id},
            user=request.user,
            empresa=campaign.empresa,
        )

        from tasks.analytics_tasks import export_dashboard_excel
        export_dashboard_excel.delay(task.id)

        AuditService.log(
            request.user, campaign.empresa, 'export_relatorio',
            f'Exportação Excel solicitada para campanha {campaign.nome}', request
        )

        return Response({'task_id': task.id, 'status_url': f'/api/core/tasks/{task.id}/'})


class ExportRiskMatrixExcelView(APIView):
    """GET /api/analytics/export/risk-matrix/{campaign_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, campaign_id):
        campaign = get_campaign_for_user(request.user, campaign_id)

        task = TaskQueue.objects.create(
            task_type='export_risk_matrix_excel',
            payload={'campaign_id': campaign_id},
            user=request.user,
            empresa=campaign.empresa,
        )

        from tasks.analytics_tasks import export_risk_matrix_excel
        export_risk_matrix_excel.delay(task.id)

        return Response({'task_id': task.id, 'status_url': f'/api/core/tasks/{task.id}/'})
