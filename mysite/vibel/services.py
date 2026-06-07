from django.contrib.auth.models import User

from .models import Notification, Profile
from .utils import extract_mention_usernames


def user_wants_notification(recipient, event_type):
    profile, _ = Profile.objects.get_or_create(user=recipient)
    if event_type == Notification.TYPE_LIKE:
        return profile.notify_likes
    if event_type == Notification.TYPE_COMMENT:
        return profile.notify_comments
    if event_type == Notification.TYPE_FOLLOW:
        return profile.notify_follows
    if event_type == Notification.TYPE_MENTION:
        return profile.notify_mentions
    return True


def create_notification(*, recipient, actor, event_type, text='', post=None):
    if recipient.id == actor.id:
        return None
    if not user_wants_notification(recipient, event_type):
        return None
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        post=post,
        event_type=event_type,
        text=text,
    )


def notify_mentions(*, text, actor, post=None):
    usernames = extract_mention_usernames(text)
    if not usernames:
        return
    users = User.objects.filter(username__in=usernames).exclude(pk=actor.pk)
    for u in users:
        create_notification(
            recipient=u,
            actor=actor,
            event_type=Notification.TYPE_MENTION,
            text=f'{actor.profile.display_handle} упомянул(а) вас',
            post=post,
        )
