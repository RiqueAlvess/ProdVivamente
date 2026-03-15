"""
Management command to initialize the public tenant (required for django-tenants routing).
Run once after first migration: python manage.py init_public_tenant
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create the public tenant and localhost domain if they do not exist.'

    def handle(self, *args, **options):
        from apps.tenants.models import Empresa, Domain

        pub, created = Empresa.objects.get_or_create(
            schema_name='public',
            defaults={'nome': 'Public', 'slug': 'public'},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Public tenant created.'))
        else:
            self.stdout.write('Public tenant already exists.')

        for hostname in ['localhost', '127.0.0.1']:
            domain, created = Domain.objects.get_or_create(
                domain=hostname,
                defaults={'tenant': pub, 'is_primary': True},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Domain {hostname} created.'))
            else:
                self.stdout.write(f'Domain {hostname} already exists.')
