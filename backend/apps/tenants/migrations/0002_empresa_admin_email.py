from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='admin_email',
            field=models.EmailField(blank=True, verbose_name='E-mail do Admin RH'),
        ),
    ]
