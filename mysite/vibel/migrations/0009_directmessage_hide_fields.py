# Generated manually for per-user DM hide

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vibel', '0008_directmessageattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='directmessage',
            name='hidden_for_recipient_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name='скрыто у получателя'
            ),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='hidden_for_sender_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name='скрыто у отправителя'
            ),
        ),
    ]
