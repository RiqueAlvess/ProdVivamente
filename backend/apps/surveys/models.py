"""
Surveys app models - Dimensao, Pergunta, Campaign, FatorRisco, etc.
"""
from django.db import models
from django.utils import timezone


class Dimensao(models.Model):
    TIPOS = [
        ('positivo', 'Positivo'),
        ('negativo', 'Negativo'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    descricao = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Dimensão'
        verbose_name_plural = 'Dimensões'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class Pergunta(models.Model):
    numero = models.IntegerField(unique=True)
    dimensao = models.ForeignKey(Dimensao, on_delete=models.CASCADE, related_name='perguntas')
    texto = models.TextField()
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Pergunta'
        verbose_name_plural = 'Perguntas'
        ordering = ['numero']

    def __str__(self):
        return f'P{self.numero}: {self.texto[:60]}...'


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('active', 'Ativo'),
        ('closed', 'Encerrado'),
    ]

    empresa = models.ForeignKey(
        'tenants.Empresa', on_delete=models.CASCADE, related_name='campaigns'
    )
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    meta_adesao = models.IntegerField(default=70, help_text='Meta de adesão em %')
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns_criadas'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'
        ordering = ['-created_at']

    def __str__(self):
        return self.nome

    def encerrar(self):
        """
        Close campaign and expire all pending/sent invitations.
        """
        from apps.invitations.models import SurveyInvitation
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])

        # Expire pending and sent invitations
        SurveyInvitation.objects.filter(
            campaign=self,
            status__in=['pending', 'sent'],
        ).update(status='expired')

    def activate(self):
        """Activate campaign."""
        self.status = 'active'
        self.save(update_fields=['status', 'updated_at'])

    @property
    def total_respostas(self):
        return self.respostas.count()

    @property
    def taxa_adesao(self):
        total_inv = self.invitations.count()
        if total_inv == 0:
            return 0.0
        return round(self.total_respostas / total_inv * 100, 1)


class CategoriaFatorRisco(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    descricao = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Categoria de Fator de Risco'
        verbose_name_plural = 'Categorias de Fatores de Risco'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class FatorRisco(models.Model):
    NIVEIS = [
        ('baixo', 'Baixo'),
        ('moderado', 'Moderado'),
        ('alto', 'Alto'),
        ('critico', 'Crítico'),
    ]

    categoria = models.ForeignKey(
        CategoriaFatorRisco, on_delete=models.CASCADE, related_name='fatores'
    )
    dimensao = models.ForeignKey(
        Dimensao, on_delete=models.SET_NULL, null=True, blank=True, related_name='fatores_risco'
    )
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    probabilidade_base = models.IntegerField(
        default=1, help_text='1=Improvável, 2=Possível, 3=Provável, 4=Frequente'
    )
    severidade_base = models.IntegerField(
        default=1, help_text='1=Insignificante, 2=Leve, 3=Moderada, 4=Grave, 5=Catastrófica'
    )
    acoes_preventivas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Fator de Risco'
        verbose_name_plural = 'Fatores de Risco'
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f'{self.nome} ({self.categoria.nome})'

    @property
    def nivel_risco_base(self):
        nr = self.probabilidade_base * self.severidade_base
        if nr <= 4:
            return 'baixo'
        elif nr <= 9:
            return 'moderado'
        elif nr <= 15:
            return 'alto'
        return 'critico'


class SeveridadePorCNAE(models.Model):
    """CNAE-specific severity adjustments for risk factors."""
    fator_risco = models.ForeignKey(FatorRisco, on_delete=models.CASCADE, related_name='severidades_cnae')
    cnae_prefixo = models.CharField(max_length=10, help_text='CNAE prefix (e.g. "47" for retail)')
    severidade_ajustada = models.IntegerField(
        default=1, help_text='Adjusted severity for this CNAE category'
    )
    justificativa = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Severidade por CNAE'
        verbose_name_plural = 'Severidades por CNAE'
        unique_together = ['fator_risco', 'cnae_prefixo']

    def __str__(self):
        return f'{self.fator_risco.nome} - CNAE {self.cnae_prefixo}'
