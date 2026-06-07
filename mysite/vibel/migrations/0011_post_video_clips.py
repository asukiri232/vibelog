from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('vibel', '0010_features_batch'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='video',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='posts/video/',
                verbose_name='видео',
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='video_clip_end_s',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name='конец клипа (сек)',
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='video_clip_limit_s',
            field=models.PositiveSmallIntegerField(
                choices=[(15, '15 секунд'), (30, '30 секунд')],
                default=15,
                verbose_name='лимит клипа (сек)',
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='video_clip_start_s',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name='начало клипа (сек)',
            ),
        ),
    ]

