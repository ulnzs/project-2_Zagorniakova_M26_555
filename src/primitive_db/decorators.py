"""Декораторы и замыкание для операций базы данных."""

import time

from primitive_db.constants import YES_ANSWER


def _preserve_metadata(wrapper, wrapped):
    """Сохранить основные метаданные обёрнутой функции без functools."""
    wrapper.__name__ = wrapped.__name__
    wrapper.__doc__ = wrapped.__doc__
    return wrapper


def handle_db_errors(func):
    """Перехватить типовые ошибки базы данных и показать понятное сообщение."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. База данных не инициализирована.")
        except KeyError as error:
            missing_item = error.args[0] if error.args else "неизвестный объект"
            print(f'Ошибка: Таблица или столбец "{missing_item}" не найден.')
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return _preserve_metadata(wrapper, func)


def confirm_action(action_name):
    """Создать декоратор, запрашивающий подтверждение опасной операции."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            question = (
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            )
            answer = input(question).strip().lower()
            if answer != YES_ANSWER:
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return _preserve_metadata(wrapper, func)

    return decorator


def log_time(func):
    """Вывести время выполнения функции по монотонным часам."""

    def wrapper(*args, **kwargs):
        started_at = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started_at
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")

    return _preserve_metadata(wrapper, func)


def create_cacher():
    """Создать функцию, кэширующую результаты вычислений по ключу."""
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    return cache_result

