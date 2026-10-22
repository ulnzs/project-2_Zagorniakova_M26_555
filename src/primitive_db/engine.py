"""Консольный цикл и маршрутизация команд базы данных."""

import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    APP_TITLE,
    COMMAND_PROMPT,
    HELP_LINES,
    META_FILE,
)
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
)
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_set_clause, parse_values, parse_where_clause
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Вывести справку по всем командам."""
    print("\n".join(HELP_LINES))


def welcome():
    """Показать приветствие и доступные команды."""
    print(APP_TITLE)
    print_help()


def _split_keyword(text, keyword):
    """Разделить текст по ключевой фразе без учёта регистра."""
    index = text.lower().find(keyword.lower())
    if index == -1:
        raise ValueError(f'ожидалась часть команды "{keyword.strip()}"')
    return text[:index].strip(), text[index + len(keyword) :].strip()


def _require_table(metadata, table_name):
    """Проверить существование таблицы."""
    if table_name not in metadata:
        raise KeyError(table_name)


def _print_records(records, columns):
    """Вывести записи в формате PrettyTable."""
    field_names = [column.split(":", maxsplit=1)[0] for column in columns]
    table = PrettyTable()
    table.field_names = field_names
    for record in records:
        table.add_row([record.get(field_name, "") for field_name in field_names])
    print(table)


def _handle_create(metadata, tokens):
    """Обработать команду создания таблицы."""
    if len(tokens) < 3:
        raise ValueError("формат: create_table <таблица> <столбец:тип> ...")
    updated_metadata = create_table(metadata, tokens[1], tokens[2:])
    if updated_metadata is not None:
        save_metadata(META_FILE, updated_metadata)


def _handle_drop(metadata, tokens):
    """Обработать команду удаления таблицы."""
    if len(tokens) != 2:
        raise ValueError("формат: drop_table <таблица>")
    updated_metadata = drop_table(metadata, tokens[1])
    if updated_metadata is not None:
        save_metadata(META_FILE, updated_metadata)


def _handle_insert(metadata, command_line):
    """Обработать команду вставки записи."""
    prefix = "insert into "
    if not command_line.lower().startswith(prefix):
        raise ValueError("формат: insert into <таблица> values (<значения>)")
    remainder = command_line[len(prefix) :].strip()
    table_name, values_text = _split_keyword(remainder, " values ")
    _require_table(metadata, table_name)
    table_data = insert(metadata, table_name, parse_values(values_text))
    if table_data is not None:
        save_table_data(table_name, table_data)


def _handle_select(metadata, command_line):
    """Обработать команду выборки записей."""
    prefix = "select from "
    if not command_line.lower().startswith(prefix):
        raise ValueError("формат: select from <таблица> [where <условие>]")
    remainder = command_line[len(prefix) :].strip()
    if " where " in remainder.lower():
        table_name, where_text = _split_keyword(remainder, " where ")
        where_clause = parse_where_clause(where_text)
    else:
        table_name = remainder
        where_clause = None
    _require_table(metadata, table_name)
    records = select(load_table_data(table_name), where_clause)
    if records is not None:
        _print_records(records, metadata[table_name])


def _handle_update(metadata, command_line):
    """Обработать команду обновления записей."""
    prefix = "update "
    if not command_line.lower().startswith(prefix):
        raise ValueError("формат: update <таблица> set ... where ...")
    remainder = command_line[len(prefix) :].strip()
    table_name, clauses_text = _split_keyword(remainder, " set ")
    set_text, where_text = _split_keyword(clauses_text, " where ")
    _require_table(metadata, table_name)

    original_data = load_table_data(table_name)
    matching_ids = [
        record.get("ID")
        for record in original_data
        if all(
            record.get(column) == value
            for column, value in parse_where_clause(where_text).items()
        )
    ]
    updated_data = update(
        original_data,
        parse_set_clause(set_text),
        parse_where_clause(where_text),
    )
    if updated_data is not None:
        save_table_data(table_name, updated_data)
        if matching_ids:
            for record_id in matching_ids:
                print(
                    f'Запись с ID={record_id} в таблице "{table_name}" '
                    "успешно обновлена."
                )
        else:
            print("Подходящие записи не найдены.")


def _handle_delete(metadata, command_line):
    """Обработать команду удаления записей."""
    prefix = "delete from "
    if not command_line.lower().startswith(prefix):
        raise ValueError("формат: delete from <таблица> where <условие>")
    remainder = command_line[len(prefix) :].strip()
    table_name, where_text = _split_keyword(remainder, " where ")
    _require_table(metadata, table_name)

    table_data = load_table_data(table_name)
    where_clause = parse_where_clause(where_text)
    removed_ids = [
        record.get("ID")
        for record in table_data
        if all(
            record.get(column) == value for column, value in where_clause.items()
        )
    ]
    updated_data = delete(table_data, where_clause)
    if updated_data is not None:
        save_table_data(table_name, updated_data)
        if removed_ids:
            for record_id in removed_ids:
                print(
                    f'Запись с ID={record_id} успешно удалена из таблицы '
                    f'"{table_name}".'
                )
        else:
            print("Подходящие записи не найдены.")


def _handle_info(metadata, tokens):
    """Обработать команду вывода информации о таблице."""
    if len(tokens) != 2:
        raise ValueError("формат: info <таблица>")
    table_name = tokens[1]
    _require_table(metadata, table_name)
    record_count = len(load_table_data(table_name))
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {', '.join(metadata[table_name])}")
    print(f"Количество записей: {record_count}")


@handle_db_errors
def execute_command(command_line, metadata):
    """Распознать одну команду и вызвать соответствующую операцию."""
    tokens = shlex.split(command_line)
    if not tokens:
        raise ValueError("команда не может быть пустой")

    command = tokens[0].lower()
    if command == "exit":
        print("Работа с базой данных завершена.")
        return False
    if command == "help":
        print_help()
    elif command == "create_table":
        _handle_create(metadata, tokens)
    elif command == "list_tables":
        tables = list_tables(metadata)
        print("\n".join(f"- {table_name}" for table_name in tables))
        if not tables:
            print("Таблицы отсутствуют.")
    elif command == "drop_table":
        _handle_drop(metadata, tokens)
    elif command == "insert":
        _handle_insert(metadata, command_line)
    elif command == "select":
        _handle_select(metadata, command_line)
    elif command == "update":
        _handle_update(metadata, command_line)
    elif command == "delete":
        _handle_delete(metadata, command_line)
    elif command == "info":
        _handle_info(metadata, tokens)
    else:
        print(f'Функции "{tokens[0]}" нет. Попробуйте снова.')
    return True


def run():
    """Запустить основной цикл консольного приложения."""
    welcome()
    while True:
        metadata = load_metadata(META_FILE)
        try:
            command_line = prompt.string(COMMAND_PROMPT)
        except (EOFError, KeyboardInterrupt):
            print("\nРабота с базой данных завершена.")
            break
        if execute_command(command_line, metadata) is False:
            break

