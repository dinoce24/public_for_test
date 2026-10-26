from __future__ import annotations

from collections import Counter

from common import clean_rows, configure_stdout, rate


def print_bin(
    label: str,
    rows: list[dict],
    predicate,
) -> None:
    subset = [row for row in rows if predicate(row)]
    print(f"  {label:>12}: {rate(subset):>18}")


def main() -> None:
    configure_stdout()
    rows, _, _ = clean_rows()

    print("== 02 单变量分箱（只统计 status=0 退单） ==")
    print(f"总体退单率: {rate(rows)}")
    print()

    print("按库存同步延迟分箱:")
    lag_bins = [
        ("0-5 min", 0, 5),
        ("5-10 min", 5, 10),
        ("10-15 min", 10, 15),
        ("15-20 min", 15, 20),
        ("20-30 min", 20, 30),
        ("30-45 min", 30, 45),
        ("45+ min", 45, float("inf")),
    ]
    for label, low, high in lag_bins:
        print_bin(
            label,
            rows,
            lambda row, lo=low, hi=high: lo <= row["lag_min"] < hi,
        )
    print()

    print("按库存克数分箱:")
    stock_bins = [
        ("0 g", 0, 0),
        ("1-2 g", 1, 2),
        ("3-5 g", 3, 5),
        ("6-10 g", 6, 10),
        ("11-20 g", 11, 20),
        ("21-30 g", 21, 30),
    ]
    for label, low, high in stock_bins:
        print_bin(
            label,
            rows,
            lambda row, lo=low, hi=high: lo <= row["stock_g"] <= hi,
        )
    print()

    print("按站点:")
    for dept in sorted({row["pharmacy_dept"] for row in rows}):
        print_bin(
            dept,
            rows,
            lambda row, value=dept: row["pharmacy_dept"] == value,
        )
    print()

    print("按颗粒品种:")
    for granule in sorted({row["granule_type"] for row in rows}):
        print_bin(
            granule,
            rows,
            lambda row, value=granule: row["granule_type"] == value,
        )
    print()

    print("按下发小时:")
    for hour in sorted({row["dispense_dt"].hour for row in rows}):
        print_bin(
            f"{hour:02d}:00",
            rows,
            lambda row, value=hour: row["dispense_dt"].hour == value,
        )
    print()

    print("辅助检查:")
    print(
        "  状态分布: "
        + str(Counter(row["status"] for row in rows))
    )
    print(
        "  库存<=5g 且延迟<=15min 的退单: "
        f"{rate([r for r in rows if r['stock_g'] <= 5 and r['lag_min'] <= 15])}"
    )
    doses = sorted(row["dose_n"] for row in rows)
    print(
        "  处方剂数四分位: "
        f"{doses[len(doses) // 4]} / "
        f"{doses[len(doses) // 2]} / "
        f"{doses[3 * len(doses) // 4]}"
    )
    print("  注: 处方剂数与退单没有稳定单调关系，本分析不把它作为主因。")


if __name__ == "__main__":
    main()
