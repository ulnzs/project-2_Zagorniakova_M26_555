# Примитивная база данных

Учебное консольное приложение на Python 3.12. Проект хранит схему базы в
`db_meta.json`, а записи каждой таблицы — в отдельном JSON-файле каталога
`data/`. Реализация процедурная: классы не используются.

## Возможности

- создание, просмотр и удаление таблиц;
- типы данных `int`, `str` и `bool`;
- автоматическая генерация целочисленного `ID`;
- CRUD-операции и фильтрация `where`;
- табличный вывод с помощью PrettyTable;
- централизованная обработка ошибок;
- подтверждение удаления таблиц и записей;
- замер времени `insert` и `select`;
- кэширование одинаковых запросов `select` через замыкание.

## Установка и запуск

Требуются `uv` и Python 3.12. В корне проекта выполните:

```bash
uv sync
uv run database
```

Для совместимости с первой частью задания доступна также команда:

```bash
uv run project
```

Модуль можно запустить напрямую:

```bash
uv run python -m primitive_db.main
```

## Команды

```text
create_table users name:str age:int is_active:bool
list_tables
insert into users values ("Sergei", 28, true)
select from users
select from users where age = 28
update users set age = 29 where name = "Sergei"
delete from users where ID = 1
info users
drop_table users
help
exit
```

Строковые значения в CRUD-командах необходимо заключать в одинарные или
двойные кавычки. Перед `delete` и `drop_table` программа запрашивает `y/n`.

## Проверка качества и сборка

```bash
uv run ruff check .
uv build
uvx twine check dist/*
```

## Демонстрация asciinema

Финальную запись следует сделать после указания личных данных и размещения
проекта в учебном репозитории:

```bash
asciinema rec primitive-db.cast
uv run database
```

Запись должна показать создание таблицы, `insert`, `select`, `update`,
подтверждение `delete`, `info` и подтверждение `drop_table`. После публикации
ссылку на запись нужно добавить в этот раздел README.
