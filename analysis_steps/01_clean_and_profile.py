from __future__ import annotations

from collections import Counter

from common import (
    CSV_PATH,
    clean_rows,
    configure_stdout,
    raw_rows,
    status_counts,
)


def main() -> None:
    configure_stdout()

    raw = raw_rows()
    rows, duplicate_groups, dropped_rows = clean_rows()

    print("== 01 数据清洗与基础口径 ==")
    print(f"源文件: {CSV_PATH}")
    print(f"原始行数: {len(raw)}")
    print(f"完全重复的 prescription_id 组数: {duplicate_groups}")
    print(f"删除的重复行数: {dropped_rows}")
    print(f"去重后处方数: {len(rows)}")
    print()

    print("原始状态分布:")
    print(f"  {status_counts(raw)}")
    print("去重后状态分布:")
    print(f"  {status_counts(rows)}")
    print()

    print("关键字段缺失检查（去重后）:")
    for field in [
        "prescription_id",
        "dispense_time",
        "stock_synced_at",
        "pharmacy_dept",
        "granule_type",
        "stock_level",
        "dose_packets",
        "dispense_status",
    ]:
        missing = sum(1 for row in rows if row.get(field, "") == "")
        print(f"  {field}: {missing}")
    print()

    print("时间字段:")
    print(f"  dispense_time 范围: {min(r['dispense_dt'] for r in rows)}")
    print(f"  stock_synced_at 范围: {min(r['sync_dt'] for r in rows)}")
    print(
        "  说明: dispense_time 为 +08:00，stock_synced_at 为 UTC；"
        "Python datetime 相减会自动统一时区。"
    )
    print(
        "  同步延迟 lag_min 范围: "
        f"{min(r['lag_min'] for r in rows):.0f} ~ "
        f"{max(r['lag_min'] for r in rows):.0f} 分钟"
    )
    print(
        "  负延迟行数: "
        f"{sum(1 for r in rows if r['lag_min'] < 0)}"
    )
    print()

    print("分类字段分布（去重后）:")
    for field in ["pharmacy_dept", "granule_type"]:
        counts = Counter(row[field] for row in rows)
        print(f"  {field}:")
        for value, count in counts.most_common():
            print(f"    {value}: {count}")
    print()

    print("口径提醒:")
    print("  - dispense_status=0 记为缺药中断/退单；1 为成功；空为状态未回传。")
    print("  - stock_level 单位为克；dose_packets 单位为剂数，两者不能直接相减。")
    print("  - 本步骤只做清洗和口径检查，不写入或修改源 CSV。")


if __name__ == "__main__":
    main()
