from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Like, Post, Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


def _sync_post_likes(post_id):
    c = Like.objects.filter(post_id=post_id).count()
    Post.objects.filter(pk=post_id).update(likes_count=c)


@receiver(post_save, sender=Like)
def like_increment(sender, instance, created, **kwargs):
    if created:
        _sync_post_likes(instance.post_id)


@receiver(post_delete, sender=Like)
def like_decrement(sender, instance, **kwargs):
    _sync_post_likes(instance.post_id)
