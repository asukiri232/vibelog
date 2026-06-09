import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve


def health(_request):
    return HttpResponse('ok', content_type='text/plain')


urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('', include('vibel.urls')),
]

if settings.DEBUG or getattr(settings, 'SERVE_MEDIA', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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
