from django import template

from vibel.utils import post_grid_image_url, safe_media_url

register = template.Library()


@register.filter
def safe_media_url_filter(file_field):
    return safe_media_url(file_field)


@register.filter
def post_grid_thumb(post):
    return post_grid_image_url(post)
