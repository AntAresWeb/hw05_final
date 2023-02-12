# Создано при изучении теории С4Т4 Контекст-процессоры
import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': dt.date.today().year,
    }
