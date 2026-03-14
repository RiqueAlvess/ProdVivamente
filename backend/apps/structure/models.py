"""
Structure app models - Unidade, Setor, Cargo.
"""
from django.db import models


class Unidade(models.Model):
    empresa = models.ForeignKey(
        'tenants.Empresa', on_delete=models.CASCADE, related_name='unidades'
    )
    nome = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        unique_together = ['empresa', 'nome']
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.empresa.nome})'


class Setor(models.Model):
    unidade = models.ForeignKey(
        Unidade, on_delete=models.CASCADE, related_name='setores'
    )
    nome = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        unique_together = ['unidade', 'nome']
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} - {self.unidade.nome}'

    @property
    def empresa(self):
        return self.unidade.empresa


class Cargo(models.Model):
    empresa = models.ForeignKey(
        'tenants.Empresa', on_delete=models.CASCADE, related_name='cargos'
    )
    nome = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        unique_together = ['empresa', 'nome']
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.empresa.nome})'
