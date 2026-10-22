"""Константы приложения."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
ID_COLUMN = "ID"
VALID_TYPES = ("int", "str", "bool")
YES_ANSWER = "y"
COMMAND_PROMPT = ">>> Введите команду: "

APP_TITLE = "***Примитивная база данных***"
HELP_LINES = (
    "",
    "***Операции с таблицами и данными***",
    "Функции:",
    "<command> create_table <таблица> <столбец:тип> ... - создать таблицу",
    "<command> list_tables - показать список всех таблиц",
    "<command> drop_table <таблица> - удалить таблицу",
    "<command> insert into <таблица> values (<значения>) - добавить запись",
    "<command> select from <таблица> [where <столбец> = <значение>] - выборка",
    "<command> update <таблица> set <столбец> = <значение> where ... - обновить",
    "<command> delete from <таблица> where <столбец> = <значение> - удалить",
    "<command> info <таблица> - показать информацию о таблице",
    "<command> help - справочная информация",
    "<command> exit - выход из программы",
    "",
)

