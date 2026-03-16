"""
Comando legado - não é mais necessário sem o sistema de tenant.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Comando legado (sistema de tenant removido). Não faz nada.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'O sistema de tenant foi removido. Este comando não é mais necessário.'
        ))
