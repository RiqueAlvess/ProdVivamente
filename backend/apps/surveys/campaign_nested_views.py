"""
Campaign-nested API views.

Provides frontend-compatible endpoints for all resources nested under campaigns:
  /api/campaigns/campaigns/{id}/invitations/
  /api/campaigns/campaigns/{id}/invitations/import/
  /api/campaigns/campaigns/{id}/invitations/template/
  /api/campaigns/campaigns/{id}/invitations/{inv_id}/
  /api/campaigns/campaigns/{id}/invitations/send_all/
  /api/campaigns/campaigns/{id}/checklist/
  /api/campaigns/campaigns/{id}/checklist/items/{item_id}/
  /api/campaigns/campaigns/{id}/checklist/items/{item_id}/upload_evidence/
  /api/campaigns/campaigns/{id}/actions/
  /api/campaigns/campaigns/{id}/actions/{action_id}/
  /api/campaigns/campaigns/{id}/actions/export_word/

Field name translation: backend Portuguese → frontend English.
"""
import logging
import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.invitations.models import SurveyInvitation
from apps.invitations.serializers import SurveyInvitationSerializer
from apps.surveys.models import Campaign
from apps.tenants.models import Empresa
from services.audit_service import AuditService
from services.import_service import import_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_campaign(pk, user):
    """Retorna a campanha, restringindo ao grupo (empresa) do usuário."""
    if user.is_staff or user.is_superuser:
        return get_object_or_404(Campaign, pk=pk)
    try:
        empresa = user.profile.empresa
        if empresa:
            return get_object_or_404(Campaign, pk=pk, empresa=empresa)
    except Exception:
        pass
    from rest_framework.exceptions import PermissionDenied
    raise PermissionDenied('Acesso negado.')


def _serialize_invitation(inv):
    """Serialize SurveyInvitation to frontend-compatible dict."""
    return {
        'id': inv.id,
        'email_hash': inv.email_hash or str(inv.hash_token)[:16],
        'email_display': inv.email_hash or str(inv.hash_token)[:16],
        'unidade': inv.unidade_id,
        'unidade_nome': inv.unidade.nome if inv.unidade_id else None,
        'setor': inv.setor_id,
        'setor_nome': inv.setor.nome if inv.setor_id else None,
        'cargo': inv.cargo_id,
        'cargo_nome': inv.cargo.nome if inv.cargo_id else None,
        'status': inv.status,
        'sent_at': inv.sent_at.isoformat() if inv.sent_at else None,
        'completed_at': inv.used_at.isoformat() if inv.used_at else None,
        'expires_at': inv.expires_at.isoformat() if inv.expires_at else None,
        'created_at': inv.created_at.isoformat() if inv.created_at else None,
    }


STATUS_PT_TO_EN = {
    'pendente': 'pending',
    'andamento': 'in_progress',
    'concluido': 'completed',
    'cancelado': 'cancelled',
}

STATUS_EN_TO_PT = {v: k for k, v in STATUS_PT_TO_EN.items()}


def _serialize_action(plano):
    """Serialize PlanoAcao to frontend-compatible dict."""
    return {
        'id': plano.id,
        'campaign': plano.campaign_id,
        'title': plano.acao_proposta[:100] if plano.acao_proposta else '',
        'description': plano.acao_proposta or '',
        'responsible': plano.responsavel or '',
        'due_date': plano.prazo.isoformat() if plano.prazo else None,
        'dimension': plano.dimensao.nome if plano.dimensao_id else (plano.nivel_risco or ''),
        'risk_level': plano.nivel_risco or '',
        'status': STATUS_PT_TO_EN.get(plano.status, plano.status),
        'sector_name': None,
        'created_at': plano.created_at.isoformat(),
        'updated_at': plano.updated_at.isoformat(),
    }


def _serialize_checklist_item(item):
    """Serialize ChecklistNR1Item to frontend-compatible dict."""
    evidencias = item.evidencias.all()
    evidence_url = None
    evidence_filename = None
    if evidencias.exists():
        last_ev = evidencias.last()
        evidence_url = last_ev.storage_url or None
        evidence_filename = last_ev.nome_original or None

    return {
        'id': item.id,
        'stage': item.etapa_id,
        'order': item.ordem,
        'description': item.descricao,
        'is_completed': item.concluido,
        'is_automatic': item.automatico,
        'responsible': item.responsavel or None,
        'deadline': item.prazo.isoformat() if item.prazo else None,
        'notes': item.observacoes or None,
        'evidence_url': evidence_url,
        'evidence_filename': evidence_filename,
        'completed_at': item.data_conclusao.isoformat() if item.data_conclusao else None,
    }


def _serialize_checklist_stage(etapa):
    """Serialize ChecklistNR1Etapa to frontend-compatible dict."""
    items = list(etapa.itens.prefetch_related('evidencias').all())
    completed = sum(1 for i in items if i.concluido)
    total = len(items)
    progress = round(completed / total * 100, 1) if total > 0 else 0

    return {
        'id': etapa.id,
        'campaign': etapa.campaign_id,
        'stage_number': etapa.numero_etapa,
        'stage_name': etapa.nome,
        'progress': progress,
        'items': [_serialize_checklist_item(i) for i in items],
    }


# ---------------------------------------------------------------------------
# Invitation views
# ---------------------------------------------------------------------------

class CampaignInvitationListCreateView(APIView):
    """
    GET  /api/campaigns/campaigns/{id}/invitations/
    POST /api/campaigns/campaigns/{id}/invitations/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        campaign = _get_campaign(pk, request.user)
        qs = SurveyInvitation.objects.filter(campaign=campaign).select_related(
            'unidade', 'setor', 'cargo'
        ).order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        invitations = [_serialize_invitation(inv) for inv in qs]
        stats = {
            'total': qs.count(),
            'pending': qs.filter(status='pending').count(),
            'sent': qs.filter(status='sent').count(),
            'used': qs.filter(status='used').count(),
            'expired': qs.filter(status='expired').count(),
        }
        return Response({
            'count': len(invitations),
            'results': invitations,
            'stats': stats,
        })

    def post(self, request, pk):
        """Create a single invitation manually."""
        campaign = _get_campaign(pk, request.user)
        if campaign.status not in ('active', 'draft'):
            return Response(
                {'error': 'Campanha deve estar ativa ou em rascunho para adicionar convites.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = (request.data.get('email') or '').strip().lower()
        setor_id = request.data.get('setor') or request.data.get('sector')
        unidade_id = request.data.get('unidade')

        if not email:
            return Response({'error': 'E-mail é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        if '@' not in email:
            return Response({'error': 'E-mail inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        if not setor_id:
            return Response({'error': 'Setor é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.structure.models import Setor, Unidade
        setor = get_object_or_404(Setor, pk=setor_id)
        unidade = setor.unidade

        from services.crypto_service import crypto_service
        from services.token_service import token_service

        email_enc = crypto_service.encrypt(email)
        email_hash = crypto_service.compute_email_hash(email)
        nome = request.data.get('nome', email.split('@')[0])
        nome_enc = crypto_service.encrypt(nome)

        invitation = SurveyInvitation.objects.create(
            hash_token=token_service.generate_token(),
            email_encrypted=email_enc,
            email_hash=email_hash,
            nome_encrypted=nome_enc,
            empresa=campaign.empresa,
            campaign=campaign,
            unidade=unidade,
            setor=setor,
            expires_at=token_service.get_expiry_date(),
        )

        return Response(_serialize_invitation(invitation), status=status.HTTP_201_CREATED)


class CampaignInvitationDeleteView(APIView):
    """DELETE /api/campaigns/campaigns/{id}/invitations/{inv_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, inv_id):
        campaign = _get_campaign(pk, request.user)
        invitation = get_object_or_404(SurveyInvitation, pk=inv_id, campaign=campaign)
        if invitation.status == 'used':
            return Response(
                {'error': 'Não é possível remover um convite já utilizado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invitation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CampaignInvitationSendAllView(APIView):
    """POST /api/campaigns/campaigns/{id}/invitations/send_all/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        campaign = _get_campaign(pk, request.user)

        pending_count = SurveyInvitation.objects.filter(
            campaign=campaign, status='pending'
        ).count()

        if pending_count == 0:
            return Response(
                {'error': 'Nenhum convite pendente para disparar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.core.models import TaskQueue
        task = TaskQueue.objects.create(
            task_type='dispatch_emails',
            payload={'campaign_id': campaign.id},
            user=request.user,
            empresa=campaign.empresa,
        )

        from tasks.email_tasks import dispatch_campaign_emails
        dispatch_campaign_emails.delay(task.id)

        AuditService.log(
            request.user, campaign.empresa, 'disparo_email',
            f'{pending_count} e-mails despachados para campanha {campaign.nome}', request
        )

        return Response({
            'task_id': task.id,
            'status_url': f'/api/core/tasks/{task.id}/',
            'pending_count': pending_count,
        }, status=status.HTTP_202_ACCEPTED)


class CampaignInvitationImportView(APIView):
    """
    POST /api/campaigns/campaigns/{id}/invitations/import/
    Upload CSV and create invitations via Celery task.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        campaign = _get_campaign(pk, request.user)

        if campaign.status not in ('active', 'draft'):
            return Response(
                {'error': 'Campanha deve estar ativa para importar convites.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'Arquivo CSV é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            content = file.read().decode('utf-8-sig')  # Handle BOM
        except UnicodeDecodeError:
            try:
                file.seek(0)
                content = file.read().decode('latin-1')
            except Exception:
                return Response({'error': 'Arquivo deve estar em UTF-8 ou Latin-1.'}, status=status.HTTP_400_BAD_REQUEST)

        valid, error, rows = import_service.validate_csv(content)
        if not valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        from apps.core.models import TaskQueue
        task = TaskQueue.objects.create(
            task_type='import_csv',
            payload={
                'campaign_id': campaign.id,
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

        return Response({
            'task_id': task.id,
            'status_url': f'/api/core/tasks/{task.id}/',
            'total_rows': len(rows),
        }, status=status.HTTP_202_ACCEPTED)


class CampaignInvitationTemplateView(APIView):
    """GET /api/campaigns/campaigns/{id}/invitations/template/ — Download CSV template"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        # Validate campaign access
        _get_campaign(pk, request.user)
        csv_content = import_service.get_template_csv(separator=';')
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="modelo_funcionarios.csv"'
        return response


# ---------------------------------------------------------------------------
# Checklist views (NR-1 compliant)
# ---------------------------------------------------------------------------

class CampaignChecklistView(APIView):
    """
    GET  /api/campaigns/campaigns/{id}/checklist/
    Auto-creates checklist if it doesn't exist.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from apps.actions.models import ChecklistNR1Etapa, ChecklistNR1Item
        from apps.actions.views import NR1_CHECKLIST_TEMPLATE

        campaign = _get_campaign(pk, request.user)

        etapas = ChecklistNR1Etapa.objects.filter(campaign=campaign).prefetch_related(
            'itens__evidencias'
        ).order_by('numero_etapa')

        if not etapas.exists():
            etapas = self._create_default_checklist(campaign)
            self._auto_mark_items(campaign, etapas)

        stages = [_serialize_checklist_stage(e) for e in etapas]
        all_items = [i for s in stages for i in s['items']]
        total = len(all_items)
        completed_count = sum(1 for i in all_items if i['is_completed'])
        overall_progress = round(completed_count / total * 100, 1) if total > 0 else 0

        return Response({
            'stages': stages,
            'progress': {
                'campaign_id': campaign.id,
                'overall_progress': overall_progress,
                'stages': [
                    {
                        'stage_number': s['stage_number'],
                        'stage_name': s['stage_name'],
                        'progress': s['progress'],
                    }
                    for s in stages
                ],
            },
        })

    def _create_default_checklist(self, campaign):
        from apps.actions.models import ChecklistNR1Etapa, ChecklistNR1Item
        from apps.actions.views import NR1_CHECKLIST_TEMPLATE

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

        return ChecklistNR1Etapa.objects.filter(campaign=campaign).prefetch_related(
            'itens__evidencias'
        ).order_by('numero_etapa')

    def _auto_mark_items(self, campaign, etapas):
        from apps.actions.models import ChecklistNR1Item
        has_responses = campaign.respostas.exists()

        for etapa in etapas:
            for item in etapa.itens.filter(automatico=True):
                if 'Selecionar' in item.descricao and 'HSE-IT' in item.descricao:
                    item.marcar_concluido(responsavel='Sistema')
                elif 'Aplicar questionário' in item.descricao and has_responses:
                    item.marcar_concluido(responsavel='Sistema')


class CampaignChecklistCreateView(APIView):
    """POST /api/campaigns/campaigns/{id}/checklist/create/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from apps.actions.models import ChecklistNR1Etapa
        campaign = _get_campaign(pk, request.user)

        if ChecklistNR1Etapa.objects.filter(campaign=campaign).exists():
            return Response({'detail': 'Checklist já existe para esta campanha.'})

        view = CampaignChecklistView()
        etapas = view._create_default_checklist(campaign)
        view._auto_mark_items(campaign, etapas)

        return Response({'detail': 'Checklist NR-1 criado com sucesso.'}, status=status.HTTP_201_CREATED)


class CampaignChecklistItemUpdateView(APIView):
    """PATCH /api/campaigns/campaigns/{id}/checklist/items/{item_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk, item_id):
        from apps.actions.models import ChecklistNR1Item
        campaign = _get_campaign(pk, request.user)
        item = get_object_or_404(ChecklistNR1Item, pk=item_id, etapa__campaign=campaign)

        if item.automatico:
            return Response(
                {'error': 'Itens automáticos não podem ser editados manualmente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        update_fields = []

        if 'is_completed' in data:
            is_completed = bool(data['is_completed'])
            if is_completed and not item.concluido:
                item.concluido = True
                item.data_conclusao = timezone.now()
                responsible = data.get('responsible', '')
                if responsible:
                    item.responsavel = responsible
                update_fields.extend(['concluido', 'data_conclusao', 'responsavel'])
            elif not is_completed and item.concluido:
                item.concluido = False
                item.data_conclusao = None
                update_fields.extend(['concluido', 'data_conclusao'])

        if 'responsible' in data:
            item.responsavel = data['responsible'] or ''
            if 'responsavel' not in update_fields:
                update_fields.append('responsavel')

        if 'deadline' in data:
            item.prazo = data['deadline'] or None
            update_fields.append('prazo')

        if 'notes' in data:
            item.observacoes = data['notes'] or ''
            update_fields.append('observacoes')

        if update_fields:
            item.save(update_fields=update_fields)

        return Response(_serialize_checklist_item(item))


class CampaignChecklistItemEvidenceView(APIView):
    """PATCH /api/campaigns/campaigns/{id}/checklist/items/{item_id}/upload_evidence/"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, pk, item_id):
        from apps.actions.models import ChecklistNR1Item, EvidenciaNR1
        from services.storage_service import storage_service
        from django.conf import settings

        campaign = _get_campaign(pk, request.user)
        item = get_object_or_404(ChecklistNR1Item, pk=item_id, etapa__campaign=campaign)

        file = request.FILES.get('evidence')
        if not file:
            return Response({'error': 'Arquivo de evidência é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > 10 * 1024 * 1024:
            return Response({'error': 'Arquivo muito grande. Máximo: 10MB.'}, status=status.HTTP_400_BAD_REQUEST)

        empresa = campaign.empresa
        storage_path = f'{empresa.id}/nr1/{campaign.id}/item-{item_id}/{file.name}'

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

        EvidenciaNR1.objects.create(
            checklist_item=item,
            empresa=empresa,
            nome_original=file.name,
            storage_path=storage_path,
            storage_url=public_url,
            tamanho_bytes=file.size,
            uploaded_by=request.user,
        )

        return Response({
            'evidence_url': public_url,
            'evidence_filename': file.name,
        })


# ---------------------------------------------------------------------------
# Action Plan views
# ---------------------------------------------------------------------------

class CampaignActionsView(APIView):
    """
    GET  /api/campaigns/campaigns/{id}/actions/
    POST /api/campaigns/campaigns/{id}/actions/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from apps.actions.models import PlanoAcao
        campaign = _get_campaign(pk, request.user)

        qs = PlanoAcao.objects.filter(campaign=campaign).select_related(
            'dimensao'
        ).order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            pt_status = STATUS_EN_TO_PT.get(status_filter, status_filter)
            qs = qs.filter(status=pt_status)

        actions = [_serialize_action(p) for p in qs]
        return Response({'count': len(actions), 'results': actions})

    def post(self, request, pk):
        from apps.actions.models import PlanoAcao
        from apps.surveys.models import Dimensao
        campaign = _get_campaign(pk, request.user)

        title = request.data.get('title', '')
        description = request.data.get('description', title)
        responsible = request.data.get('responsible', '')
        due_date = request.data.get('due_date') or None
        dimension_name = request.data.get('dimension', '')
        en_status = request.data.get('status', 'pending')
        pt_status = STATUS_EN_TO_PT.get(en_status, 'pendente')
        risk_level = request.data.get('risk_level', '')

        # Try to find dimension by name
        dimensao = None
        if dimension_name:
            dimensao = Dimensao.objects.filter(nome__icontains=dimension_name).first()

        plano = PlanoAcao.objects.create(
            empresa=campaign.empresa,
            campaign=campaign,
            dimensao=dimensao,
            nivel_risco=risk_level,
            acao_proposta=description or title,
            responsavel=responsible,
            prazo=due_date,
            status=pt_status,
            created_by=request.user,
        )

        AuditService.log(
            request.user, campaign.empresa, 'update_action',
            f'Plano de ação criado: #{plano.id}', request
        )

        return Response(_serialize_action(plano), status=status.HTTP_201_CREATED)


class CampaignActionDetailView(APIView):
    """PATCH /api/campaigns/campaigns/{id}/actions/{action_id}/"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk, action_id):
        from apps.actions.models import PlanoAcao
        campaign = _get_campaign(pk, request.user)
        plano = get_object_or_404(PlanoAcao, pk=action_id, campaign=campaign)

        update_fields = []

        if 'status' in request.data:
            en_status = request.data['status']
            pt_status = STATUS_EN_TO_PT.get(en_status, en_status)
            plano.status = pt_status
            update_fields.append('status')

        if 'description' in request.data:
            plano.acao_proposta = request.data['description']
            update_fields.append('acao_proposta')

        if 'title' in request.data:
            plano.acao_proposta = request.data['title']
            update_fields.append('acao_proposta')

        if 'responsible' in request.data:
            plano.responsavel = request.data['responsible'] or ''
            update_fields.append('responsavel')

        if 'due_date' in request.data:
            plano.prazo = request.data['due_date'] or None
            update_fields.append('prazo')

        if update_fields:
            update_fields.append('updated_at')
            plano.save(update_fields=update_fields)

        return Response(_serialize_action(plano))


class CampaignActionsExportWordView(APIView):
    """POST /api/campaigns/campaigns/{id}/actions/export_word/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from apps.core.models import TaskQueue
        campaign = _get_campaign(pk, request.user)

        task = TaskQueue.objects.create(
            task_type='export_plano_acao',
            payload={'campaign_id': campaign.id},
            user=request.user,
            empresa=campaign.empresa,
        )

        return Response({
            'task_id': task.id,
            'status_url': f'/api/core/tasks/{task.id}/',
            'message': 'Exportação iniciada.',
        }, status=status.HTTP_202_ACCEPTED)
