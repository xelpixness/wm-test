import argparse
import json
from tabulate import tabulate
from datetime import datetime

from arg_checks import check_file_access, check_date, check_report_type, AVAILABLE_REPORTS


class LogAnalyzer:
    def __init__(self):
        self.file_paths = []
        self.available_reports = AVAILABLE_REPORTS
        self.target_date = None
        self.report_type = None
        self._report_data = []

        self._grab_methods = {
            'average': self._grab_by_average,
            'user-agent': self._grab_by_user_agent,
            'max': self._grab_by_max # не реализован
        }

        self._report_generators = {
            'average': self._generate_average_report,
            'user-agent': self._generate_user_agent_report,
            'max': self._generate_max_report, # не реализован
        }


    def process_logs(self):
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

                        self._grab_methods[self.report_type](stats, log_entry)

                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Ошибка в строке файла {file_path}: {line.strip()}")
                        print(f"Ошибка: {str(e)}")

        self._report_generators[self.report_type](stats)



    def _grab_by_average(self, stats, log_entry):
        url = log_entry.get('url', 'unknown')
        response_time = log_entry.get('response_time', 0.0)

        if url not in stats:
            stats[url] = {'total': 0, 'sum_response_time': 0.0}

        stats[url]['total'] += 1
        stats[url]['sum_response_time'] += response_time


    def _generate_average_report(self, stats):
        report = []
        for url, data in stats.items():
            avg_time = data['sum_response_time'] / data['total'] if data['total'] > 0 else 0
            report.append({
                'handler': url,
                'total': data['total'],
                'avg_response_time': round(avg_time, 3)
            })
        self._report_data = report
        self._report_data.sort(key=lambda x: x['total'], reverse=True)


    # Бонусное
    def _grab_by_user_agent(self, stats, log_entry):
        user_agent = log_entry.get('http_user_agent', 'unknown')
        if user_agent not in stats:
            stats[user_agent] = {'total': 0}
        stats[user_agent]['total'] += 1


    def _generate_user_agent_report(self, stats):
        report = []
        for user_agent, data in stats.items():
            report.append({
                'user_agent': user_agent,
                'total': data['total'],
            })
        self._report_data = report
        self._report_data.sort(key=lambda x: x['total'], reverse=True)


    # если надо пропишем здесь логику сбора данных
    # а в ф-ии ниже сгенерим отчет. пока пусть выбрасывает необработанное исключение
    def _grab_by_max(self, stats, log_entry):
        raise NotImplementedError("Отчёт 'max' в разработке")
    def _generate_max_report(self, stats):
        ...


    def print_report(self):
        print(tabulate(self._report_data, headers='keys', showindex='always'))

    def get_available_reports(self):
        return self.available_reports

    def __str__(self):
        return f"LogAnalyzer (report_type={self.report_type}, files={len(self.file_paths)})"



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
    log_analyzer.report_type = args.report

    log_analyzer.process_logs()
    log_analyzer.print_report()


if __name__ == '__main__':
    main()



