from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

FOCUS_DEPT = "国医馆调配站"
LAG_THRESHOLD_MIN = 15.0
STOCK_THRESHOLD_G = 3

RETURN_MINUTES = 75.0
BLOCK_MINUTES = 15.0

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "prescriptions.csv"

Row = dict[str, Any]


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def raw_rows() -> list[Row]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def clean_rows() -> tuple[list[Row], int, int]:
    """Remove exact duplicate prescription_id rows and parse analysis fields.

    Duplicate IDs with different content are rejected rather than silently
    deduplicated, so a legitimate repeated prescription cannot be dropped.
    """
    first_by_id: dict[str, Row] = {}
    duplicate_ids: set[str] = set()
    dropped_rows = 0

    for row in raw_rows():
        pid = row["prescription_id"]
        if pid in first_by_id:
            if row != first_by_id[pid]:
                raise ValueError(
                    f"prescription_id={pid} appears with different content; "
                    "refusing to deduplicate silently."
                )
            duplicate_ids.add(pid)
            dropped_rows += 1
            continue
        first_by_id[pid] = row

    rows = [_enrich(row) for row in first_by_id.values()]
    rows.sort(key=lambda r: r["dispense_dt"])
    return rows, len(duplicate_ids), dropped_rows


def _enrich(row: Row) -> Row:
    out = dict(row)
    out["dispense_dt"] = datetime.fromisoformat(row["dispense_time"])
    out["sync_dt"] = datetime.fromisoformat(row["stock_synced_at"])
    out["lag_min"] = (
        out["dispense_dt"] - out["sync_dt"]
    ).total_seconds() / 60.0
    out["stock_g"] = int(row["stock_level"])
    out["dose_n"] = int(row["dose_packets"])
    out["status"] = row["dispense_status"]
    out["returned"] = out["status"] == "0"
    out["blank"] = out["status"] == ""
    return out


def is_focus(row: Row) -> bool:
    return row["pharmacy_dept"] == FOCUS_DEPT


def is_high_risk(row: Row) -> bool:
    """Refined operating rule found in step 03/04."""
    if is_focus(row):
        return row["stock_g"] <= STOCK_THRESHOLD_G
    return row["lag_min"] > LAG_THRESHOLD_MIN


def rate(rows: Iterable[Row]) -> str:
    items = list(rows)
    total = len(items)
    returned = sum(1 for row in items if row["returned"])
    if total == 0:
        return "0/0"
    return f"{returned}/{total} = {returned / total:.1%}"


def count_rate(rows: Iterable[Row], predicate: Callable[[Row], bool]) -> str:
    items = [row for row in rows if predicate(row)]
    return rate(items)


def status_counts(rows: Iterable[Row]) -> str:
    items = list(rows)
    counts = Counter(
        row.get("status", row.get("dispense_status", ""))
        for row in items
    )
    return (
        f"success={counts.get('1', 0)}, "
        f"return={counts.get('0', 0)}, "
        f"blank={counts.get('', 0)}, "
        f"total={len(items)}"
    )


def hours(minutes: float) -> str:
    return f"{minutes / 60.0:.1f} h"
