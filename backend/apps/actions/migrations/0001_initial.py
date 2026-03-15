from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenants', '0001_initial'),
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanoAcao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivel_risco', models.CharField(blank=True, max_length=50)),
                ('descricao_risco', models.TextField(blank=True)),
                ('acao_proposta', models.TextField()),
                ('responsavel', models.CharField(blank=True, max_length=255)),
                ('prazo', models.DateField(blank=True, null=True)),
                ('recursos_necessarios', models.TextField(blank=True)),
                ('indicadores', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('andamento', 'Em Andamento'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado')], default='pendente', max_length=20)),
                ('conteudo_estruturado', models.JSONField(blank=True, null=True)),
                ('conteudo_html', models.TextField(blank=True)),
                ('gerado_por_ia', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planos_acao', to='tenants.empresa')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='planos_acao', to='surveys.campaign')),
                ('dimensao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='surveys.dimensao')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planos_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Plano de Ação',
                'verbose_name_plural': 'Planos de Ação',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChecklistNR1Etapa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_etapa', models.IntegerField()),
                ('nome', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_etapas', to='surveys.campaign')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tenants.empresa')),
            ],
            options={
                'verbose_name': 'Etapa do Checklist NR-1',
                'verbose_name_plural': 'Etapas do Checklist NR-1',
                'ordering': ['numero_etapa'],
                'unique_together': {('campaign', 'numero_etapa')},
            },
        ),
        migrations.CreateModel(
            name='ChecklistNR1Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.TextField()),
                ('automatico', models.BooleanField(default=False, help_text='Automatically marked complete by system')),
                ('concluido', models.BooleanField(default=False)),
                ('data_conclusao', models.DateTimeField(blank=True, null=True)),
                ('responsavel', models.CharField(blank=True, max_length=255)),
                ('prazo', models.DateField(blank=True, null=True)),
                ('observacoes', models.TextField(blank=True)),
                ('ordem', models.IntegerField(default=0)),
                ('etapa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='actions.checklistnr1etapa')),
            ],
            options={
                'verbose_name': 'Item do Checklist NR-1',
                'verbose_name_plural': 'Itens do Checklist NR-1',
                'ordering': ['ordem'],
            },
        ),
        migrations.CreateModel(
            name='EvidenciaNR1',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_original', models.CharField(max_length=255)),
                ('storage_path', models.CharField(max_length=500)),
                ('storage_url', models.URLField(blank=True)),
                ('tipo', models.CharField(choices=[('documento', 'Documento'), ('imagem', 'Imagem'), ('planilha', 'Planilha'), ('apresentacao', 'Apresentação'), ('email', 'E-mail'), ('ata', 'Ata'), ('certificado', 'Certificado'), ('outro', 'Outro')], default='documento', max_length=20)),
                ('tamanho_bytes', models.BigIntegerField()),
                ('descricao', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('checklist_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidencias', to='actions.checklistnr1item')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tenants.empresa')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Evidência NR-1',
                'verbose_name_plural': 'Evidências NR-1',
                'ordering': ['-created_at'],
            },
        ),
    ]
