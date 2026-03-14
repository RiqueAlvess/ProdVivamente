"""
Core app models - TaskQueue, UserNotification.
"""
from django.contrib.auth.models import User
from django.db import models


class TaskQueue(models.Model):
    STATUSES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    task_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    error_message = models.TextField(blank=True)

    # Output file (stored in Supabase)
    file_path = models.CharField(max_length=500, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_url = models.URLField(blank=True)

    # Progress tracking
    progress = models.IntegerField(default=0)
    progress_message = models.CharField(max_length=255, blank=True)

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks'
    )
    empresa = models.ForeignKey(
        'tenants.Empresa', on_delete=models.SET_NULL, null=True, blank=True
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fila de Tarefas'
        verbose_name_plural = 'Fila de Tarefas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.task_type} [{self.status}] #{self.id}'


class UserNotification(models.Model):
    TYPES = [
        ('task_completed', 'Tarefa Concluída'),
        ('task_failed', 'Tarefa Falhou'),
        ('file_ready', 'Arquivo Pronto'),
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    task = models.ForeignKey(
        TaskQueue, on_delete=models.SET_NULL, null=True, blank=True
    )
    notification_type = models.CharField(max_length=30, choices=TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link_url = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'task', 'notification_type'],
                condition=models.Q(task__isnull=False),
                name='unique_user_task_notification',
            )
        ]

    def __str__(self):
        return f'{self.user.username}: {self.title}'
