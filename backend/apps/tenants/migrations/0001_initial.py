from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('cnpj', models.CharField(max_length=18, unique=True)),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('total_funcionarios', models.IntegerField(default=0)),
                ('cnae', models.CharField(blank=True, max_length=10)),
                ('cnae_descricao', models.CharField(blank=True, max_length=255)),
                ('admin_email', models.EmailField(blank=True, max_length=254, verbose_name='E-mail do Admin RH')),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Empresa',
                'verbose_name_plural': 'Empresas',
                'ordering': ['nome'],
            },
        ),
    ]
