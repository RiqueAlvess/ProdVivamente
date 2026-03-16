import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factindicadorcampanha',
            name='campaign',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='surveys.campaign'),
        ),
    ]
