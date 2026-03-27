# Generated migration to remove document-related models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_nonstudent_student'),
    ]

    operations = [
        # Remove Document-related models
        migrations.DeleteModel(
            name='DocumentKeyRequest',
        ),
        migrations.DeleteModel(
            name='OneTimeKey',
        ),
        migrations.DeleteModel(
            name='ResumeAnalysisLog',
        ),
        migrations.DeleteModel(
            name='ResumeKeyword',
        ),
        migrations.DeleteModel(
            name='ResumeRating',
        ),
        migrations.DeleteModel(
            name='Resume',
        ),
        migrations.DeleteModel(
            name='DocumentPerformance',
        ),
        migrations.DeleteModel(
            name='ShardKey',
        ),
        migrations.DeleteModel(
            name='Shard',
        ),
        migrations.DeleteModel(
            name='Document',
        ),
    ]
