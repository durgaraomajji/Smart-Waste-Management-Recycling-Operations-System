from app.utils.calculation_utils import processing_loss_pct, recycling_yield


def test_yield_percentage():
    assert recycling_yield(80, 100) == 80.0
    assert recycling_yield(33.333, 100) == 33.33


def test_yield_zero_input_is_safe():
    assert recycling_yield(10, 0) == 0.0


def test_loss_pct():
    assert processing_loss_pct(5, 50) == 10.0
