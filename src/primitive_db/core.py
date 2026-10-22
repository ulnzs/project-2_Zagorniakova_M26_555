"""Основная бизнес-логика примитивной базы данных."""

import json

from primitive_db.constants import ID_COLUMN, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import delete_table_data, load_table_data

_cache_select_result = create_cacher()


def _validate_identifier(name, entity_name):
    """Проверить имя таблицы или столбца."""
    if not name or not name.isidentifier():
        raise ValueError(f"некорректное имя {entity_name}: {name}")


def _normalize_column(column):
    """Преобразовать описание столбца к паре имя/тип."""
    if isinstance(column, str):
        column_name, separator, type_name = column.partition(":")
        if not separator:
            raise ValueError(f'столбец "{column}" должен иметь формат имя:тип')
    elif isinstance(column, (tuple, list)) and len(column) == 2:
        column_name, type_name = column
    else:
        raise ValueError(f"некорректное описание столбца: {column}")

    column_name = str(column_name).strip()
    type_name = str(type_name).strip().lower()
    _validate_identifier(column_name, "столбца")
    if type_name not in VALID_TYPES:
        raise ValueError(
            f'тип "{type_name}" не поддерживается; доступны: '
            f'{", ".join(VALID_TYPES)}'
        )
    return column_name, type_name


def _get_columns(metadata, table_name):
    """Вернуть список описаний столбцов существующей таблицы."""
    if table_name not in metadata:
        raise KeyError(table_name)
    return metadata[table_name]


def _column_pairs(columns):
    """Преобразовать список строк имя:тип в список пар."""
    return [_normalize_column(column) for column in columns]


def _coerce_value(value, type_name):
    """Проверить и при необходимости преобразовать значение к типу столбца."""
    if type_name == "str":
        if not isinstance(value, str):
            raise ValueError(f'ожидался тип str, получено значение "{value}"')
        return value
    if type_name == "int":
        if isinstance(value, bool):
            raise ValueError(f'ожидался тип int, получено значение "{value}"')
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f'ожидался тип int, получено значение "{value}"'
            ) from error
    if type_name == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ("true", "false"):
            return value.lower() == "true"
        raise ValueError(f'ожидался тип bool, получено значение "{value}"')
    raise ValueError(f'неподдерживаемый тип "{type_name}"')


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создать таблицу, автоматически добавив целочисленный столбец ID."""
    _validate_identifier(table_name, "таблицы")
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None
    if not columns:
        raise ValueError("необходимо указать хотя бы один столбец")

    normalized_columns = [(ID_COLUMN, "int")]
    seen_names = {ID_COLUMN}
    for column in columns:
        column_name, type_name = _normalize_column(column)
        if column_name in seen_names:
            raise ValueError(f'столбец "{column_name}" указан повторно')
        seen_names.add(column_name)
        normalized_columns.append((column_name, type_name))

    metadata[table_name] = [
        f"{column_name}:{type_name}"
        for column_name, type_name in normalized_columns
    ]
    columns_text = ", ".join(metadata[table_name])
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}'
    )
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удалить таблицу из метаданных и удалить её файл данных."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None
    del metadata[table_name]
    delete_table_data(table_name)
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Вернуть отсортированный список имён таблиц."""
    return sorted(metadata)


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавить запись с автоматически сгенерированным ID."""
    columns = _column_pairs(_get_columns(metadata, table_name))
    data_columns = columns[1:]
    if len(values) != len(data_columns):
        raise ValueError(
            f"ожидалось значений: {len(data_columns)}, получено: {len(values)}"
        )

    table_data = load_table_data(table_name)
    current_ids = [
        row.get(ID_COLUMN, 0)
        for row in table_data
        if isinstance(row.get(ID_COLUMN, 0), int)
    ]
    new_id = max(current_ids, default=0) + 1
    record = {ID_COLUMN: new_id}
    for (column_name, type_name), value in zip(data_columns, values, strict=True):
        record[column_name] = _coerce_value(value, type_name)
    table_data.append(record)
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


def _matches(record, where_clause):
    """Проверить соответствие записи всем условиям фильтра."""
    if where_clause is None:
        return True
    for column_name, expected_value in where_clause.items():
        if column_name not in record:
            raise KeyError(column_name)
        if record[column_name] != expected_value:
            return False
    return True


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Вернуть все записи либо записи, соответствующие условию."""
    cache_key = (
        json.dumps(table_data, ensure_ascii=False, sort_keys=True),
        json.dumps(where_clause, ensure_ascii=False, sort_keys=True),
    )

    def get_filtered_records():
        return [
            dict(record) for record in table_data if _matches(record, where_clause)
        ]

    cached_records = _cache_select_result(cache_key, get_filtered_records)
    return [dict(record) for record in cached_records]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновить поля всех записей, соответствующих условию."""
    for record in table_data:
        if _matches(record, where_clause):
            for column_name, new_value in set_clause.items():
                if column_name == ID_COLUMN:
                    raise ValueError("изменять ID запрещено")
                if column_name not in record:
                    raise KeyError(column_name)
                current_value = record[column_name]
                if isinstance(current_value, bool):
                    type_name = "bool"
                elif isinstance(current_value, int):
                    type_name = "int"
                else:
                    type_name = "str"
                record[column_name] = _coerce_value(new_value, type_name)
    return table_data


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data, where_clause):
    """Удалить все записи, соответствующие условию."""
    return [record for record in table_data if not _matches(record, where_clause)]

