# 缺药中断分析代码（可检查版）

本文件夹把分析过程拆成 5 个可单独运行的步骤。只使用 Python 标准库，不依赖 pandas，也不会修改 `prescriptions.csv`。

## 文件说明

| 文件 | 作用 |
|---|---|
| `common.py` | 公共口径：读取 CSV、去重、解析时间、计算 `lag_min`、定义高风险规则 |
| `01_clean_and_profile.py` | 数据清洗与字段检查：重复行、缺失值、状态分布、时间范围 |
| `02_univariate_bins.py` | 单变量分箱：同步延迟、库存克数、站点、品种、小时 |
| `03_department_stratification.py` | 关键分层：国医馆与其他三站的 2x2 交叉表、精确库存/延迟分布 |
| `04_risk_rule_evaluation.py` | 高风险规则评估：覆盖、召回、精度、未覆盖退单 |
| `05_cost_benefit.py` | 按 `csv.pre` 的 75/15 分钟成本口径测算收益 |

## 运行顺序

在项目根目录执行：

```powershell
python analysis_steps\01_clean_and_profile.py
python analysis_steps\02_univariate_bins.py
python analysis_steps\03_department_stratification.py
python analysis_steps\04_risk_rule_evaluation.py
python analysis_steps\05_cost_benefit.py
```

如果 Windows 终端中文乱码，先执行 `chcp 65001`。

## 关键口径

- **去重**：按 `prescription_id` 去重，但只删除完全相同的重复行；同一 ID 内容不同会直接报错，避免误删。
- **退单**：`dispense_status=0` 视为缺药中断/退单；`1` 为成功；空字符串为“状态未回传”，单独统计，不混进退单率。
- **同步延迟**：`lag_min = dispense_time - stock_synced_at`。`dispense_time` 是 `+08:00`，`stock_synced_at` 是 UTC，代码用带时区的时间相减自动换算。
- **库存单位**：`stock_level` 是克；`dose_packets` 是剂数，二者不能直接相减。代码只把库存克数当作经验风险水位。
- **成本**：来自 `csv.pre`，每次缺药中断约 75 分钟，每次提前阻断约 15 分钟。

## 预期结果（用于核对）

清洗：
- 原始 1045 行
- 50 组完全重复 `prescription_id`，删除 50 行
- 去重后 995 单
- 原始状态：成功 904、退单 97、空白 44
- 去重后状态：成功 862、退单 93、空白 40

总体：
- 退单率：93/995 = 9.3%

分层：
- 国医馆库存 <=3g：21/32 = 65.6%
- 国医馆库存 4-5g：0/20
- 国医馆库存 >5g：1/215 = 0.5%
- 其他三站延迟 <=15min：8/541 = 1.5%
- 其他三站延迟 >15min：63/187 = 33.7%
- 其他三站新鲜数据且库存 <=5g：0/111

高风险规则：
```text
国医馆且库存 <=3g
或
其他三站且同步延迟 >15min
```

- 命中 219/995 = 22.0%
- 捕获退单 84/93 = 90.3%
- 精度 84/219 = 38.4%

成本（按 7 天样本折算为每周）：
- 当前损失：93 × 75 = 6975 min ≈ 116.2 h
- 全部拦截成本：219 × 15 = 3285 min ≈ 54.8 h
- 避免损失：84 × 75 = 6300 min = 105.0 h
- 净收益（保守）：3015 min ≈ 50.2 h
- 净收益（15 分钟只计实际缺药）：5040 min = 84.0 h
- 回本所需阻断单数：ceil(3285/75) = 44 单

## 注意事项

- 这是观察性分析，不能仅凭相关性证明因果；建议用试点前后对照验证。
- 国医馆 `4-5g` 组只有 20 单，结论需要更多样本确认。
- `dose_packets` 与库存克数单位不同，若要精确判断“库存可支撑多少剂”，还需要补充“单剂颗粒用量（g/剂）”或处方明细。
- 40 单状态空白未计入退单损失，若其中隐藏缺药，实际损失会更高。
