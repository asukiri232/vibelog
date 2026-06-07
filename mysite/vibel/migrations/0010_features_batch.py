# Generated for feature batch

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vibel', '0009_directmessage_hide_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_private',
            field=models.BooleanField(default=False, verbose_name='закрытый профиль'),
        ),
        migrations.AddField(
            model_name='profile',
            name='notify_comments',
            field=models.BooleanField(default=True, verbose_name='уведомления о комментариях'),
        ),
        migrations.AddField(
            model_name='profile',
            name='notify_follows',
            field=models.BooleanField(default=True, verbose_name='уведомления о подписках'),
        ),
        migrations.AddField(
            model_name='profile',
            name='notify_likes',
            field=models.BooleanField(default=True, verbose_name='уведомления о лайках'),
        ),
        migrations.AddField(
            model_name='profile',
            name='notify_mentions',
            field=models.BooleanField(default=True, verbose_name='уведомления об упоминаниях'),
        ),
        migrations.AddField(
            model_name='post',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='post',
            name='visibility',
            field=models.CharField(
                choices=[('public', 'Публичный'), ('private', 'Только для себя'), ('draft', 'Черновик')],
                default='public',
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='изображение'),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='edited_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='изменено'),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='reply_to',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='replies',
                to='vibel.directmessage',
            ),
        ),
        migrations.CreateModel(
            name='PostAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='posts/extra/', verbose_name='изображение')),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='vibel.post')),
            ],
            options={'ordering': ['sort_order', 'id']},
        ),
        migrations.CreateModel(
            name='HiddenPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hidden_by', to='vibel.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hidden_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('user', 'post')}},
        ),
        migrations.CreateModel(
            name='UserBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('blocked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks_in', to=settings.AUTH_USER_MODEL)),
                ('blocker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks_out', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('blocker', 'blocked')}},
        ),
        migrations.CreateModel(
            name='ContentReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_type', models.CharField(choices=[('post', 'Пост'), ('comment', 'Комментарий'), ('dm', 'Сообщение')], max_length=16)),
                ('target_id', models.PositiveIntegerField()),
                ('reason', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={'indexes': [models.Index(fields=['target_type', 'target_id'], name='vibel_conte_target__a1b2c3_idx')]},
        ),
    ]
