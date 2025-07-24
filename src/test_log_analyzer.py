import pytest
import json
from main import LogAnalyzer
from datetime import datetime

@pytest.fixture
def sample_log_file(tmp_path):
    data = [
        {"@timestamp": "2025-06-22T13:57:32+00:00", "url": "/api/1", "response_time": 0.1},
        {"@timestamp": "2025-06-22T14:00:00+00:00", "url": "/api/1", "response_time": 0.3}
    ]
    file_path = tmp_path / "test.log"
    file_path.write_text('\n'.join(json.dumps(x) for x in data))
    return file_path


@pytest.fixture
def sample_large_log_file(tmp_path):
    data = [
        # API 1
        {"@timestamp": "2025-06-22T10:00:00+00:00", "url": "/api/users", "response_time": 0.15},
        {"@timestamp": "2025-06-22T10:01:00+00:00", "url": "/api/users", "response_time": 0.20},
        {"@timestamp": "2025-06-22T10:02:00+00:00", "url": "/api/users", "response_time": 0.18},
        {"@timestamp": "2025-06-22T10:03:00+00:00", "url": "/api/users", "response_time": 0.22},
        {"@timestamp": "2025-06-22T10:04:00+00:00", "url": "/api/users", "response_time": 0.25},

        # API 2   - другая дата
        {"@timestamp": "2025-03-27T11:00:00+00:00", "url": "/api/products", "response_time": 0.40},
        {"@timestamp": "2025-03-27T11:01:00+00:00", "url": "/api/products", "response_time": 0.35},
        {"@timestamp": "2025-03-27T11:02:00+00:00", "url": "/api/products", "response_time": 0.50},

        # API 3
        {"@timestamp": "2025-06-22T12:00:00+00:00", "url": "/api/orders", "response_time": 1.20},
        {"@timestamp": "2025-06-22T12:01:00+00:00", "url": "/api/orders", "response_time": 0.80}
    ]
    file_path = tmp_path / "large_test.log"
    file_path.write_text('\n'.join(json.dumps(x) for x in data))
    return file_path




# ------------------ _grab_by_average -----------------


def test_grab_by_average_basic(sample_log_file):
    analyzer = LogAnalyzer()
    stats = {}

    with open(sample_log_file) as f:
        first_line = f.readline()
        log_entry = json.loads(first_line)

        analyzer._grab_by_average(stats, log_entry)

    assert "/api/1" in stats
    assert stats["/api/1"]["total"] == 1
    assert stats["/api/1"]["sum_response_time"] == pytest.approx(0.1)


def test_grab_by_average_multiple_entries(sample_log_file):
    analyzer = LogAnalyzer()
    stats = {}

    with open(sample_log_file) as f:
        for line in f:
            log_entry = json.loads(line)
            analyzer._grab_by_average(stats, log_entry)

    assert stats["/api/1"]["total"] == 2
    assert stats["/api/1"]["sum_response_time"] == pytest.approx(0.4)


def test_grab_by_average_with_large_data(sample_large_log_file):
    analyzer = LogAnalyzer()
    stats = {}

    with open(sample_large_log_file) as f:
        for line in f:
            log_entry = json.loads(line)
            analyzer._grab_by_average(stats, log_entry)

    assert len(stats) == 3  # 3 уникальных API

    assert stats["/api/users"]["total"] == 5
    assert stats["/api/users"]["sum_response_time"] == pytest.approx(0.15 + 0.20 + 0.18 + 0.22 + 0.25)

    assert stats["/api/products"]["total"] == 3
    assert stats["/api/products"]["sum_response_time"] == pytest.approx(0.40 + 0.35 + 0.50)

    assert stats["/api/orders"]["total"] == 2
    assert stats["/api/orders"]["sum_response_time"] == pytest.approx(1.20 + 0.80)


def test_grab_by_average_missing_response_time():
    analyzer = LogAnalyzer()
    stats = {}
    log_entry = {"@timestamp": "2025-06-22T00:00:00+00:00", "url": "/api/test"}
    analyzer._grab_by_average(stats, log_entry)
    assert stats["/api/test"]["sum_response_time"] == 0.0


def test_grab_by_average_invalid_response_time():
    analyzer = LogAnalyzer()
    stats = {}
    log_entry = {"@timestamp": "2025-06-22", "url": "/api/test", "response_time": "badbad"}

    with pytest.raises(TypeError):
        analyzer._grab_by_average(stats, log_entry)


def test_grab_by_average_invalid_timestamp():
    analyzer = LogAnalyzer()
    stats = {}
    log_entry = {"@timestamp": "20asd", "url": "/api/test", "response_time": "0.3"}

    with pytest.raises(TypeError):
        analyzer._grab_by_average(stats, log_entry)




# ------------------ _generate_average_report -----------------

def test_generate_average_report_basic():
    analyzer = LogAnalyzer()
    test_stats = {
        "/api/users": {
            "total": 5,
            "sum_response_time": 1.0
        }
    }

    analyzer._generate_average_report(test_stats)

    assert len(analyzer._report_data) == 1
    assert analyzer._report_data[0]["handler"] == "/api/users"
    assert analyzer._report_data[0]["total"] == 5
    assert analyzer._report_data[0]["avg_response_time"] == 0.2  # 1.0 / 5



def test_generate_average_report_rounding():
    analyzer = LogAnalyzer()
    test_stats = {
        "/api/metrics": {
            "total": 3,
            "sum_response_time": 0.333
        }
    }
    analyzer._generate_average_report(test_stats)
    assert analyzer._report_data[0]["avg_response_time"] == 0.111


def test_generate_average_report_sorting():
    analyzer = LogAnalyzer()
    test_stats = {
        "/api/low": {
            "total": 2,
            "sum_response_time": 0.4
        },
        "/api/high": {
            "total": 5,
            "sum_response_time": 1.0
        }
    }

    analyzer._generate_average_report(test_stats)
    assert analyzer._report_data[0]["handler"] == "/api/high"
    assert analyzer._report_data[1]["handler"] == "/api/low"


def test_generate_average_report_empty():
    analyzer = LogAnalyzer()
    analyzer._generate_average_report({})

    assert analyzer._report_data == []






# ------------------ process_logs -----------------

def test_process_logs_without_date_filter(sample_large_log_file):
    analyzer = LogAnalyzer()
    analyzer.file_paths = [sample_large_log_file]
    analyzer.report_type = 'average'
    analyzer.target_date = None  # Явно отключаем фильтр даты

    analyzer.process_logs()

    assert len(analyzer._report_data) == 3

    total = sum(item['total'] for item in analyzer._report_data)
    assert total == 10

    handlers = {item['handler'] for item in analyzer._report_data}
    assert handlers == {'/api/users', '/api/products', '/api/orders'}

    for item in analyzer._report_data:
        if item['handler'] == '/api/users':
            assert item['total'] == 5
            assert item['avg_response_time'] == pytest.approx(0.2)  # (0.15+0.2+0.18+0.22+0.25)/5
        elif item['handler'] == '/api/products':
            assert item['total'] == 3
            assert item['avg_response_time'] == pytest.approx(0.4167, rel=1e-3)  # (0.4+0.35+0.5)/3
        elif item['handler'] == '/api/orders':
            assert item['total'] == 2
            assert item['avg_response_time'] == pytest.approx(1.0)  # (1.2+0.8)/2



def test_filter_by_date(sample_large_log_file):
    analyzer = LogAnalyzer()
    analyzer.file_paths = [sample_large_log_file]
    analyzer.report_type = 'average'
    analyzer.target_date = datetime.strptime("2025-06-22", "%Y-%m-%d").date()

    analyzer.process_logs()

    # /api/users и /api/orders
    assert len(analyzer._report_data) == 2

    # /api/products не попал в отчет (другая дата)
    handlers = {item['handler'] for item in analyzer._report_data}
    assert '/api/products' not in handlers

    # Проверяем общее количество записей
    total = sum(item['total'] for item in analyzer._report_data)
    assert total == 7  # 5 (users) + 2 (orders)
