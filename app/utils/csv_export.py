import csv
import io
from collections.abc import Iterable

_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")


def _safe(value):
    """Neutralise spreadsheet formula injection (CSV injection) in exported text cells."""
    if isinstance(value, str) and value.startswith(_DANGEROUS):
        return "'" + value
    return value


def rows_to_csv(rows: Iterable[dict]) -> str:
    rows = list(rows)
    buf = io.StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _safe(v) for k, v in row.items()})
    return buf.getvalue()
