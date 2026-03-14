"""
Structure app models - Unidade, Setor, Cargo.
With django-tenants, each empresa has its own schema — no empresa FK needed.
"""
from django.db import models


class Unidade(models.Model):
    # No empresa FK — schema isolation handles tenant separation
    nome = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        unique_together = ['nome']
        ordering = ['nome']

    def __str__(self):
        return self.nome


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


class Cargo(models.Model):
    # No empresa FK — schema isolation handles tenant separation
    nome = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        unique_together = ['nome']
        ordering = ['nome']

    def __str__(self):
        return self.nome
