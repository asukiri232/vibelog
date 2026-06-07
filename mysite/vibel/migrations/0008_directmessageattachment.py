# Multiple images per direct message (new); legacy `DirectMessage.image` kept for old rows.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vibel', '0007_comment_dm_images'),
    ]

    operations = [
        migrations.CreateModel(
            name='DirectMessageAttachment',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'image',
                    models.ImageField(upload_to='dm/', verbose_name='изображение'),
                ),
                (
                    'sort_order',
                    models.PositiveSmallIntegerField(default=0),
                ),
                (
                    'message',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attachments',
                        to='vibel.directmessage',
                    ),
                ),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]
