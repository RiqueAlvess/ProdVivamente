from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyinvitation',
            name='email_hash',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
    ]
