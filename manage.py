#!/usr/bin/env python
"""Точка входа Django для Vercel и локальных команд из корня репозитория."""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MYSITE_DIR = os.path.join(ROOT_DIR, 'mysite')

if MYSITE_DIR not in sys.path:
    sys.path.insert(0, MYSITE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')


def main():
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Install requirements.txt first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
