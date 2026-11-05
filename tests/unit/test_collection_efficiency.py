from app.utils.calculation_utils import average, collection_efficiency, vehicle_utilization


def test_efficiency_excludes_cancelled():
    assert collection_efficiency(completed=8, total=12, excluded=2) == 80.0


def test_efficiency_no_requests():
    assert collection_efficiency(0, 0) == 0.0


def test_average_handles_empty():
    assert average([]) == 0.0 and average([10, 20]) == 15.0


def test_vehicle_utilization_load_factor():
    # 2 trips x 1000 kg capacity, 1500 kg collected -> 75 %
    assert vehicle_utilization(1500, 1000, 2) == 75.0
    assert vehicle_utilization(10, 0, 0) == 0.0
