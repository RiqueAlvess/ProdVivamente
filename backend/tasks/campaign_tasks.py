"""
Celery tasks for campaign management (CSV import, etc.).
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_csv_import(self, task_id: int):
    """
    Process CSV import task - create SurveyInvitation records.
    payload: {'campaign_id': int, 'empresa_id': str, 'rows': list}
    """
    from apps.core.models import TaskQueue
    from apps.surveys.models import Campaign
    from apps.invitations.models import SurveyInvitation
    from apps.structure.models import Unidade, Setor, Cargo
    from apps.tenants.models import Empresa
    from services.crypto_service import crypto_service
    from services.token_service import token_service
    from services.notification_service import notification_service

    try:
        task = TaskQueue.objects.get(pk=task_id)
    except TaskQueue.DoesNotExist:
        logger.error('Task %d not found', task_id)
        return

    task.attempts += 1
    _update_task(task, 'processing', 0, 'Iniciando importação...')

    try:
        payload = task.payload
        campaign_id = payload['campaign_id']
        empresa_id = payload['empresa_id']
        rows = payload['rows']

        campaign = Campaign.objects.get(pk=campaign_id)
        empresa = Empresa.objects.get(pk=empresa_id)

        total = len(rows)
        created = 0
        skipped = 0
        errors = []

        for i, row in enumerate(rows):
            try:
                # Get or create Unidade
                unidade, _ = Unidade.objects.get_or_create(
                    empresa=empresa,
                    nome=row['unidade'].strip(),
                )

                # Get or create Setor
                setor, _ = Setor.objects.get_or_create(
                    unidade=unidade,
                    nome=row['setor'].strip(),
                )

                # Get or create Cargo (optional)
                cargo = None
                if row.get('cargo'):
                    cargo, _ = Cargo.objects.get_or_create(
                        empresa=empresa,
                        nome=row['cargo'].strip(),
                    )

                # Encrypt PII
                email_enc = crypto_service.encrypt(row['email'].lower())
                nome_enc = crypto_service.encrypt(row['nome'])

                # Create invitation
                invitation = SurveyInvitation.objects.create(
                    hash_token=token_service.generate_token(),
                    email_encrypted=email_enc,
                    nome_encrypted=nome_enc,
                    empresa=empresa,
                    campaign=campaign,
                    unidade=unidade,
                    setor=setor,
                    cargo=cargo,
                    expires_at=token_service.get_expiry_date(),
                )
                created += 1

            except Exception as e:
                logger.warning('Failed to create invitation for row %d: %s', i, e)
                errors.append(f'Linha {i + 2}: {str(e)[:100]}')
                skipped += 1

            # Update progress
            progress = round((i + 1) / total * 100)
            if (i + 1) % 10 == 0 or i + 1 == total:
                _update_task(task, 'processing', progress, f'Processando {i + 1}/{total}...')

        result = {
            'created': created,
            'skipped': skipped,
            'total': total,
            'errors': errors[:10],
        }

        task.payload = {**payload, 'result': result}
        _update_task(task, 'completed', 100, f'{created} convites criados, {skipped} ignorados.')
        task.save(update_fields=['payload'])

        logger.info(
            'CSV import complete for campaign %d: %d created, %d skipped',
            campaign_id, created, skipped
        )
        notification_service.notificar_tarefa_concluida(task)

    except Exception as exc:
        logger.error('CSV import task %d failed: %s', task_id, exc)
        if task.attempts < task.max_attempts:
            _update_task(task, 'pending', error=str(exc))
            raise self.retry(exc=exc, countdown=60)
        else:
            _update_task(task, 'failed', error=str(exc))
            notification_service.notificar_tarefa_falhou(task)


@shared_task
def process_pending_tasks():
    """
    Process any tasks stuck in 'pending' state for too long.
    Called by Celery beat every 30 seconds.
    """
    from apps.core.models import TaskQueue
    from datetime import timedelta

    # Find tasks that are pending but should have been processed
    cutoff = timezone.now() - timedelta(minutes=5)
    pending_tasks = TaskQueue.objects.filter(
        status='pending',
        attempts__lt=models_max_attempts(),
        created_at__lt=cutoff,
    ).order_by('created_at')[:10]

    for task in pending_tasks:
        logger.info('Re-queuing stale pending task %d (%s)', task.id, task.task_type)
        _dispatch_task(task)


def models_max_attempts():
    return 3


def _dispatch_task(task):
    """Dispatch a task to the appropriate Celery worker."""
    dispatch_map = {
        'import_csv': 'tasks.campaign_tasks.process_csv_import',
        'dispatch_emails': 'tasks.email_tasks.dispatch_campaign_emails',
        'generate_sector_analysis': 'tasks.ai_analysis_tasks.generate_sector_analysis',
        'generate_action_plan': 'tasks.ai_analysis_tasks.generate_action_plan',
        'export_dashboard_excel': 'tasks.analytics_tasks.export_dashboard_excel',
        'export_risk_matrix_excel': 'tasks.analytics_tasks.export_risk_matrix_excel',
    }

    celery_task_path = dispatch_map.get(task.task_type)
    if not celery_task_path:
        logger.warning('Unknown task type: %s', task.task_type)
        return

    module_path, func_name = celery_task_path.rsplit('.', 1)
    try:
        import importlib
        module = importlib.import_module(module_path)
        celery_task = getattr(module, func_name)
        celery_task.delay(task.id)
        logger.info('Re-dispatched task %d (%s)', task.id, task.task_type)
    except Exception as e:
        logger.error('Failed to dispatch task %d: %s', task.id, e)
