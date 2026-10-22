"""Вспомогательные функции для хранения JSON-данных."""

import json
import os

from primitive_db.constants import DATA_DIR


def load_metadata(filepath):
    """Загрузить метаданные или вернуть пустой словарь, если файла нет."""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохранить метаданные в JSON-файл."""
    parent_directory = os.path.dirname(filepath)
    if parent_directory:
        os.makedirs(parent_directory, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_table_filepath(table_name):
    """Вернуть путь к JSON-файлу таблицы."""
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Загрузить записи таблицы или вернуть пустой список, если файла нет."""
    filepath = get_table_filepath(table_name)
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохранить записи таблицы в отдельный JSON-файл."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = get_table_filepath(table_name)
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def delete_table_data(table_name):
    """Удалить файл данных таблицы, если он существует."""
    filepath = get_table_filepath(table_name)
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass

