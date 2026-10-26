from __future__ import annotations

from common import (
    FOCUS_DEPT,
    STOCK_THRESHOLD_G,
    LAG_THRESHOLD_MIN,
    clean_rows,
    configure_stdout,
    is_focus,
    is_high_risk,
    rate,
)


def main() -> None:
    configure_stdout()
    rows, _, _ = clean_rows()

    returns = [row for row in rows if row["returned"]]
    flagged = [row for row in rows if is_high_risk(row)]

    true_positive = sum(1 for row in flagged if row["returned"])
    false_positive = len(flagged) - true_positive
    false_negative = len(returns) - true_positive
    true_negative = len(rows) - true_positive - false_positive - false_negative

    print("== 04 高风险规则评估 ==")
    print(
        "规则: "
        f"{FOCUS_DEPT} 且库存<={STOCK_THRESHOLD_G}g，"
        f"或其他站点且延迟>{LAG_THRESHOLD_MIN:.0f}min"
    )
    print()

    print("混淆矩阵（正类=status 0 缺药中断）:")
    print(f"  TP={true_positive}, FP={false_positive}, "
          f"FN={false_negative}, TN={true_negative}")
    print(f"  覆盖处方: {len(flagged)}/{len(rows)} = "
          f"{len(flagged) / len(rows):.1%}")
    print(f"  召回率: {true_positive}/{len(returns)} = "
          f"{true_positive / len(returns):.1%}")
    print(f"  命中精度: {true_positive}/{len(flagged)} = "
          f"{true_positive / len(flagged):.1%}")
    print(f"  特异度: {true_negative}/{len(rows) - len(returns)} = "
          f"{true_negative / (len(rows) - len(returns)):.1%}")
    print()

    print("规则覆盖段拆分:")
    segments = [
        (
            "国医馆库存<=3g",
            lambda row: is_focus(row)
            and row["stock_g"] <= STOCK_THRESHOLD_G,
        ),
        (
            "其他三站延迟>15min",
            lambda row: not is_focus(row)
            and row["lag_min"] > LAG_THRESHOLD_MIN,
        ),
        (
            "国医馆库存>3g（未覆盖）",
            lambda row: is_focus(row)
            and row["stock_g"] > STOCK_THRESHOLD_G,
        ),
        (
            "其他三站延迟<=15min（未覆盖）",
            lambda row: not is_focus(row)
            and row["lag_min"] <= LAG_THRESHOLD_MIN,
        ),
    ]
    for label, predicate in segments:
        subset = [row for row in rows if predicate(row)]
        print(f"  {label:>26}: {rate(subset):>18}")
    print()

    print("未覆盖的退单（false negatives）:")
    for row in rows:
        if row["returned"] and not is_high_risk(row):
            print(
                f"  id={row['prescription_id']} "
                f"dept={row['pharmacy_dept']} "
                f"stock={row['stock_g']}g "
                f"lag={row['lag_min']:.0f}min "
                f"dose={row['dose_n']}"
            )
    print()

    print("对比：全场景粗规则（延迟>15min 或 库存<=5g）")
    broad = [
        row
        for row in rows
        if row["lag_min"] > LAG_THRESHOLD_MIN
        or row["stock_g"] <= 5
    ]
    broad_tp = sum(1 for row in broad if row["returned"])
    print(f"  覆盖: {len(broad)}/{len(rows)} = {len(broad) / len(rows):.1%}")
    print(f"  召回: {broad_tp}/{len(returns)} = {broad_tp / len(returns):.1%}")
    print(f"  精度: {broad_tp}/{len(broad)} = {broad_tp / len(broad):.1%}")
    print()
    print("结论: 按站点拆分后，覆盖从42%降到22%，召回仍保持90%，"
          "精度从20%提升到38%。")


if __name__ == "__main__":
    main()
