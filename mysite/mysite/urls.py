import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve


def health(_request):
    return HttpResponse('ok', content_type='text/plain')


def ready(_request):
    from django.contrib.auth import get_user_model

    media_root = settings.MEDIA_ROOT
    media_files = 0
    if media_root and os.path.isdir(media_root):
        for _root, _dirs, files in os.walk(media_root):
            media_files += len(files)
    users = get_user_model().objects.count()
    return HttpResponse(
        f'ok users={users} media_files={media_files} media_root={media_root}',
        content_type='text/plain',
    )


urlpatterns = [
    path('health/', health, name='health'),
    path('ready/', ready, name='ready'),
    path('admin/', admin.site.urls),
    path('', include('vibel.urls')),
]

_serve_media = settings.DEBUG or getattr(settings, 'SERVE_MEDIA', False)
if _serve_media:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Railway / Vercel: явная раздача /media/ (надёжнее за прокси).
if _serve_media and (
    os.environ.get('VERCEL')
    or os.environ.get('RAILWAY_ENVIRONMENT')
    or os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    or os.environ.get('PORT')
):
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]

# Запасной путь для Vercel, если CDN/static не подхватился.
if os.environ.get('VERCEL'):
    urlpatterns += [
        re_path(
            r'^static/(?P<path>.*)$',
            serve,
            {'document_root': settings.STATIC_ROOT},
        ),
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
