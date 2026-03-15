from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cargo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Cargo',
                'verbose_name_plural': 'Cargos',
                'ordering': ['nome'],
                'unique_together': {('nome',)},
            },
        ),
        migrations.CreateModel(
            name='Unidade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Unidade',
                'verbose_name_plural': 'Unidades',
                'ordering': ['nome'],
                'unique_together': {('nome',)},
            },
        ),
        migrations.CreateModel(
            name='Setor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('unidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='setores', to='structure.unidade')),
            ],
            options={
                'verbose_name': 'Setor',
                'verbose_name_plural': 'Setores',
                'ordering': ['nome'],
                'unique_together': {('unidade', 'nome')},
            },
        ),
    ]
