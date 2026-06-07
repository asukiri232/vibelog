"""Друзья = взаимная подписка (оба Follow)."""
from django.contrib.auth.models import User

from .models import Follow


def mutual_follow_ids(user: User) -> set[int]:
    following = set(
        Follow.objects.filter(follower=user).values_list('following_id', flat=True)
    )
    followers = set(
        Follow.objects.filter(following=user).values_list('follower_id', flat=True)
    )
    return following & followers


def are_friends(a: User, b: User) -> bool:
    if not a.is_authenticated or not b.is_authenticated or a.pk == b.pk:
        return False
    return Follow.objects.filter(follower=a, following=b).exists() and Follow.objects.filter(
        follower=b, following=a
    ).exists()
