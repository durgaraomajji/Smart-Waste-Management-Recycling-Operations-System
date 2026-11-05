"""Pure calculation helpers (no DB access) - formulas are documented in docs/calculation_formulas.md."""
from collections.abc import Iterable


def percentage(part: float, whole: float, digits: int = 2) -> float:
    """part / whole x 100, returning 0.0 when whole is zero."""
    if not whole:
        return 0.0
    return round(part / whole * 100, digits)


def recycling_yield(recycled_output_kg: float, input_kg: float) -> float:
    """Recycling yield % = recycled output / input x 100."""
    return percentage(recycled_output_kg, input_kg)


def processing_loss_pct(loss_kg: float, input_kg: float) -> float:
    return percentage(loss_kg, input_kg)


def collection_efficiency(completed: int, total: int, excluded: int = 0) -> float:
    """Collection efficiency % = completed / (total - cancelled/rejected) x 100."""
    return percentage(completed, total - excluded)


def average(values: Iterable[float], digits: int = 2) -> float:
    vals = list(values)
    return round(sum(vals) / len(vals), digits) if vals else 0.0


def vehicle_utilization(collected_kg: float, capacity_kg: float, trips: int) -> float:
    """Average load factor % = collected / (capacity x trips) x 100."""
    return percentage(collected_kg, capacity_kg * trips) if capacity_kg and trips else 0.0


def center_utilization(current_load_kg: float, daily_capacity_kg: float) -> float:
    return percentage(current_load_kg, daily_capacity_kg)


def recycling_percentage(total_recycled_kg: float, total_collected_kg: float) -> float:
    """Recycling % = total recycled / total collected x 100."""
    return percentage(total_recycled_kg, total_collected_kg)
