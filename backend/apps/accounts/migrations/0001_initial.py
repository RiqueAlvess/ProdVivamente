import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('structure', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('rh', 'RH'), ('lideranca', 'Liderança')], default='rh', max_length=20)),
                ('telefone', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usuarios', to='tenants.empresa', verbose_name='Empresa')),
                ('setores_permitidos', models.ManyToManyField(blank=True, to='structure.setor')),
                ('unidades_permitidas', models.ManyToManyField(blank=True, to='structure.unidade')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de Usuário',
                'verbose_name_plural': 'Perfis de Usuários',
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acao', models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'), ('import_csv', 'Importação CSV'), ('disparo_email', 'Disparo de E-mails'), ('export_relatorio', 'Exportação de Relatório'), ('create_campaign', 'Criação de Campanha'), ('view_dashboard', 'Visualização de Dashboard'), ('update_action', 'Atualização de Plano de Ação'), ('upload_evidence', 'Upload de Evidência'), ('delete_evidence', 'Remoção de Evidência')], max_length=50)),
                ('descricao', models.TextField()),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tenants.empresa', verbose_name='Empresa')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log de Auditoria',
                'verbose_name_plural': 'Logs de Auditoria',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'created_at'], name='accounts_au_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['empresa', 'created_at'], name='accounts_au_empresa_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['acao', 'created_at'], name='accounts_au_acao_idx'),
        ),
    ]
