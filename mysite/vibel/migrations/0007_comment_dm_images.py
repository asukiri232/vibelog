from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vibel', '0006_directmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='comments/',
                verbose_name='изображение',
            ),
        ),
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(
                blank=True,
                default='',
                max_length=500,
                verbose_name='текст',
            ),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='dm/',
                verbose_name='изображение',
            ),
        ),
        migrations.AlterField(
            model_name='directmessage',
            name='body',
            field=models.TextField(
                blank=True,
                default='',
                max_length=2000,
                verbose_name='текст',
            ),
        ),
    ]
