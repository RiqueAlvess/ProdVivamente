"""
Accounts app models - UserProfile and AuditLog.
NO registration endpoint - only admin creates users via Django admin.
With django-tenants, UserProfile is schema-isolated per tenant.
"""
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ROLES = [
        ('rh', 'RH'),
        ('lideranca', 'Liderança'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLES, default='rh')
    # No empresa FK — isolation is done by PostgreSQL schema (django-tenants)
    unidades_permitidas = models.ManyToManyField('structure.Unidade', blank=True)
    setores_permitidos = models.ManyToManyField('structure.Setor', blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


class AuditLog(models.Model):
    ACOES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('import_csv', 'Importação CSV'),
        ('disparo_email', 'Disparo de E-mails'),
        ('export_relatorio', 'Exportação de Relatório'),
        ('create_campaign', 'Criação de Campanha'),
        ('view_dashboard', 'Visualização de Dashboard'),
        ('update_action', 'Atualização de Plano de Ação'),
        ('upload_evidence', 'Upload de Evidência'),
        ('delete_evidence', 'Remoção de Evidência'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # No empresa FK — audit is per-schema (tenant-scoped)
    acao = models.CharField(max_length=50, choices=ACOES)
    descricao = models.TextField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['acao', 'created_at']),
        ]

    def __str__(self):
        return f'{self.user} - {self.acao} - {self.created_at:%Y-%m-%d %H:%M}'
