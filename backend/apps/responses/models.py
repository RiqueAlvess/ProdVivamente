"""
Responses app models - SurveyResponse.
CRITICAL: NO FK to SurveyInvitation, User or Cargo - BLIND DROP architecture.
"""
from django.db import models


class SurveyResponse(models.Model):
    # NO FK to SurveyInvitation - BLIND DROP
    # NO cargo field
    # NO user field
    campaign = models.ForeignKey(
        'surveys.Campaign', on_delete=models.CASCADE, related_name='respostas'
    )
    unidade = models.ForeignKey('structure.Unidade', on_delete=models.CASCADE)
    setor = models.ForeignKey('structure.Setor', on_delete=models.CASCADE)

    # Demographic fields (voluntary, cannot be linked to invitation/user)
    faixa_etaria = models.CharField(max_length=50, blank=True)
    tempo_empresa = models.CharField(max_length=50, blank=True)
    genero = models.CharField(max_length=50, blank=True)

    # Answers: {str(pergunta_numero): int(value 0-4)}
    respostas = models.JSONField(default=dict)

    # Free text comment with sentiment analysis
    comentario_livre = models.TextField(blank=True)
    sentimento_score = models.FloatField(null=True, blank=True)
    sentimento_categorias = models.JSONField(null=True, blank=True)

    # LGPD consent
    lgpd_aceito = models.BooleanField(default=True)
    lgpd_aceito_em = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Resposta de Pesquisa'
        verbose_name_plural = 'Respostas de Pesquisa'
        indexes = [
            models.Index(fields=['campaign', 'created_at']),
            models.Index(fields=['campaign', 'unidade']),
            models.Index(fields=['campaign', 'setor']),
        ]

    def __str__(self):
        return f'Resposta #{self.id} - {self.campaign.nome}'
