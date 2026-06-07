import logging
import os

from django.core.exceptions import ValidationError

from .errors import WRITE_ERROR_MSG, respond_write_error

logger = logging.getLogger(__name__)

class VercelBootstrapMiddleware:
    """Гарантирует БД и /tmp/media перед обработкой запроса на Vercel."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if os.environ.get('VERCEL'):
            try:
                from vercel_bootstrap import ensure_vercel_runtime

                ensure_vercel_runtime()
            except Exception:
                logger.exception('Vercel bootstrap failed in middleware')
        return self.get_response(request)


class SafeWriteErrorMiddleware:
    """На Vercel ловит необработанные ошибки записи и не отдаёт голый 500."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            if not os.environ.get('VERCEL'):
                raise
            from django.db import DatabaseError

            write_errors = (
                DatabaseError,
                OSError,
                PermissionError,
                IOError,
                ValidationError,
            )
            if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
                raise
            if not isinstance(exc, write_errors):
                logger.exception('Unhandled error on %s %s', request.method, request.path)
                raise
            logger.warning('Write error on %s %s: %s', request.method, request.path, exc)
            return respond_write_error(request, WRITE_ERROR_MSG)
