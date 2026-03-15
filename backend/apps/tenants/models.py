"""
Tenants app models - Empresa (TenantMixin) and Domain (DomainMixin).
Uses django-tenants for PostgreSQL schema-per-tenant isolation.
"""
from django.db import models
from django.utils.text import slugify
from django_tenants.models import TenantMixin, DomainMixin


class Empresa(TenantMixin):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    total_funcionarios = models.IntegerField(default=0)
    cnae = models.CharField(max_length=10, blank=True)
    cnae_descricao = models.CharField(max_length=255, blank=True)
    logo_url = models.URLField(blank=True)
    favicon_url = models.URLField(blank=True)
    cor_primaria = models.CharField(max_length=7, default='#0EA5E9')
    cor_secundaria = models.CharField(max_length=7, default='#8B5CF6')
    cor_fonte = models.CharField(max_length=7, default='#1E293B')
    nome_app = models.CharField(max_length=100, default='VIVAMENTE 360º')
    admin_email = models.EmailField(blank=True, verbose_name='E-mail do Admin RH')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TenantMixin: automatically creates the PostgreSQL schema on save
    auto_create_schema = True

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


class Domain(DomainMixin):
    """
    Maps a domain/subdomain to an Empresa (tenant).
    Example: empresa1.vivamente.com.br → Empresa(slug='empresa1')
    DomainMixin provides: domain (CharField), tenant (FK → Empresa), is_primary (BooleanField).
    """

    class Meta:
        verbose_name = 'Domínio'
        verbose_name_plural = 'Domínios'
