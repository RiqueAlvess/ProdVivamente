"""
Celery configuration for VIVAMENTE 360º.
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('vivamente')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# ---------------------------------------------------------------------------
# Beat Schedule
# ---------------------------------------------------------------------------
app.conf.beat_schedule = {
    # Process pending tasks from TaskQueue every 30 seconds
    'process-pending-tasks': {
        'task': 'tasks.campaign_tasks.process_pending_tasks',
        'schedule': 30.0,
        'options': {'expires': 25},
    },
    # Cleanup expired exports every hour
    'cleanup-expired-exports': {
        'task': 'tasks.analytics_tasks.cleanup_expired_exports',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {'expires': 3600},
    },
    # Rebuild analytics star schema every 6 hours
    'rebuild-analytics': {
        'task': 'tasks.analytics_tasks.rebuild_all_active_campaigns',
        'schedule': crontab(minute=0, hour='*/6'),
        'options': {'expires': 21600},
    },
    # Check action plan deadlines daily
    'check-action-deadlines': {
        'task': 'tasks.notification_tasks.check_action_plan_deadlines',
        'schedule': crontab(minute=0, hour=8),  # 8 AM daily
    },
    # Check campaign participation rates daily
    'check-participation-rates': {
        'task': 'tasks.notification_tasks.check_participation_rates',
        'schedule': crontab(minute=30, hour=9),  # 9:30 AM daily
    },
}

app.conf.timezone = 'America/Sao_Paulo'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
