import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('surveys', '0001_initial'),
        ('structure', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faixa_etaria', models.CharField(blank=True, max_length=50)),
                ('tempo_empresa', models.CharField(blank=True, max_length=50)),
                ('genero', models.CharField(blank=True, max_length=50)),
                ('respostas', models.JSONField(default=dict)),
                ('comentario_livre', models.TextField(blank=True)),
                ('sentimento_score', models.FloatField(blank=True, null=True)),
                ('sentimento_categorias', models.JSONField(blank=True, null=True)),
                ('lgpd_aceito', models.BooleanField(default=True)),
                ('lgpd_aceito_em', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respostas', to='surveys.campaign')),
                ('setor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structure.setor')),
                ('unidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structure.unidade')),
            ],
            options={
                'verbose_name': 'Resposta de Pesquisa',
                'verbose_name_plural': 'Respostas de Pesquisa',
            },
        ),
        migrations.AddIndex(
            model_name='surveyresponse',
            index=models.Index(fields=['campaign', 'created_at'], name='responses_campaign_created_idx'),
        ),
        migrations.AddIndex(
            model_name='surveyresponse',
            index=models.Index(fields=['campaign', 'unidade'], name='responses_campaign_unidade_idx'),
        ),
        migrations.AddIndex(
            model_name='surveyresponse',
            index=models.Index(fields=['campaign', 'setor'], name='responses_campaign_setor_idx'),
        ),
    ]
