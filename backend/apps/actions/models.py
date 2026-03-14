"""
Actions app models - PlanoAcao, ChecklistNR1, EvidenciaNR1.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class PlanoAcao(models.Model):
    STATUS = [
        ('pendente', 'Pendente'),
        ('andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    empresa = models.ForeignKey('tenants.Empresa', on_delete=models.CASCADE, related_name='planos_acao')
    campaign = models.ForeignKey(
        'surveys.Campaign', on_delete=models.CASCADE, null=True, blank=True, related_name='planos_acao'
    )
    dimensao = models.ForeignKey(
        'surveys.Dimensao', on_delete=models.SET_NULL, null=True, blank=True
    )
    nivel_risco = models.CharField(max_length=50, blank=True)
    descricao_risco = models.TextField(blank=True)
    acao_proposta = models.TextField()
    responsavel = models.CharField(max_length=255, blank=True)
    prazo = models.DateField(null=True, blank=True)
    recursos_necessarios = models.TextField(blank=True)
    indicadores = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pendente')

    # Rich text content (TipTap compatible)
    conteudo_estruturado = models.JSONField(null=True, blank=True)
    conteudo_html = models.TextField(blank=True)

    # AI generated flag
    gerado_por_ia = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='planos_criados'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano de Ação'
        verbose_name_plural = 'Planos de Ação'
        ordering = ['-created_at']

    def __str__(self):
        return f'Plano #{self.id} - {self.empresa.nome}'


class ChecklistNR1Etapa(models.Model):
    """NR-1 compliance checklist stage."""
    campaign = models.ForeignKey(
        'surveys.Campaign', on_delete=models.CASCADE, related_name='checklist_etapas'
    )
    empresa = models.ForeignKey('tenants.Empresa', on_delete=models.CASCADE)
    numero_etapa = models.IntegerField()
    nome = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Etapa do Checklist NR-1'
        verbose_name_plural = 'Etapas do Checklist NR-1'
        unique_together = ['campaign', 'numero_etapa']
        ordering = ['numero_etapa']

    def __str__(self):
        return f'Etapa {self.numero_etapa}: {self.nome}'

    @property
    def percentual_conclusao(self):
        total = self.itens.count()
        if total == 0:
            return 0
        concluidos = self.itens.filter(concluido=True).count()
        return round(concluidos / total * 100, 1)


class ChecklistNR1Item(models.Model):
    """Individual item in a checklist stage."""
    etapa = models.ForeignKey(ChecklistNR1Etapa, on_delete=models.CASCADE, related_name='itens')
    descricao = models.TextField()
    automatico = models.BooleanField(
        default=False, help_text='Automatically marked complete by system'
    )
    concluido = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    responsavel = models.CharField(max_length=255, blank=True)
    prazo = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Item do Checklist NR-1'
        verbose_name_plural = 'Itens do Checklist NR-1'
        ordering = ['ordem']

    def __str__(self):
        return f'{self.etapa} - {self.descricao[:60]}'

    def marcar_concluido(self, responsavel=''):
        self.concluido = True
        self.data_conclusao = timezone.now()
        if responsavel:
            self.responsavel = responsavel
        self.save(update_fields=['concluido', 'data_conclusao', 'responsavel'])


class EvidenciaNR1(models.Model):
    """Evidence file uploaded for an NR-1 checklist item."""
    TIPOS = [
        ('documento', 'Documento'),
        ('imagem', 'Imagem'),
        ('planilha', 'Planilha'),
        ('apresentacao', 'Apresentação'),
        ('email', 'E-mail'),
        ('ata', 'Ata'),
        ('certificado', 'Certificado'),
        ('outro', 'Outro'),
    ]

    checklist_item = models.ForeignKey(
        ChecklistNR1Item, on_delete=models.CASCADE, related_name='evidencias'
    )
    empresa = models.ForeignKey('tenants.Empresa', on_delete=models.CASCADE)
    nome_original = models.CharField(max_length=255)
    storage_path = models.CharField(max_length=500)     # Supabase Storage path
    storage_url = models.URLField(blank=True)            # Public URL from Supabase
    tipo = models.CharField(max_length=20, choices=TIPOS, default='documento')
    tamanho_bytes = models.BigIntegerField()
    descricao = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidência NR-1'
        verbose_name_plural = 'Evidências NR-1'
        ordering = ['-created_at']

    def __str__(self):
        return self.nome_original
