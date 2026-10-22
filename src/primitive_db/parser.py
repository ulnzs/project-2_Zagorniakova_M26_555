"""Разбор значений и составных команд консольной базы данных."""


def _split_comma_separated(text):
    """Разделить строку по запятым, сохраняя содержимое кавычек."""
    parts = []
    current = []
    quote = None
    escaped = False

    for character in text:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\" and quote:
            current.append(character)
            escaped = True
        elif character in ("'", '"'):
            current.append(character)
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
        elif character == "," and quote is None:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(character)

    if quote is not None:
        raise ValueError("незакрытая кавычка")

    parts.append("".join(current).strip())
    if any(not part for part in parts):
        raise ValueError("между запятыми должно быть значение")
    return parts


def parse_value(raw_value):
    """Преобразовать текстовое представление в int, str или bool."""
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]

    lowered_value = value.lower()
    if lowered_value == "true":
        return True
    if lowered_value == "false":
        return False

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f'строковое значение "{value}" должно быть в кавычках'
        ) from error


def parse_values(values_text):
    """Разобрать список значений в круглых скобках."""
    stripped_text = values_text.strip()
    if not (stripped_text.startswith("(") and stripped_text.endswith(")")):
        raise ValueError("значения должны находиться в круглых скобках")
    inner_text = stripped_text[1:-1].strip()
    if not inner_text:
        return []
    return [parse_value(item) for item in _split_comma_separated(inner_text)]


def _split_assignment(assignment):
    """Разделить выражение присваивания по знаку вне кавычек."""
    quote = None
    for index, character in enumerate(assignment):
        if character in ("'", '"'):
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
        elif character == "=" and quote is None:
            column = assignment[:index].strip()
            value = assignment[index + 1 :].strip()
            if not column or not value:
                break
            return column, value
    raise ValueError(f'условие "{assignment.strip()}" должно содержать знак =')


def parse_where_clause(where_text):
    """Преобразовать условие where в словарь с одним элементом."""
    column, raw_value = _split_assignment(where_text)
    return {column: parse_value(raw_value)}


def parse_set_clause(set_text):
    """Преобразовать одно или несколько присваиваний set в словарь."""
    result = {}
    for assignment in _split_comma_separated(set_text):
        column, raw_value = _split_assignment(assignment)
        result[column] = parse_value(raw_value)
    return result

