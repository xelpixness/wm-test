import os
import argparse
from datetime import datetime
AVAILABLE_REPORTS = ['average', 'max', 'user-agent']

def check_file_access(file_path):
    if not os.path.exists(file_path):
        raise argparse.ArgumentTypeError(f"Файл '{file_path}' не существует!")
    if not os.path.isfile(file_path):
        raise argparse.ArgumentTypeError(f"'{file_path}' должен быть файлом, а не директорией!")
    if not os.access(file_path, os.R_OK):
        raise argparse.ArgumentTypeError(f"Нет прав на чтение файла '{file_path}'!")
    return file_path


def check_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%d-%m").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Некорректный формат даты: {date_str}. Ожидается YYYY-DD-MM")


def check_report_type(report_name):
    if report_name not in AVAILABLE_REPORTS:
        raise argparse.ArgumentTypeError(
            f"Отчет '{report_name}' недоступен. Допустимые: {AVAILABLE_REPORTS}"
        )
    return report_name
