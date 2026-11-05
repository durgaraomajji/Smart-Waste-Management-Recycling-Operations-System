from app.utils.calculation_utils import center_utilization, percentage, recycling_percentage
from app.utils.csv_export import rows_to_csv


def test_recycling_percentage():
    assert recycling_percentage(250, 1000) == 25.0
    assert recycling_percentage(5, 0) == 0.0


def test_center_utilization():
    assert center_utilization(850, 1000) == 85.0


def test_percentage_rounding():
    assert percentage(1, 3) == 33.33


def test_csv_neutralises_formula_injection():
    out = rows_to_csv([{"name": "=cmd()", "kg": 5}])
    assert "'=cmd()" in out
