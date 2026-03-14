"""
Management command to seed psychosocial risk factors per NR-1.
Run: python manage.py seed_risk_factors
"""
from django.core.management.base import BaseCommand

CATEGORIAS_DATA = [
    {'nome': 'Organização do Trabalho', 'descricao': 'Fatores relacionados à estrutura e organização do trabalho', 'ordem': 1},
    {'nome': 'Conteúdo do Trabalho', 'descricao': 'Fatores relacionados às tarefas e demandas do trabalho', 'ordem': 2},
    {'nome': 'Relações Interpessoais', 'descricao': 'Fatores relacionados às interações no ambiente de trabalho', 'ordem': 3},
    {'nome': 'Ambiente Físico', 'descricao': 'Fatores do ambiente físico que afetam o bem-estar psicossocial', 'ordem': 4},
    {'nome': 'Gestão e Liderança', 'descricao': 'Fatores relacionados à qualidade da gestão e liderança', 'ordem': 5},
    {'nome': 'Comunicação Organizacional', 'descricao': 'Fatores relacionados à comunicação interna', 'ordem': 6},
]

FATORES_DATA = [
    # Organização do Trabalho
    {
        'categoria': 'Organização do Trabalho',
        'dimensao': 'demandas',
        'nome': 'Excesso de Carga de Trabalho',
        'descricao': 'Volume excessivo de tarefas e responsabilidades além da capacidade',
        'probabilidade_base': 3,
        'severidade_base': 4,
        'acoes_preventivas': 'Redistribuição de tarefas, contratação de pessoal, priorização de atividades',
    },
    {
        'categoria': 'Organização do Trabalho',
        'dimensao': 'demandas',
        'nome': 'Prazos Irrealistas',
        'descricao': 'Metas e prazos incompatíveis com o tempo e recursos disponíveis',
        'probabilidade_base': 3,
        'severidade_base': 3,
        'acoes_preventivas': 'Revisão de cronogramas, negociação de prazos, planejamento adequado',
    },
    {
        'categoria': 'Organização do Trabalho',
        'dimensao': 'controle',
        'nome': 'Falta de Autonomia',
        'descricao': 'Pouca ou nenhuma participação nas decisões que afetam o trabalho',
        'probabilidade_base': 2,
        'severidade_base': 3,
        'acoes_preventivas': 'Delegação de responsabilidades, consulta aos colaboradores nas decisões',
    },
    # Conteúdo do Trabalho
    {
        'categoria': 'Conteúdo do Trabalho',
        'dimensao': 'cargo',
        'nome': 'Ambiguidade de Papel',
        'descricao': 'Falta de clareza sobre funções, responsabilidades e expectativas',
        'probabilidade_base': 2,
        'severidade_base': 3,
        'acoes_preventivas': 'Descrição de cargos clara, reuniões de alinhamento, feedback regular',
    },
    {
        'categoria': 'Conteúdo do Trabalho',
        'dimensao': 'cargo',
        'nome': 'Conflito de Papel',
        'descricao': 'Demandas incompatíveis de diferentes partes do trabalho',
        'probabilidade_base': 2,
        'severidade_base': 3,
        'acoes_preventivas': 'Definição clara de prioridades, alinhamento com liderança',
    },
    # Relações Interpessoais
    {
        'categoria': 'Relações Interpessoais',
        'dimensao': 'relacionamentos',
        'nome': 'Assédio Moral',
        'descricao': 'Comportamentos ofensivos, humilhantes ou intimidadores repetidos',
        'probabilidade_base': 2,
        'severidade_base': 5,
        'acoes_preventivas': 'Política de tolerância zero, canal de denúncia, treinamento de líderes',
    },
    {
        'categoria': 'Relações Interpessoais',
        'dimensao': 'relacionamentos',
        'nome': 'Conflitos Interpessoais',
        'descricao': 'Tensões e conflitos frequentes entre colegas ou com liderança',
        'probabilidade_base': 2,
        'severidade_base': 3,
        'acoes_preventivas': 'Mediação de conflitos, treinamento em comunicação não-violenta',
    },
    {
        'categoria': 'Relações Interpessoais',
        'dimensao': 'apoio_colegas',
        'nome': 'Falta de Suporte Social',
        'descricao': 'Ausência de apoio e cooperação entre colegas de equipe',
        'probabilidade_base': 2,
        'severidade_base': 2,
        'acoes_preventivas': 'Atividades de integração, cultura de colaboração, trabalho em equipe',
    },
    # Gestão e Liderança
    {
        'categoria': 'Gestão e Liderança',
        'dimensao': 'apoio_chefia',
        'nome': 'Liderança Inadequada',
        'descricao': 'Falta de suporte, feedback e encorajamento da liderança',
        'probabilidade_base': 2,
        'severidade_base': 4,
        'acoes_preventivas': 'Desenvolvimento de lideranças, coaching, feedback 360°',
    },
    {
        'categoria': 'Gestão e Liderança',
        'dimensao': 'apoio_chefia',
        'nome': 'Ausência de Reconhecimento',
        'descricao': 'Falta de valorização e reconhecimento pelos resultados alcançados',
        'probabilidade_base': 3,
        'severidade_base': 3,
        'acoes_preventivas': 'Programas de reconhecimento, feedback positivo, benefícios',
    },
    # Comunicação Organizacional
    {
        'categoria': 'Comunicação Organizacional',
        'dimensao': 'comunicacao_mudancas',
        'nome': 'Comunicação Ineficaz',
        'descricao': 'Informações insuficientes ou confusas sobre mudanças e decisões organizacionais',
        'probabilidade_base': 3,
        'severidade_base': 2,
        'acoes_preventivas': 'Comunicados regulares, reuniões de equipe, canais de comunicação claros',
    },
    {
        'categoria': 'Comunicação Organizacional',
        'dimensao': 'comunicacao_mudancas',
        'nome': 'Gestão de Mudanças Inadequada',
        'descricao': 'Mudanças organizacionais implementadas sem consulta ou comunicação adequada',
        'probabilidade_base': 2,
        'severidade_base': 3,
        'acoes_preventivas': 'Gestão participativa de mudanças, comunicação prévia, suporte na transição',
    },
]


class Command(BaseCommand):
    help = 'Seeds psychosocial risk factors per NR-1 methodology'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing risk factors before seeding',
        )

    def handle(self, *args, **options):
        from apps.surveys.models import CategoriaFatorRisco, FatorRisco, Dimensao

        if options['reset']:
            self.stdout.write('Deleting existing risk factors...')
            FatorRisco.objects.all().delete()
            CategoriaFatorRisco.objects.all().delete()

        self.stdout.write('Seeding risk factor categories...')
        categoria_map = {}
        for cat in CATEGORIAS_DATA:
            obj, created = CategoriaFatorRisco.objects.update_or_create(
                nome=cat['nome'],
                defaults={
                    'descricao': cat['descricao'],
                    'ordem': cat['ordem'],
                }
            )
            categoria_map[cat['nome']] = obj
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {obj.nome}')

        self.stdout.write(f'\nSeeding {len(FATORES_DATA)} risk factors...')
        created_count = 0
        updated_count = 0

        for fator_data in FATORES_DATA:
            categoria = categoria_map[fator_data['categoria']]
            dimensao = None
            if fator_data.get('dimensao'):
                try:
                    dimensao = Dimensao.objects.get(codigo=fator_data['dimensao'])
                except Dimensao.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  Dimensão não encontrada: {fator_data["dimensao"]}')
                    )

            _, created = FatorRisco.objects.update_or_create(
                categoria=categoria,
                nome=fator_data['nome'],
                defaults={
                    'dimensao': dimensao,
                    'descricao': fator_data['descricao'],
                    'probabilidade_base': fator_data['probabilidade_base'],
                    'severidade_base': fator_data['severidade_base'],
                    'acoes_preventivas': fator_data['acoes_preventivas'],
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(f'  {"Created" if created else "Updated"}: {fator_data["nome"]}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {len(CATEGORIAS_DATA)} categories, '
            f'{created_count} factors created, {updated_count} updated.'
        ))
