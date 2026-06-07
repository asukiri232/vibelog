"""Сборка для Vercel: статика отдаётся через WhiteNoise finders (vibel/static/)."""


def main() -> None:
    # collectstatic дублирует admin-assets и раздувает bundle; на Vercel включён
    # WHITENOISE_USE_FINDERS в settings.py — исходников vibel/static/ достаточно.
    print('Vercel build: static via WhiteNoise finders (no collectstatic)')


if __name__ == '__main__':
    main()
