"""Безопасная обработка ошибок записи (БД, файлы) — без 500 для пользователя."""
from __future__ import annotations

from django.contrib import messages
from django.db import DatabaseError
from django.http import JsonResponse
from django.shortcuts import redirect


WRITE_ERROR_MSG = 'Не удалось сохранить данные. Попробуйте ещё раз через минуту.'

_WRITE_EXCEPTIONS = (DatabaseError, OSError, PermissionError, IOError)


def wants_json_response(request) -> bool:
    if request.GET.get('vl_json') == '1':
        return True
    if request.POST.get('vl_expect_json') == '1':
        return True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return True
    accept = (request.headers.get('accept') or '').lower()
    return 'application/json' in accept


def run_safe_write(action, *, message: str = WRITE_ERROR_MSG):
    """Выполняет action(); при ошибке БД/файлов возвращает (None, message)."""
    try:
        return action(), None
    except _WRITE_EXCEPTIONS:
        return None, message


def respond_write_error(request, message: str = WRITE_ERROR_MSG, *, redirect_name: str = 'vibel:feed'):
    if wants_json_response(request):
        return JsonResponse({'ok': False, 'error': message}, status=500)
    messages.error(request, message)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect(redirect_name)


def add_form_write_error(form, message: str = WRITE_ERROR_MSG) -> None:
    form.add_error(None, message)
