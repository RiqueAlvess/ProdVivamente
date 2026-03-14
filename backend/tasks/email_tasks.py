"""
Celery tasks for email sending.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _update_task_status(task, status, progress=None, message='', error=''):
    """Helper to update TaskQueue status."""
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
def send_email_task(self, task_id: int):
    """
    Process a single email task from TaskQueue.
    payload: {'to': str, 'subject': str, 'html_body': str}
    """
    from apps.core.models import TaskQueue
    from services.email_service import get_email_service
    from services.notification_service import notification_service

    try:
        task = TaskQueue.objects.get(pk=task_id)
    except TaskQueue.DoesNotExist:
        logger.error('Task %d not found', task_id)
        return

    task.attempts += 1
    _update_task_status(task, 'processing', 0, 'Enviando e-mail...')

    try:
        email_svc = get_email_service()
        payload = task.payload
        success = email_svc.send(
            to=payload['to'],
            subject=payload['subject'],
            html_body=payload['html_body'],
        )

        if success:
            _update_task_status(task, 'completed', 100, 'E-mail enviado.')
            notification_service.notificar_tarefa_concluida(task)
        else:
            raise Exception('Email service returned failure')

    except Exception as exc:
        logger.error('Email task %d failed: %s', task_id, exc)
        if task.attempts < task.max_attempts:
            _update_task_status(task, 'pending', error=str(exc))
            raise self.retry(exc=exc, countdown=60 * task.attempts)
        else:
            _update_task_status(task, 'failed', error=str(exc))
            notification_service.notificar_tarefa_falhou(task)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def dispatch_campaign_emails(self, task_id: int):
    """
    Dispatch emails to all pending invitations for a campaign.
    payload: {'campaign_id': int}
    """
    from apps.core.models import TaskQueue
    from apps.invitations.models import SurveyInvitation
    from apps.surveys.models import Campaign
    from services.email_service import get_email_service
    from services.import_service import import_service
    from services.notification_service import notification_service

    try:
        task = TaskQueue.objects.get(pk=task_id)
    except TaskQueue.DoesNotExist:
        logger.error('Task %d not found', task_id)
        return

    task.attempts += 1
    _update_task_status(task, 'processing', 0, 'Iniciando disparo de e-mails...')

    try:
        campaign_id = task.payload['campaign_id']
        campaign = Campaign.objects.get(pk=campaign_id)
        empresa = campaign.empresa

        pending_invitations = SurveyInvitation.objects.filter(
            campaign=campaign,
            status='pending',
        ).select_related('empresa', 'unidade', 'setor')

        total = pending_invitations.count()
        if total == 0:
            _update_task_status(task, 'completed', 100, 'Nenhum convite pendente.')
            return

        email_svc = get_email_service()
        sent = 0
        failed = 0

        for invitation in pending_invitations:
            try:
                html_body = import_service.get_email_html(invitation, empresa)
                subject = f'Pesquisa de Clima - {empresa.nome_app}'

                # Decrypt email
                from services.crypto_service import crypto_service
                email_to = crypto_service.decrypt(invitation.email_encrypted)

                success = email_svc.send(
                    to=email_to,
                    subject=subject,
                    html_body=html_body,
                )

                if success:
                    invitation.mark_as_sent()
                    sent += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error('Failed to send invitation %s: %s', invitation.hash_token, e)
                failed += 1

            # Update progress
            progress = round((sent + failed) / total * 100)
            _update_task_status(
                task, 'processing', progress,
                f'Enviando: {sent + failed}/{total}'
            )

        result_msg = f'{sent} enviados, {failed} falhas de {total} total.'
        _update_task_status(task, 'completed', 100, result_msg)
        task.payload['result'] = {'sent': sent, 'failed': failed, 'total': total}
        task.save(update_fields=['payload'])

        logger.info('Dispatch complete for campaign %d: %s', campaign_id, result_msg)
        notification_service.notificar_tarefa_concluida(task)

    except Exception as exc:
        logger.error('Dispatch task %d failed: %s', task_id, exc)
        if task.attempts < task.max_attempts:
            _update_task_status(task, 'pending', error=str(exc))
            raise self.retry(exc=exc, countdown=60)
        else:
            _update_task_status(task, 'failed', error=str(exc))
            notification_service.notificar_tarefa_falhou(task)
