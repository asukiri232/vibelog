"""Сборка для Vercel: migrate, collectstatic, копия в public/static для CDN."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args: str) -> None:
    subprocess.check_call([sys.executable, *args], cwd=ROOT)


def main() -> None:
    # migrate на Vercel выполняется при cold start (см. vercel_bootstrap.py)
    run('manage.py', 'collectstatic', '--noinput')

    src = ROOT / 'mysite' / 'staticfiles'
    dst = ROOT / 'public' / 'static'
    if not src.exists():
        raise SystemExit(f'collectstatic did not create {src}')

    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    print(f'Copied static assets to {dst}')


if __name__ == '__main__':
    main()
