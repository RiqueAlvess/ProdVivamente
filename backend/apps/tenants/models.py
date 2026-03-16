"""
Tenants app models - Empresa.
Isolamento de dados por empresa (grupo): cada usuário pertence a uma empresa
e só acessa os dados desta empresa. Não há mais multi-tenancy por schema.
"""
from django.db import models
from django.utils.text import slugify


class Empresa(models.Model):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    total_funcionarios = models.IntegerField(default=0)
    cnae = models.CharField(max_length=10, blank=True)
    cnae_descricao = models.CharField(max_length=255, blank=True)
    admin_email = models.EmailField(blank=True, verbose_name='E-mail do Admin RH')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            n = 1
            while Empresa.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
