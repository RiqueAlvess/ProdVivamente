"""
Management command to seed HSE-IT questions and dimensions.
Run: python manage.py seed_questions
"""
from django.core.management.base import BaseCommand

DIMENSOES_DATA = [
    {
        'codigo': 'demandas',
        'nome': 'Demandas',
        'tipo': 'negativo',
        'descricao': 'Carga de trabalho, ritmo e exigências do trabalho',
        'ordem': 1,
    },
    {
        'codigo': 'controle',
        'nome': 'Controle',
        'tipo': 'positivo',
        'descricao': 'Autonomia e participação nas decisões sobre o trabalho',
        'ordem': 2,
    },
    {
        'codigo': 'apoio_chefia',
        'nome': 'Apoio da Chefia',
        'tipo': 'positivo',
        'descricao': 'Suporte e feedback recebidos da liderança',
        'ordem': 3,
    },
    {
        'codigo': 'apoio_colegas',
        'nome': 'Apoio dos Colegas',
        'tipo': 'positivo',
        'descricao': 'Suporte e colaboração entre colegas de trabalho',
        'ordem': 4,
    },
    {
        'codigo': 'relacionamentos',
        'nome': 'Relacionamentos',
        'tipo': 'negativo',
        'descricao': 'Conflitos e tensões interpessoais no ambiente de trabalho',
        'ordem': 5,
    },
    {
        'codigo': 'cargo',
        'nome': 'Cargo/Função',
        'tipo': 'positivo',
        'descricao': 'Clareza sobre papéis, responsabilidades e expectativas',
        'ordem': 6,
    },
    {
        'codigo': 'comunicacao_mudancas',
        'nome': 'Comunicação e Mudanças',
        'tipo': 'positivo',
        'descricao': 'Clareza na comunicação e gestão de mudanças organizacionais',
        'ordem': 7,
    },
]

PERGUNTAS_DATA = [
    (1,  'cargo',                 'Eu sei exatamente o que é esperado de mim no trabalho'),
    (2,  'controle',              'Posso decidir quando fazer uma pausa'),
    (3,  'demandas',              'Diferentes grupos no trabalho exigem coisas de mim que são difíceis de combinar'),
    (4,  'cargo',                 'Eu sei como fazer meu trabalho'),
    (5,  'relacionamentos',       'Estou sujeito a atenção pessoal ou assédio na forma de palavras ou comportamentos ofensivos'),
    (6,  'demandas',              'Tenho prazos inatingíveis'),
    (7,  'apoio_colegas',         'Se o trabalho fica difícil, meus colegas me ajudam'),
    (8,  'apoio_chefia',          'Sou apoiado(a) em uma crise emocional no trabalho'),
    (9,  'demandas',              'Tenho que trabalhar muito intensamente'),
    (10, 'controle',              'Tenho voz nas mudanças no modo como faço meu trabalho'),
    (11, 'cargo',                 'Tenho tempo suficiente para completar meu trabalho'),
    (12, 'demandas',              'Tenho que desconsiderar regras ou procedimentos para fazer o trabalho'),
    (13, 'cargo',                 'Sei qual é o meu papel e responsabilidades'),
    (14, 'relacionamentos',       'Tenho que trabalhar com pessoas que têm valores de trabalho diferentes'),
    (15, 'controle',              'Posso planejar quando fazer as pausas'),
    (16, 'demandas',              'Tenho volume de trabalho pesado'),
    (17, 'cargo',                 'Existe uma boa combinação entre o que a organização espera de mim e as habilidades que tenho'),
    (18, 'demandas',              'Tenho que trabalhar muito rapidamente'),
    (19, 'controle',              'Tenho uma palavra a dizer sobre o ritmo em que trabalho'),
    (20, 'demandas',              'Tenho que negligenciar alguns aspectos do meu trabalho porque tenho muito a fazer'),
    (21, 'relacionamentos',       'Existe fricção ou raiva entre colegas'),
    (22, 'demandas',              'Não tenho tempo para fazer uma pausa'),
    (23, 'apoio_chefia',          'Minha chefia imediata me encoraja no trabalho'),
    (24, 'apoio_colegas',         'Recebo o respeito no trabalho que mereço de meus colegas'),
    (25, 'controle',              'Tenho controle sobre quando fazer uma pausa'),
    (26, 'comunicacao_mudancas',  'Os funcionários são sempre consultados sobre mudanças no trabalho'),
    (27, 'apoio_colegas',         'Posso contar com meus colegas para me ajudar quando as coisas ficam difíceis no trabalho'),
    (28, 'comunicacao_mudancas',  'Posso conversar com minha chefia sobre algo que me incomodou'),
    (29, 'apoio_chefia',          'Minha chefia me apoia para o trabalho'),
    (30, 'controle',              'Tenho alguma participação em decisões sobre o meu trabalho'),
    (31, 'apoio_colegas',         'Recebo ajuda e apoio de meus colegas'),
    (32, 'comunicacao_mudancas',  'Quando ocorrem mudanças no trabalho, tenho clareza sobre como funcionará na prática'),
    (33, 'apoio_chefia',          'Recebo feedback sobre o meu trabalho'),
    (34, 'relacionamentos',       'Existe tensão entre mim e colegas de trabalho'),
    (35, 'apoio_chefia',          'Minha chefia me incentiva nas minhas atividades'),
]


class Command(BaseCommand):
    help = 'Seeds all 35 HSE-IT questions and 7 dimensions into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing questions and dimensions before seeding',
        )

    def handle(self, *args, **options):
        from apps.surveys.models import Dimensao, Pergunta

        if options['reset']:
            self.stdout.write('Deleting existing questions and dimensions...')
            Pergunta.objects.all().delete()
            Dimensao.objects.all().delete()

        self.stdout.write('Seeding dimensions...')
        dimensao_map = {}
        for d in DIMENSOES_DATA:
            dimensao, created = Dimensao.objects.update_or_create(
                codigo=d['codigo'],
                defaults={
                    'nome': d['nome'],
                    'tipo': d['tipo'],
                    'descricao': d['descricao'],
                    'ordem': d['ordem'],
                }
            )
            dimensao_map[d['codigo']] = dimensao
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {dimensao.nome}')

        self.stdout.write(f'\nSeeding {len(PERGUNTAS_DATA)} questions...')
        created_count = 0
        updated_count = 0

        for numero, dimensao_codigo, texto in PERGUNTAS_DATA:
            dimensao = dimensao_map[dimensao_codigo]
            _, created = Pergunta.objects.update_or_create(
                numero=numero,
                defaults={
                    'dimensao': dimensao,
                    'texto': texto,
                    'ativo': True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(f'  P{numero:02d} [{dimensao_codigo}]: {texto[:60]}...')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {len(DIMENSOES_DATA)} dimensions, '
            f'{created_count} questions created, {updated_count} updated.'
        ))
