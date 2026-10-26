from __future__ import annotations

from common import (
    FOCUS_DEPT,
    clean_rows,
    configure_stdout,
    is_focus,
    rate,
)


def cell(rows: list[dict], lag_pred, stock_pred) -> str:
    subset = [row for row in rows if lag_pred(row) and stock_pred(row)]
    return rate(subset)


def main() -> None:
    configure_stdout()
    rows, _, _ = clean_rows()

    focus = [row for row in rows if is_focus(row)]
    others = [row for row in rows if not is_focus(row)]

    print("== 03 按站点分层：2x2 交叉表 ==")
    print("单元格格式: 退单数/单量 = 退单率")
    print()

    for name, group in [(FOCUS_DEPT, focus), ("其他三站", others)]:
        print(f"{name}（n={len(group)}）:")
        print(f"{'':>12} {'库存<=5g':>22} {'库存>5g':>22}")
        for lag_label, lag_pred in [
            ("延迟<=15min", lambda row: row["lag_min"] <= 15),
            ("延迟>15min", lambda row: row["lag_min"] > 15),
        ]:
            left = cell(
                group,
                lag_pred,
                lambda row: row["stock_g"] <= 5,
            )
            right = cell(
                group,
                lag_pred,
                lambda row: row["stock_g"] > 5,
            )
            print(f"{lag_label:>12} {left:>22} {right:>22}")
        print()

    print("国医馆按精确库存克数:")
    print(f"{'库存':>8} {'退单/单量':>22}")
    for stock_g in range(0, 11):
        subset = [row for row in focus if row["stock_g"] == stock_g]
        if subset:
            print(f"{stock_g:>6}g {rate(subset):>22}")
    print()

    print("其他三站按精确延迟分箱:")
    lag_bins = [
        ("0-5 min", 0, 5),
        ("5-10 min", 5, 10),
        ("10-15 min", 10, 15),
        ("15-30 min", 15, 30),
        ("30-45 min", 30, 45),
        ("45+ min", 45, float("inf")),
    ]
    for label, low, high in lag_bins:
        subset = [
            row
            for row in others
            if low <= row["lag_min"] < high
        ]
        print(f"  {label:>10}: {rate(subset):>18}")
    print()

    print("数据中的天然断层:")
    low_gap = [row for row in others if row["lag_min"] <= 13]
    high_gap = [row for row in others if row["lag_min"] >= 17]
    mid_gap = [
        row for row in others if 13 < row["lag_min"] < 17
    ]
    print(f"  其他三站延迟<=13min: {rate(low_gap)}")
    print(f"  其他三站延迟>=17min: {rate(high_gap)}")
    print(f"  其他三站延迟14-16min: {rate(mid_gap)}（本数据为空）")
    print()

    print("分层结论:")
    print(
        "  - 其他三站: 新鲜数据下即使库存<=5g也无退单；"
        "延迟>15min后无论库存高低，退单率都在32%-38%。"
    )
    print(
        "  - 国医馆: 库存<=3g 退单率65.6%；4-5g为0/20；"
        ">5g仅0.5%；与同步延迟基本无关。"
    )
    print(
        "  - 因此不能在全院用一个统一的“低库存”或“延迟”阈值，"
        "必须按站点分型。"
    )


if __name__ == "__main__":
    main()
