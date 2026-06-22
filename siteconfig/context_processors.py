from .models import SiteSetting


def site_settings(request) -> dict:
    """Прокидывает настройки магазина во все шаблоны (контакты, тексты)."""
    try:
        return {'site': SiteSetting.load()}
    except Exception:  # noqa: BLE001 — таблицы может не быть до миграций
        return {'site': None}
