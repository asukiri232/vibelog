import io
import logging
import re
from typing import Iterable, List, Set

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile

try:
    from PIL import Image
except ImportError:
    Image = None

MAX_IMAGE_EDGE = 1920
JPEG_QUALITY = 85

MENTION_RE = re.compile(r'@([a-zA-Z0-9_]{1,150})')

logger = logging.getLogger(__name__)


def optimize_uploaded_image(uploaded, max_edge=MAX_IMAGE_EDGE):
    """Сжимает изображение перед сохранением; при отсутствии Pillow возвращает как есть."""
    if not uploaded or not Image:
        return uploaded
    try:
        img = Image.open(uploaded)
        img.load()
    except Exception:
        return uploaded

    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    w, h = img.size
    if max(w, h) > max_edge:
        if w >= h:
            nh = int(h * max_edge / w)
            nw = max_edge
        else:
            nw = int(w * max_edge / h)
            nh = max_edge
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    buf.seek(0)
    name = uploaded.name.rsplit('.', 1)[0] + '.jpg' if '.' in uploaded.name else 'image.jpg'
    return InMemoryUploadedFile(
        buf,
        uploaded.field_name if hasattr(uploaded, 'field_name') else 'image',
        name,
        'image/jpeg',
        buf.getbuffer().nbytes,
        None,
    )


def extract_mention_usernames(text: str) -> List[str]:
    if not text:
        return []
    seen = set()
    out = []
    for m in MENTION_RE.finditer(text):
        u = m.group(1).lower()
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def blocked_user_ids(user) -> Set[int]:
    if not user.is_authenticated:
        return set()
    from .models import UserBlock

    blocked = set(
        UserBlock.objects.filter(blocker=user).values_list('blocked_id', flat=True)
    )
    blocked |= set(
        UserBlock.objects.filter(blocked=user).values_list('blocker_id', flat=True)
    )
    return blocked


def safe_media_url(file_field) -> str:
    """Return the URL for a file field, or an empty string if the field is
    empty, has no name, or the storage backend raises any error.

    Catches all exceptions so that a missing or corrupt file never propagates
    to the template layer and crashes the request.
    """
    if not file_field:
        return ''
    name = getattr(file_field, 'name', None)
    if not name:
        return ''
    try:
        return file_field.url
    except Exception:
        logger.warning(
            'safe_media_url: could not resolve URL for file field %r (name=%r)',
            file_field,
            name,
            exc_info=True,
        )
        return ''


def post_grid_image_url(post) -> str:
    """Превью для сетки профиля: главное фото, вложение или пусто (видео/текст)."""
    url = safe_media_url(getattr(post, 'image', None))
    if url:
        return url
    attachments = getattr(post, '_prefetched_objects_cache', {}).get('attachments')
    if attachments is not None:
        iterable = attachments
    else:
        iterable = post.attachments.all()
    for att in iterable:
        url = safe_media_url(getattr(att, 'image', None))
        if url:
            return url
    return ''


def filter_blocked_users(qs, user, field_prefix=''):
    """Исключает пользователей из чёрного списка (в обе стороны)."""
    if not user.is_authenticated:
        return qs
    ids = blocked_user_ids(user)
    if not ids:
        return qs
    kw = {f'{field_prefix}__in': ids} if field_prefix else {'pk__in': ids}
    return qs.exclude(**kw)
