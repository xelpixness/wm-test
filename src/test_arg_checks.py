import pytest
import argparse
from datetime import date
from arg_checks import check_file_access, check_date, check_report_type, AVAILABLE_REPORTS

@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")
    return file_path



def test_check_file_access_valid(temp_file):
    assert check_file_access(str(temp_file)) == str(temp_file)

def test_check_file_access_not_exists():
    with pytest.raises(argparse.ArgumentTypeError):
        check_file_access("nonexistent_file.txt")

def test_check_file_access_directory(tmp_path):
    with pytest.raises(argparse.ArgumentTypeError):
        check_file_access(str(tmp_path))



def test_check_date_valid():
    assert check_date("2025-22-06") == date(2025, 6, 22)

def test_check_date_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        check_date("2025/22/06")



def test_check_report_type_valid():
    for report in AVAILABLE_REPORTS:
        assert check_report_type(report) == report

def test_check_report_type_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        check_report_type("invalid_report")