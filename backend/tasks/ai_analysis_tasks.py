"""
Celery tasks for AI analysis.
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


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_sector_analysis(self, task_id: int):
    """
    Generate AI-powered sector analysis.
    payload: {'setor_id': int, 'campaign_id': int}
    """
    from apps.core.models import TaskQueue
    from apps.analytics.models import SectorAnalysis
    from apps.structure.models import Setor
    from apps.surveys.models import Campaign
    from services.sector_analysis_service import sector_analysis_service
    from services.notification_service import notification_service

    try:
        task = TaskQueue.objects.get(pk=task_id)
    except TaskQueue.DoesNotExist:
        logger.error('Task %d not found', task_id)
        return

    task.attempts += 1
    _update_task(task, 'processing', 10, 'Iniciando análise de setor...')

    # Create/update SectorAnalysis record
    setor_id = task.payload['setor_id']
    campaign_id = task.payload['campaign_id']

    try:
        setor = Setor.objects.get(pk=setor_id)
        campaign = Campaign.objects.get(pk=campaign_id)

        analysis, _ = SectorAnalysis.objects.get_or_create(
            setor=setor,
            campaign=campaign,
            defaults={'status': 'processing'},
        )
        analysis.status = 'processing'
        analysis.save(update_fields=['status'])

        _update_task(task, 'processing', 30, 'Calculando scores...')
        result = sector_analysis_service.gerar_analise(campaign, setor)

        _update_task(task, 'processing', 80, 'Salvando análise...')
        analysis.status = 'completed'
        analysis.pontos_criticos = result.get('pontos_criticos', [])
        analysis.recomendacoes = result.get('recomendacoes', [])
        analysis.analise_completa = result.get('analise_completa', '')
        analysis.modelo_ia = result.get('modelo_ia', '')
        analysis.save()

        task.payload['analysis_id'] = analysis.id
        task.save(update_fields=['payload'])

        _update_task(task, 'completed', 100, 'Análise concluída.')
        notification_service.notificar_tarefa_concluida(task)

    except Exception as exc:
        logger.error('Sector analysis task %d failed: %s', task_id, exc)
        # Mark analysis as failed if it exists
        try:
            SectorAnalysis.objects.filter(
                setor_id=setor_id, campaign_id=campaign_id, status='processing'
            ).update(status='failed', error_message=str(exc))
        except Exception:
            pass

        if task.attempts < task.max_attempts:
            _update_task(task, 'pending', error=str(exc))
            raise self.retry(exc=exc, countdown=120)
        else:
            _update_task(task, 'failed', error=str(exc))
            notification_service.notificar_tarefa_falhou(task)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def analyze_sentiment(self, response_id: int):
    """
    Analyze sentiment of a survey response comment.
    Called automatically after survey submission if comment exists.
    """
    from apps.responses.models import SurveyResponse
    from services.sentiment_service import sentiment_service

    try:
        response = SurveyResponse.objects.get(pk=response_id)
    except SurveyResponse.DoesNotExist:
        logger.warning('SurveyResponse %d not found for sentiment analysis', response_id)
        return

    if not response.comentario_livre:
        return

    try:
        result = sentiment_service.analisar(response.comentario_livre)
        response.sentimento_score = result.get('score')
        response.sentimento_categorias = result
        response.save(update_fields=['sentimento_score', 'sentimento_categorias'])
        logger.info('Sentiment analysis complete for response %d', response_id)
    except Exception as exc:
        logger.error('Sentiment analysis failed for response %d: %s', response_id, exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_action_plan(self, task_id: int):
    """
    Generate AI action plan for a dimension.
    payload: {'campaign_id': int, 'dimensao_id': int}
    """
    from apps.core.models import TaskQueue
    from apps.actions.models import PlanoAcao
    from apps.surveys.models import Campaign, Dimensao
    from services.ai_service import get_ai_service
    from services.score_service import score_service, TIPO_DIMENSAO
    from services.notification_service import notification_service

    try:
        task = TaskQueue.objects.get(pk=task_id)
    except TaskQueue.DoesNotExist:
        return

    task.attempts += 1
    _update_task(task, 'processing', 10, 'Gerando plano de ação com IA...')

    try:
        campaign_id = task.payload['campaign_id']
        dimensao_id = task.payload['dimensao_id']

        campaign = Campaign.objects.get(pk=campaign_id)
        dimensao = Dimensao.objects.get(pk=dimensao_id)

        # Calculate score for this dimension
        scores = score_service.calcular_medias_campanha(campaign)
        dim_data = scores.get(dimensao.codigo, {})
        score = dim_data.get('media')
        nivel = dim_data.get('nivel', 'moderado')

        context = {
            'dimensao': dimensao.nome,
            'nivel_risco': nivel,
            'score': score,
            'empresa': campaign.empresa.nome,
            'setor': 'Geral',
            'fatores_risco': [],
        }

        _update_task(task, 'processing', 40, 'Consultando IA...')
        ai = get_ai_service()
        result = ai.gerar_plano_acao(context)

        _update_task(task, 'processing', 80, 'Salvando plano...')
        plano = PlanoAcao.objects.create(
            empresa=campaign.empresa,
            campaign=campaign,
            dimensao=dimensao,
            nivel_risco=nivel,
            acao_proposta=result.get('acao_proposta', ''),
            recursos_necessarios=result.get('recursos_necessarios', ''),
            indicadores=result.get('indicadores', ''),
            gerado_por_ia=True,
            created_by=task.user,
        )

        task.payload['plano_id'] = plano.id
        task.save(update_fields=['payload'])

        _update_task(task, 'completed', 100, 'Plano de ação gerado.')
        notification_service.notificar_tarefa_concluida(task)

    except Exception as exc:
        logger.error('Action plan task %d failed: %s', task_id, exc)
        if task.attempts < task.max_attempts:
            _update_task(task, 'pending', error=str(exc))
            raise self.retry(exc=exc, countdown=60)
        else:
            _update_task(task, 'failed', error=str(exc))
            notification_service.notificar_tarefa_falhou(task)
