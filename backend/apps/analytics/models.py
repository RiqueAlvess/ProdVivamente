"""
Analytics app models - Star schema for dashboard queries.
"""
from django.db import models


# ---------------------------------------------------------------------------
# Dimension tables (star schema)
# ---------------------------------------------------------------------------

class DimTempo(models.Model):
    """Time dimension."""
    data = models.DateField(unique=True)
    ano = models.IntegerField()
    mes = models.IntegerField()
    trimestre = models.IntegerField()
    semana = models.IntegerField()
    dia_semana = models.IntegerField()  # 0=Monday
    nome_mes = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Dimensão Tempo'
        ordering = ['data']

    def __str__(self):
        return str(self.data)


class DimEstrutura(models.Model):
    """Organizational structure dimension."""
    unidade = models.ForeignKey('structure.Unidade', on_delete=models.CASCADE)
    setor = models.ForeignKey('structure.Setor', on_delete=models.CASCADE)
    unidade_nome = models.CharField(max_length=255)
    setor_nome = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Dimensão Estrutura'
        unique_together = ['unidade', 'setor']

    def __str__(self):
        return f'{self.unidade_nome} > {self.setor_nome}'


class DimDemografia(models.Model):
    """Demographics dimension."""
    faixa_etaria = models.CharField(max_length=50, blank=True)
    tempo_empresa = models.CharField(max_length=50, blank=True)
    genero = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Dimensão Demografia'
        unique_together = ['faixa_etaria', 'tempo_empresa', 'genero']

    def __str__(self):
        return f'{self.faixa_etaria} / {self.genero}'


class DimDimensaoHSE(models.Model):
    """HSE-IT dimension."""
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Dimensão HSE'

    def __str__(self):
        return self.nome


# ---------------------------------------------------------------------------
# Fact tables (star schema)
# ---------------------------------------------------------------------------

class FactScoreDimensao(models.Model):
    """Fact: average score per dimension per sector per campaign."""
    campaign = models.ForeignKey('surveys.Campaign', on_delete=models.CASCADE)
    dim_estrutura = models.ForeignKey(DimEstrutura, on_delete=models.CASCADE)
    dim_dimensao = models.ForeignKey(DimDimensaoHSE, on_delete=models.CASCADE)
    dim_tempo = models.ForeignKey(DimTempo, null=True, blank=True, on_delete=models.SET_NULL)
    score_medio = models.FloatField()
    nivel_risco = models.CharField(max_length=20)
    total_respostas = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fato Score Dimensão'
        unique_together = ['campaign', 'dim_estrutura', 'dim_dimensao']
        indexes = [
            models.Index(fields=['campaign', 'nivel_risco']),
        ]


class FactIndicadorCampanha(models.Model):
    """Fact: campaign-level KPIs."""
    campaign = models.OneToOneField('surveys.Campaign', on_delete=models.CASCADE)
    total_convidados = models.IntegerField(default=0)
    total_respondidos = models.IntegerField(default=0)
    taxa_adesao = models.FloatField(default=0.0)
    igrp = models.FloatField(null=True, blank=True)
    score_geral = models.FloatField(null=True, blank=True)
    nivel_risco_geral = models.CharField(max_length=20, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fato Indicador Campanha'


class FactRespostaPergunta(models.Model):
    """Fact: aggregated answer distribution per question."""
    campaign = models.ForeignKey('surveys.Campaign', on_delete=models.CASCADE)
    dim_estrutura = models.ForeignKey(DimEstrutura, on_delete=models.CASCADE)
    pergunta_numero = models.IntegerField()
    valor_0 = models.IntegerField(default=0)  # Never
    valor_1 = models.IntegerField(default=0)  # Rarely
    valor_2 = models.IntegerField(default=0)  # Sometimes
    valor_3 = models.IntegerField(default=0)  # Often
    valor_4 = models.IntegerField(default=0)  # Always
    total = models.IntegerField(default=0)
    media = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fato Resposta Pergunta'
        unique_together = ['campaign', 'dim_estrutura', 'pergunta_numero']


class SectorAnalysis(models.Model):
    """AI-generated sector analysis."""
    STATUS_CHOICES = [
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    campaign = models.ForeignKey('surveys.Campaign', on_delete=models.CASCADE)
    setor = models.ForeignKey('structure.Setor', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    pontos_criticos = models.JSONField(null=True, blank=True)
    recomendacoes = models.JSONField(null=True, blank=True)
    analise_completa = models.TextField(blank=True)
    modelo_ia = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Análise de Setor'
        verbose_name_plural = 'Análises de Setores'
        ordering = ['-created_at']

    def __str__(self):
        return f'Análise {self.setor.nome} - {self.campaign.nome}'
