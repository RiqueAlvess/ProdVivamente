"""
Celery tasks for analytics and star schema updates.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _update_task(task, status, progress=None, message='', error=''):
    task.status = status
    if progress is not None:
        task.progress = progress
    if message:
        task.progress_message = message
    if error:
        task.error_message = error
    if status == 'processing' and not task.started_at:
        task.started_at = timezone.now()
    if status in ('completed', 'failed'):
        task.completed_at = timezone.now()
    task.save()


@shared_task
def rebuild_star_schema(campaign_id: int):
    """
    Rebuild the analytics star schema for a campaign.
    Updates DimEstrutura, FactScoreDimensao, FactIndicadorCampanha, FactRespostaPergunta.
    """
    from apps.surveys.models import Campaign
    from apps.analytics.models import (
        DimEstrutura, DimDimensaoHSE, FactScoreDimensao, FactIndicadorCampanha, FactRespostaPergunta
    )
    from apps.responses.models import SurveyResponse
    from services.score_service import score_service, DIMENSOES, TIPO_DIMENSAO
    from django.db.models import Count

    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        logger.error('Campaign %d not found for star schema rebuild', campaign_id)
        return

    respostas = SurveyResponse.objects.filter(campaign=campaign)
    total = respostas.count()

    logger.info('Rebuilding star schema for campaign %d (%d responses)', campaign_id, total)

    # Ensure DimDimensaoHSE records exist
    for dim_codigo, tipo in TIPO_DIMENSAO.items():
        DimDimensaoHSE.objects.get_or_create(
            codigo=dim_codigo,
            defaults={'nome': dim_codigo.replace('_', ' ').title(), 'tipo': tipo}
        )

    # Update campaign KPIs
    invitations_count = campaign.invitations.count()
    taxa_adesao = round(total / invitations_count * 100, 1) if invitations_count > 0 else 0.0

    FactIndicadorCampanha.objects.update_or_create(
        campaign=campaign,
        defaults={
            'total_convidados': invitations_count,
            'total_respondidos': total,
            'taxa_adesao': taxa_adesao,
        }
    )

    # Process scores by setor
    setores = respostas.values('setor', 'unidade').distinct()

    for setor_data in setores:
        setor_id = setor_data['setor']
        unidade_id = setor_data['unidade']

        from apps.structure.models import Setor, Unidade
        try:
            setor = Setor.objects.get(pk=setor_id)
            unidade = Unidade.objects.get(pk=unidade_id)
        except (Setor.DoesNotExist, Unidade.DoesNotExist):
            continue

        # Ensure DimEstrutura exists
        dim_estrutura, _ = DimEstrutura.objects.get_or_create(
            unidade=unidade,
            setor=setor,
            defaults={
                'unidade_nome': unidade.nome,
                'setor_nome': setor.nome,
            }
        )

        setor_respostas = respostas.filter(setor_id=setor_id)
        setor_count = setor_respostas.count()

        if setor_count < 5:  # K-anonymity
            continue

        # Calculate scores per dimension for this sector
        for dim_codigo in DIMENSOES:
            dim_scores = []
            for r in setor_respostas:
                s = score_service.calcular_score_dimensao(r.respostas, dim_codigo)
                if s is not None:
                    dim_scores.append(s)

            if not dim_scores:
                continue

            score_medio = sum(dim_scores) / len(dim_scores)
            tipo = TIPO_DIMENSAO[dim_codigo]
            nivel = score_service.classificar_risco(score_medio, tipo)

            dim_dimensao = DimDimensaoHSE.objects.get(codigo=dim_codigo)

            FactScoreDimensao.objects.update_or_create(
                campaign=campaign,
                dim_estrutura=dim_estrutura,
                dim_dimensao=dim_dimensao,
                defaults={
                    'score_medio': round(score_medio, 3),
                    'nivel_risco': nivel,
                    'total_respostas': setor_count,
                }
            )

        # Update question distribution
        for pergunta_num in range(1, 36):
            contagens = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
            total_q = 0
            soma = 0
            for r in setor_respostas:
                val = r.respostas.get(str(pergunta_num))
                if val is not None:
                    try:
                        v = int(val)
                        contagens[v] = contagens.get(v, 0) + 1
                        total_q += 1
                        soma += v
                    except (ValueError, TypeError):
                        pass

            if total_q > 0:
                FactRespostaPergunta.objects.update_or_create(
                    campaign=campaign,
                    dim_estrutura=dim_estrutura,
                    pergunta_numero=pergunta_num,
                    defaults={
                        'valor_0': contagens[0],
                        'valor_1': contagens[1],
                        'valor_2': contagens[2],
                        'valor_3': contagens[3],
                        'valor_4': contagens[4],
                        'total': total_q,
                        'media': round(soma / total_q, 3),
                    }
                )

    logger.info('Star schema rebuild complete for campaign %d', campaign_id)


@shared_task
def rebuild_all_active_campaigns():
    """Rebuild analytics for all active campaigns. Called by Celery beat."""
    from apps.surveys.models import Campaign
    campaigns = Campaign.objects.filter(status='active')
    for campaign in campaigns:
        rebuild_star_schema.delay(campaign.id)
    logger.info('Queued rebuild for %d active campaigns', campaigns.count())


@shared_task
def cleanup_expired_exports():
    """Delete exported files older than 24 hours from Supabase Storage."""
    from apps.core.models import TaskQueue
    from services.storage_service import storage_service
    from django.conf import settings
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(hours=24)
    old_tasks = TaskQueue.objects.filter(
        status='completed',
        file_path__gt='',
        completed_at__lt=cutoff,
    )

    deleted = 0
    for task in old_tasks:
        try:
            storage_service.delete(settings.SUPABASE_BUCKET_EXPORTS, [task.file_path])
            task.file_path = ''
            task.file_url = ''
            task.file_name = ''
            task.save(update_fields=['file_path', 'file_url', 'file_name'])
            deleted += 1
        except Exception as e:
            logger.warning('Failed to delete export %s: %s', task.file_path, e)

    logger.info('Cleaned up %d expired export files', deleted)


@shared_task
def compute_dashboard_cache(campaign_id: int):
    """Pre-compute and cache dashboard data for fast access."""
    from django.core.cache import cache
    from apps.surveys.models import Campaign
    from db_selectors.dashboard_selectors import DashboardSelectors
    from services.risk_service import RiskService

    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        return

    risk_svc = RiskService()
    cache_key = f'dashboard_campaign_{campaign_id}'
    data = {
        'metrics': DashboardSelectors.get_metrics(campaign),
        'dimensoes_scores': DashboardSelectors.get_dimensoes_scores(campaign),
        'distribuicao_riscos': risk_svc.get_distribuicao_riscos(campaign),
        'igrp': risk_svc.calcular_igrp(campaign),
    }
    cache.set(cache_key, data, timeout=3600)  # 1 hour cache
    logger.info('Dashboard cache computed for campaign %d', campaign_id)


@shared_task
def export_dashboard_excel(task_id: int):
    """Export dashboard data to Excel and upload to Supabase."""
    from apps.core.models import TaskQueue
    from apps.surveys.models import Campaign
    from services.export_service import export_service
    from services.storage_service import storage_service
    from services.notification_service import notification_service
    from django.conf import settings

    try:
        task = TaskQueue.objects.get(pk=task_id)
    except TaskQueue.DoesNotExist:
        return

    _update_task(task, 'processing', 10, 'Gerando relatório Excel...')

    try:
        campaign_id = task.payload['campaign_id']
        campaign = Campaign.objects.get(pk=campaign_id)

        excel_bytes = export_service.gerar_excel_dashboard(campaign)
        filename = f'dashboard_{campaign.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        storage_path = f'{campaign.empresa_id}/exports/{filename}'

        _update_task(task, 'processing', 70, 'Enviando arquivo...')
        storage_service.upload(
            bucket=settings.SUPABASE_BUCKET_EXPORTS,
            path=storage_path,
            file_content=excel_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        file_url = storage_service.get_signed_url(
            settings.SUPABASE_BUCKET_EXPORTS, storage_path, expires_in=86400
        )

        task.file_path = storage_path
        task.file_name = filename
        task.file_size = len(excel_bytes)
        task.file_url = file_url
        task.save(update_fields=['file_path', 'file_name', 'file_size', 'file_url'])

        _update_task(task, 'completed', 100, 'Relatório pronto para download.')
        notification_service.notificar_tarefa_concluida(task)

    except Exception as exc:
        logger.error('Export Excel task %d failed: %s', task_id, exc)
        _update_task(task, 'failed', error=str(exc))
        notification_service.notificar_tarefa_falhou(task)


@shared_task
def export_risk_matrix_excel(task_id: int):
    """Export risk matrix to Excel."""
    from apps.core.models import TaskQueue
    from apps.surveys.models import Campaign
    from services.export_service import export_service
    from services.storage_service import storage_service
    from services.notification_service import notification_service
    from django.conf import settings

    try:
        task = TaskQueue.objects.get(pk=task_id)
    except TaskQueue.DoesNotExist:
        return

    _update_task(task, 'processing', 10, 'Gerando matriz de riscos...')

    try:
        campaign_id = task.payload['campaign_id']
        campaign = Campaign.objects.get(pk=campaign_id)

        excel_bytes = export_service.gerar_excel_risk_matrix(campaign)
        filename = f'matriz_risco_{campaign.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        storage_path = f'{campaign.empresa_id}/exports/{filename}'

        _update_task(task, 'processing', 70, 'Enviando arquivo...')
        storage_service.upload(
            bucket=settings.SUPABASE_BUCKET_EXPORTS,
            path=storage_path,
            file_content=excel_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        file_url = storage_service.get_signed_url(
            settings.SUPABASE_BUCKET_EXPORTS, storage_path, expires_in=86400
        )

        task.file_path = storage_path
        task.file_name = filename
        task.file_size = len(excel_bytes)
        task.file_url = file_url
        task.save(update_fields=['file_path', 'file_name', 'file_size', 'file_url'])

        _update_task(task, 'completed', 100, 'Matriz de riscos pronta.')
        notification_service.notificar_tarefa_concluida(task)

    except Exception as exc:
        logger.error('Risk matrix export task %d failed: %s', task_id, exc)
        _update_task(task, 'failed', error=str(exc))
        notification_service.notificar_tarefa_falhou(task)
