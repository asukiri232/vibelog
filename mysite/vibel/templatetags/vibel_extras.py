import logging

from django import template

from vibel.utils import post_grid_image_url, safe_media_url

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter
def safe_media_url_filter(file_field):
    """Template filter wrapper around safe_media_url().

    Returns the media URL for *file_field*, or an empty string on any error.
    Failures are logged at WARNING level so they appear in Railway logs without
    crashing the request.
    """
    try:
        return safe_media_url(file_field)
    except Exception:
        logger.warning(
            'safe_media_url_filter: unexpected error for value %r',
            file_field,
            exc_info=True,
        )
        return ''


@register.filter
def post_grid_thumb(post):
    return post_grid_image_url(post)
