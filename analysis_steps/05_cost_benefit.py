from __future__ import annotations

import math

from common import (
    BLOCK_MINUTES,
    RETURN_MINUTES,
    clean_rows,
    configure_stdout,
    hours,
    is_focus,
    is_high_risk,
)


def segment_stats(rows: list[dict], predicate) -> tuple[int, int]:
    subset = [row for row in rows if predicate(row)]
    flagged = len(subset)
    prevented = sum(1 for row in subset if row["returned"])
    return flagged, prevented


def print_segment(name: str, flagged: int, prevented: int) -> None:
    block_cost = flagged * BLOCK_MINUTES
    saved = prevented * RETURN_MINUTES
    net = saved - block_cost
    print(f"{name}:")
    print(f"  拦截单量: {flagged}")
    print(f"  其中实际缺药: {prevented}")
    print(f"  阻断成本: {block_cost:.0f} min = {hours(block_cost)}")
    print(f"  避免损失: {saved:.0f} min = {hours(saved)}")
    print(f"  净收益: {net:.0f} min = {hours(net)}")


def main() -> None:
    configure_stdout()
    rows, _, _ = clean_rows()

    returns = [row for row in rows if row["returned"]]
    flagged = [row for row in rows if is_high_risk(row)]
    prevented = sum(1 for row in flagged if row["returned"])

    current_loss = len(returns) * RETURN_MINUTES
    block_all_cost = len(flagged) * BLOCK_MINUTES
    saved_if_all = prevented * RETURN_MINUTES
    net_if_all = saved_if_all - block_all_cost
    net_if_actual_only = prevented * (RETURN_MINUTES - BLOCK_MINUTES)
    residual_returns = len(returns) - prevented
    residual_loss = residual_returns * RETURN_MINUTES
    post_cost_all = block_all_cost + residual_loss
    post_cost_actual = prevented * BLOCK_MINUTES + residual_loss
    break_even_prevented = math.ceil(block_all_cost / RETURN_MINUTES)
    break_even_precision = BLOCK_MINUTES / RETURN_MINUTES

    print("== 05 成本收益测算 ==")
    print("成本参数来自 csv.pre:")
    print(f"  - 每次缺药中断损失: {RETURN_MINUTES:.0f} min")
    print(f"  - 每次提前阻断成本: {BLOCK_MINUTES:.0f} min")
    print("  - 按 7 天样本折算为“每周”")
    print()

    print("当前基准:")
    print(f"  退单数: {len(returns)}")
    print(f"  损失: {current_loss:.0f} min = {hours(current_loss)}")
    print()

    print("高风险规则拦截（国医馆库存<=3g，或其他三站延迟>15min）:")
    print(f"  拦截单量: {len(flagged)}")
    print(f"  其中实际缺药: {prevented}")
    print(f"  精度: {prevented}/{len(flagged)} = "
          f"{prevented / len(flagged):.1%}")
    print()

    print("情形 A：拦截所有高风险单")
    print(f"  阻断成本: {block_all_cost:.0f} min = {hours(block_all_cost)}")
    print(f"  避免损失: {saved_if_all:.0f} min = {hours(saved_if_all)}")
    print(f"  净收益: {net_if_all:.0f} min = {hours(net_if_all)}")
    print(f"  干预后剩余损失: {post_cost_all:.0f} min = "
          f"{hours(post_cost_all)}")
    print()

    print("情形 B：15 分钟只计实际被阻断的缺药单")
    print(f"  净收益: {net_if_actual_only:.0f} min = "
          f"{hours(net_if_actual_only)}")
    print(f"  干预后剩余损失: {post_cost_actual:.0f} min = "
          f"{hours(post_cost_actual)}")
    print()

    print("回本条件:")
    print(f"  需要阻断至少 {break_even_prevented} 单缺药即可覆盖阻断成本。")
    print(f"  等价于拦截精度 > {break_even_precision:.0%}；"
          f"当前精度 {prevented / len(flagged):.1%}，高于回本线。")
    print()

    print("分站点收益:")
    focus_flagged, focus_prevented = segment_stats(
        rows,
        lambda row: is_focus(row) and row["stock_g"] <= 3,
    )
    other_flagged, other_prevented = segment_stats(
        rows,
        lambda row: not is_focus(row) and row["lag_min"] > 15,
    )
    print_segment("  国医馆（库存<=3g）", focus_flagged, focus_prevented)
    print_segment("  其他三站（延迟>15min）", other_flagged, other_prevented)
    print()

    print("注意:")
    print("  - 以上是“若拦截后缺药全部被避免”的上限估计。")
    print("  - 40 单状态空白未计入退单损失；若其中隐藏缺药，损失更高。")
    print("  - 未折算人力单价和患者延误成本；如需金额，乘以对应时薪即可。")


if __name__ == "__main__":
    main()
