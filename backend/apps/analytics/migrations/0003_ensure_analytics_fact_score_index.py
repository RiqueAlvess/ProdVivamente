"""
Ensure analytics_fact_score_idx exists on analytics_factscoredimensao.

This migration handles upgrade paths where 0001_initial was applied from an
older version of the code that did not include the AddIndex operation for
analytics_fact_score_idx. On those databases the index was never created,
even though the migration state in 0001_initial now declares it.

This migration is idempotent: if the index already exists (e.g. on a fresh
database where 0001_initial ran in full) the IF NOT EXISTS clause is a no-op.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_alter_factindicadorcampanha_campaign'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS analytics_fact_score_idx
                ON analytics_factscoredimensao (campaign_id, nivel_risco);
            """,
            reverse_sql="DROP INDEX IF EXISTS analytics_fact_score_idx;",
        ),
    ]
