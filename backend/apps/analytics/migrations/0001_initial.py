from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('structure', '0001_initial'),
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DimTempo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(unique=True)),
                ('ano', models.IntegerField()),
                ('mes', models.IntegerField()),
                ('trimestre', models.IntegerField()),
                ('semana', models.IntegerField()),
                ('dia_semana', models.IntegerField()),
                ('nome_mes', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name': 'Dimensão Tempo',
                'ordering': ['data'],
            },
        ),
        migrations.CreateModel(
            name='DimEstrutura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unidade_nome', models.CharField(max_length=255)),
                ('setor_nome', models.CharField(max_length=255)),
                ('unidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structure.unidade')),
                ('setor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structure.setor')),
            ],
            options={
                'verbose_name': 'Dimensão Estrutura',
                'unique_together': {('unidade', 'setor')},
            },
        ),
        migrations.CreateModel(
            name='DimDemografia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faixa_etaria', models.CharField(blank=True, max_length=50)),
                ('tempo_empresa', models.CharField(blank=True, max_length=50)),
                ('genero', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'verbose_name': 'Dimensão Demografia',
                'unique_together': {('faixa_etaria', 'tempo_empresa', 'genero')},
            },
        ),
        migrations.CreateModel(
            name='DimDimensaoHSE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=50, unique=True)),
                ('nome', models.CharField(max_length=255)),
                ('tipo', models.CharField(max_length=10)),
            ],
            options={
                'verbose_name': 'Dimensão HSE',
            },
        ),
        migrations.CreateModel(
            name='FactScoreDimensao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score_medio', models.FloatField()),
                ('nivel_risco', models.CharField(max_length=20)),
                ('total_respostas', models.IntegerField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='surveys.campaign')),
                ('dim_estrutura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analytics.dimestrutura')),
                ('dim_dimensao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analytics.dimdimensaohse')),
                ('dim_tempo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='analytics.dimtempo')),
            ],
            options={
                'verbose_name': 'Fato Score Dimensão',
                'unique_together': {('campaign', 'dim_estrutura', 'dim_dimensao')},
                'indexes': [
                    models.Index(fields=['campaign', 'nivel_risco'], name='analytics_factscore_campaign_nr_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='FactIndicadorCampanha',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_convidados', models.IntegerField(default=0)),
                ('total_respondidos', models.IntegerField(default=0)),
                ('taxa_adesao', models.FloatField(default=0.0)),
                ('igrp', models.FloatField(blank=True, null=True)),
                ('score_geral', models.FloatField(blank=True, null=True)),
                ('nivel_risco_geral', models.CharField(blank=True, max_length=20)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='surveys.campaign', unique=True)),
            ],
            options={
                'verbose_name': 'Fato Indicador Campanha',
            },
        ),
        migrations.CreateModel(
            name='FactRespostaPergunta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pergunta_numero', models.IntegerField()),
                ('valor_0', models.IntegerField(default=0)),
                ('valor_1', models.IntegerField(default=0)),
                ('valor_2', models.IntegerField(default=0)),
                ('valor_3', models.IntegerField(default=0)),
                ('valor_4', models.IntegerField(default=0)),
                ('total', models.IntegerField(default=0)),
                ('media', models.FloatField(default=0.0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='surveys.campaign')),
                ('dim_estrutura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analytics.dimestrutura')),
            ],
            options={
                'verbose_name': 'Fato Resposta Pergunta',
                'unique_together': {('campaign', 'dim_estrutura', 'pergunta_numero')},
            },
        ),
        migrations.CreateModel(
            name='SectorAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('processing', 'Processando'), ('completed', 'Concluído'), ('failed', 'Falhou')], default='processing', max_length=20)),
                ('pontos_criticos', models.JSONField(blank=True, null=True)),
                ('recomendacoes', models.JSONField(blank=True, null=True)),
                ('analise_completa', models.TextField(blank=True)),
                ('modelo_ia', models.CharField(blank=True, max_length=100)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='surveys.campaign')),
                ('setor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structure.setor')),
            ],
            options={
                'verbose_name': 'Análise de Setor',
                'verbose_name_plural': 'Análises de Setores',
                'ordering': ['-created_at'],
            },
        ),
    ]
