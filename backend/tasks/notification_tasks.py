"""
Celery tasks for notifications and alerts.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_action_plan_deadlines():
    """
    Check action plan deadlines and send alerts 7 days before due date.
    Called daily by Celery beat at 8 AM.
    """
    from apps.actions.models import PlanoAcao
    from services.notification_service import notification_service

    warning_date = (timezone.now() + timedelta(days=7)).date()

    plans_due = PlanoAcao.objects.filter(
        prazo=warning_date,
        status__in=['pendente', 'andamento'],
    ).select_related('empresa')

    for plan in plans_due:
        try:
            notification_service.alerta_prazo_vencendo(plan, days_remaining=7)
            logger.info('Deadline alert sent for plan %d', plan.id)
        except Exception as e:
            logger.error('Failed to send deadline alert for plan %d: %s', plan.id, e)

    # Also check overdue plans
    overdue_plans = PlanoAcao.objects.filter(
        prazo__lt=timezone.now().date(),
        status__in=['pendente', 'andamento'],
    ).select_related('empresa')

    logger.info(
        'Deadline check: %d due soon, %d overdue',
        plans_due.count(),
        overdue_plans.count()
    )


@shared_task
def check_participation_rates():
    """
    Check campaign participation rates and alert on low adherence.
    Called daily by Celery beat at 9:30 AM.
    """
    from apps.surveys.models import Campaign
    from services.notification_service import notification_service

    active_campaigns = Campaign.objects.filter(status='active').select_related('empresa')

    for campaign in active_campaigns:
        try:
            if campaign.taxa_adesao < 50 and campaign.invitations.exists():
                notification_service.alerta_adesao_baixa(campaign, campaign.empresa)
                logger.info(
                    'Low adherence alert for campaign %d: %.1f%%',
                    campaign.id, campaign.taxa_adesao
                )
        except Exception as e:
            logger.error('Failed to check participation for campaign %d: %s', campaign.id, e)


@shared_task
def expire_old_invitations():
    """Mark expired invitations as expired. Run daily."""
    from apps.invitations.models import SurveyInvitation

    expired_count = SurveyInvitation.objects.filter(
        status__in=['pending', 'sent'],
        expires_at__lt=timezone.now(),
    ).update(status='expired')

    logger.info('Expired %d invitations', expired_count)
