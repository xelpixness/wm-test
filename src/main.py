import argparse
import json
from tabulate import tabulate
from datetime import datetime

from dataclasses import dataclass

from abc import ABC, abstractmethod

from arg_checks import check_file_access, check_date, check_report_type, AVAILABLE_REPORTS


class ReportStrategy(ABC):
    @abstractmethod
    def grab_data(self, stats: dict, log_entry: dict): ...

    @abstractmethod
    def generate_report(self, stats: dict) -> list[dict]: ...


@dataclass
class AverageReportItem:
    handler: str
    total: int
    avg_response_time: float


class AverageReportStrategy(ReportStrategy):
    def grab_data(self, stats: dict, log_entry: dict):
        url = log_entry.get('url', 'unknown')
        response_time = log_entry.get('response_time', 0.0)
        if url not in stats:
            stats[url] = {'total': 0, 'sum_response_time': 0.0}
        stats[url]['total'] += 1
        stats[url]['sum_response_time'] += response_time

    def generate_report(self, stats: dict) -> list[AverageReportItem]:
        report = []
        for url, data in stats.items():
            avg_time = data['sum_response_time'] / data['total'] if data['total'] > 0 else 0
            report.append(AverageReportItem(
                handler=url,
                total=data['total'],
                avg_response_time=round(avg_time, 3)
            ))
        return sorted(report, key=lambda x: x.total, reverse=True)



class UserAgentStrategy(ReportStrategy):
    def grab_data(self, stats: dict, log_entry: dict):
        user_agent = log_entry.get('http_user_agent', 'unknown')
        if user_agent not in stats:
            stats[user_agent] = {'total': 0}
        stats[user_agent]['total'] += 1


    def generate_report(self, stats: dict) -> list[dict]:
        report = []
        for user_agent, data in stats.items():
            report.append({
                'user_agent': user_agent,
                'total': data['total'],
            })
        return sorted(report, key=lambda x: x['total'], reverse=True)



class LogAnalyzer:
    def __init__(self):
        self.file_paths: list[str] = []
        self.target_date: datetime.time = None
        self._report_data: list[dict] = []
        self.strategy: ReportStrategy | None = None


    def set_strategy(self, strategy: ReportStrategy):
        self.strategy = strategy


    def process_logs(self):
        if not self.strategy:
            raise ValueError("Не выбран тип отчета!")

        stats = {}
        for file_path in self.file_paths:
            with open(file_path, 'r') as file:
                for line in file:
                    try:
                        log_entry = json.loads(line)

                        if self.target_date is not None:
                            log_timestamp = datetime.strptime(
                                log_entry.get('@timestamp', ''),
                                "%Y-%m-%dT%H:%M:%S%z"
                            ).date()

                            if log_timestamp != self.target_date:
                                continue

                        self.strategy.grab_data(stats, log_entry)

                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Ошибка в строке файла {file_path}: {line.strip()}")
                        print(f"Ошибка: {str(e)}")

        self._report_data = self.strategy.generate_report(stats)


    def print_report(self) -> None:
        print(tabulate(self._report_data, headers='keys', showindex='always'))


    def __str__(self) -> str:
        return f"LogAnalyzer, files={len(self.file_paths)})"


def main():
    parser = argparse.ArgumentParser(description="Программа для обработки лог файлов.")
    parser.add_argument('--file',
                        nargs='+',
                        type=check_file_access,
                        help="Один или несколько .log файлов",
                        required=True)

    parser.add_argument('--report',
                        type=check_report_type,
                        help="Название отчета",
                        required=True)

    parser.add_argument('--date',
                        type=check_date,
                        help="Дата для фильтрации логов (формат: YYYY-DD-MM)")


    args = parser.parse_args()

    log_analyzer = LogAnalyzer()

    log_analyzer.file_paths = args.file
    log_analyzer.target_date = args.date


    if args.report == "average":
        log_analyzer.set_strategy(AverageReportStrategy())
    elif args.report == "user-agent":
        log_analyzer.set_strategy(UserAgentStrategy())

    log_analyzer.process_logs()
    log_analyzer.print_report()


if __name__ == '__main__':
    main()
