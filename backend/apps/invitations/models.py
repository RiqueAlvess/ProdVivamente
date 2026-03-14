"""
Invitations app models - SurveyInvitation with encrypted PII.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class SurveyInvitation(models.Model):
    STATUS = [
        ('pending', 'Pendente'),
        ('sent', 'Enviado'),
        ('used', 'Utilizado'),
        ('expired', 'Expirado'),
    ]

    hash_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    email_encrypted = models.TextField()   # AES-256-GCM encrypted
    nome_encrypted = models.TextField()    # AES-256-GCM encrypted
    empresa = models.ForeignKey('tenants.Empresa', on_delete=models.CASCADE, related_name='invitations')
    campaign = models.ForeignKey(
        'surveys.Campaign', on_delete=models.CASCADE, related_name='invitations'
    )
    unidade = models.ForeignKey('structure.Unidade', on_delete=models.CASCADE)
    setor = models.ForeignKey('structure.Setor', on_delete=models.CASCADE)
    cargo = models.ForeignKey(
        'structure.Cargo', on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    expires_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Convite de Pesquisa'
        verbose_name_plural = 'Convites de Pesquisa'
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['hash_token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'Convite {self.hash_token} - {self.status}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.status in ('pending', 'sent') and not self.is_expired

    def mark_as_used(self):
        self.status = 'used'
        self.used_at = timezone.now()
        self.save(update_fields=['status', 'used_at'])

    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    @property
    def survey_url(self):
        """URL for the respondent to access the survey."""
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f'{frontend_url}/pesquisa/{self.hash_token}'
