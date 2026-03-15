import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('surveys', '0001_initial'),
        ('structure', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_token', models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                ('email_encrypted', models.TextField()),
                ('nome_encrypted', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('sent', 'Enviado'), ('used', 'Utilizado'), ('expired', 'Expirado')], default='pending', max_length=20)),
                ('expires_at', models.DateTimeField()),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='tenants.empresa')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='surveys.campaign')),
                ('unidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structure.unidade')),
                ('setor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='structure.setor')),
                ('cargo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='structure.cargo')),
            ],
            options={
                'verbose_name': 'Convite de Pesquisa',
                'verbose_name_plural': 'Convites de Pesquisa',
                'indexes': [
                    models.Index(fields=['campaign', 'status'], name='invitations_campaign_status_idx'),
                    models.Index(fields=['hash_token'], name='invitations_hash_token_idx'),
                    models.Index(fields=['expires_at'], name='invitations_expires_at_idx'),
                ],
            },
        ),
    ]
