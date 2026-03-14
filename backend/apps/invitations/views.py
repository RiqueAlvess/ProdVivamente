"""
Invitations views - CSV import, email dispatch, listing.
"""
import logging

from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import SurveyInvitation
from .serializers import SurveyInvitationSerializer
from apps.surveys.models import Campaign
from apps.core.models import TaskQueue
from apps.tenants.models import Empresa
from services.audit_service import AuditService
from services.import_service import import_service

logger = logging.getLogger(__name__)


def get_user_empresa(user, empresa_id=None):
    """Get empresa for user - raises PermissionError if not allowed."""
    if user.is_staff or user.is_superuser:
        if empresa_id:
            return get_object_or_404(Empresa, pk=empresa_id)
        return None
    if hasattr(user, 'profile'):
        empresas = user.profile.empresas.filter(ativo=True)
        if empresa_id:
            emp = empresas.filter(pk=empresa_id).first()
            if not emp:
                raise PermissionError('Acesso negado a esta empresa.')
            return emp
        return empresas.first()
    raise PermissionError('Usuário sem empresa associada.')


class ImportCSVView(APIView):
    """
    POST /api/invitations/import/
    Upload CSV and create invitations via Celery task.
    Expected CSV columns: nome, email, unidade, setor, cargo (optional)
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')
        campaign_id = request.data.get('campaign_id')

        if not file:
            return Response({'error': 'Arquivo CSV é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        if not campaign_id:
            return Response({'error': 'campaign_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            campaign = Campaign.objects.get(pk=campaign_id, status='active')
        except Campaign.DoesNotExist:
            return Response(
                {'error': 'Campanha não encontrada ou não está ativa.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            empresa = get_user_empresa(request.user, campaign.empresa_id)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

        try:
            content = file.read().decode('utf-8-sig')  # Handle BOM
        except UnicodeDecodeError:
            return Response({'error': 'Arquivo deve estar em UTF-8.'}, status=status.HTTP_400_BAD_REQUEST)

        valid, error, rows = import_service.validate_csv(content)
        if not valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        task = TaskQueue.objects.create(
            task_type='import_csv',
            payload={
                'campaign_id': campaign_id,
                'rows': rows,
                'empresa_id': str(campaign.empresa_id),
            },
            user=request.user,
            empresa=campaign.empresa,
        )

        from tasks.campaign_tasks import process_csv_import
        process_csv_import.delay(task.id)

        AuditService.log(
            request.user, campaign.empresa, 'import_csv',
            f'{len(rows)} registros importados para campanha {campaign.nome}', request
        )

        return Response(
            {
                'task_id': task.id,
                'status_url': f'/api/core/tasks/{task.id}/',
                'total_rows': len(rows),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class DispatchEmailsView(APIView):
    """
    POST /api/invitations/campaigns/{campaign_id}/dispatch/
    Dispatch emails to all pending invitations.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, campaign_id):
        try:
            empresa = get_user_empresa(request.user)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

        campaign = get_object_or_404(Campaign, pk=campaign_id)

        pending_count = SurveyInvitation.objects.filter(
            campaign=campaign, status='pending'
        ).count()

        if pending_count == 0:
            return Response(
                {'error': 'Nenhum convite pendente para disparar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = TaskQueue.objects.create(
            task_type='dispatch_emails',
            payload={'campaign_id': campaign_id},
            user=request.user,
            empresa=campaign.empresa,
        )

        from tasks.email_tasks import dispatch_campaign_emails
        dispatch_campaign_emails.delay(task.id)

        AuditService.log(
            request.user, campaign.empresa, 'disparo_email',
            f'{pending_count} e-mails despachados para campanha {campaign.nome}', request
        )

        return Response(
            {
                'task_id': task.id,
                'status_url': f'/api/core/tasks/{task.id}/',
                'pending_count': pending_count,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class InvitationListView(generics.ListAPIView):
    """GET /api/invitations/ - List invitations with filters"""
    serializer_class = SurveyInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            qs = SurveyInvitation.objects.all()
        elif hasattr(user, 'profile'):
            qs = SurveyInvitation.objects.filter(empresa__in=user.profile.empresas.all())
        else:
            return SurveyInvitation.objects.none()

        qs = qs.select_related('empresa', 'campaign', 'unidade', 'setor', 'cargo')

        campaign_id = self.request.query_params.get('campaign_id')
        status_filter = self.request.query_params.get('status')
        unidade_id = self.request.query_params.get('unidade_id')
        setor_id = self.request.query_params.get('setor_id')

        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if unidade_id:
            qs = qs.filter(unidade_id=unidade_id)
        if setor_id:
            qs = qs.filter(setor_id=setor_id)

        return qs


class InvitationStatsView(APIView):
    """GET /api/invitations/campaigns/{campaign_id}/stats/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, pk=campaign_id)
        invitations = SurveyInvitation.objects.filter(campaign=campaign)

        stats = {
            'total': invitations.count(),
            'pending': invitations.filter(status='pending').count(),
            'sent': invitations.filter(status='sent').count(),
            'used': invitations.filter(status='used').count(),
            'expired': invitations.filter(status='expired').count(),
        }
        stats['taxa_uso'] = round(
            stats['used'] / stats['total'] * 100, 1
        ) if stats['total'] > 0 else 0

        return Response(stats)
