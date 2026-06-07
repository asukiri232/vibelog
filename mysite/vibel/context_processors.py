from .forms import REPORT_REASON_CHOICES
from .models import DirectMessage, Notification, Profile


def header_state(request):
    unread_notifications_count = 0
    unread_dm_count = 0
    nav_profile = None
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        unread_dm_count = DirectMessage.objects.filter(
            recipient=request.user, read_at__isnull=True
        ).count()
        nav_profile, _ = Profile.objects.get_or_create(user=request.user)
    return {
        'unread_notifications_count': unread_notifications_count,
        'unread_dm_count': unread_dm_count,
        'nav_profile': nav_profile,
        'report_reason_choices': REPORT_REASON_CHOICES,
    }
