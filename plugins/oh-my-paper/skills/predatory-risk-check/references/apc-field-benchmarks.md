# APC 学科基准（年度刷新）

各学科 APC（USD）均值 + std，用于异常检测的 z-score 计算。

==这是静态参考表，不实时抓==。年度（每年 Q1）人工刷新一次。

## 当前数据（2026-04）

来源：DOAJ 公开 OA 期刊 APC 字段聚合 + Springer/Elsevier 官方价目（2024-2025 数据综合）。

| 学科大类（letpub `wos_subjects[0].category` 命名）| Mean USD | Std USD | 备注 |
|---|---:|---:|---|
| **MULTIDISCIPLINARY SCIENCES** | 2800 | 1800 | Nature Comms / Sci Rep / PLOS ONE 拉高均值 |
| **CHEMISTRY, MULTIDISCIPLINARY** | 2500 | 1200 | |
| **CHEMISTRY, PHYSICAL** | 2400 | 1100 | |
| **MATERIALS SCIENCE, MULTIDISCIPLINARY** | 2300 | 1300 | |
| **PHYSICS, APPLIED** | 2200 | 1000 | |
| **PHYSICS, MULTIDISCIPLINARY** | 2400 | 1200 | |
| **ENGINEERING, ELECTRICAL & ELECTRONIC** | 1800 | 900 | IEEE 期刊拉低均值 |
| **COMPUTER SCIENCE, ARTIFICIAL INTELLIGENCE** | 2000 | 1100 | |
| **COMPUTER SCIENCE, INFORMATION SYSTEMS** | 1900 | 1000 | |
| **MEDICINE, GENERAL & INTERNAL** | 3000 | 1500 | NEJM / JAMA / Lancet 拉高 |
| **ONCOLOGY** | 2900 | 1400 | |
| **BIOCHEMISTRY & MOLECULAR BIOLOGY** | 2700 | 1300 | |
| **CELL BIOLOGY** | 2900 | 1500 | |
| **NEUROSCIENCES** | 2800 | 1400 | |
| **PHARMACOLOGY & PHARMACY** | 2600 | 1200 | |
| **MICROBIOLOGY** | 2500 | 1100 | |
| **ENVIRONMENTAL SCIENCES** | 2400 | 1200 | |
| **ENERGY & FUELS** | 2700 | 1400 | Cell 类掠夺刊偏多 |
| **ECONOMICS** | 1800 | 1500 | std 大——商科 OA 不普及 |
| **MANAGEMENT** | 1900 | 1700 | std 大 |
| **DEFAULT (未匹配学科)** | 2300 | 1300 | fallback |

## 用法

```python
def get_field_benchmark(wos_category: str) -> tuple[float, float]:
    """返回 (mean, std)，未匹配则返回 DEFAULT"""
    return APC_FIELD_BENCHMARKS.get(wos_category.upper(), (2300, 1300))
```

## 解读 z-score

| z-score 范围 | 解读 | 动作 |
|---|---|---|
| `> 3` | 异常高（> 99.7 percentile）| `abnormal_apc_high`（critical）|
| `2 ~ 3` | 偏高（top 5%）| 不打 flag，但记 `note: high_apc_borderline` |
| `-2 ~ 2` | 正常区间 | 无 flag |
| `< -2 且 apc > 200` | 异常低（疑似 hijacked / lowballer）| `abnormal_apc_low`（warning）|
| `apc == 0` | 钻石 OA | `safety: free_oa` |

## 已知问题

### 学科映射

letpub 的 `wos_subjects[0].category` 偶发与上表大写格式不完全一致。匹配前 `.upper()` 兜底。

### 期刊跨学科

候选期刊跨多个学科（如 Nature Comms 跨多领域）时，按第一学科匹配。==这可能导致误判==：

- Nature Comms 第一学科 MULTIDISCIPLINARY → benchmark mean $2800
- 实际 APC ~$6790 → z-score ≈ 2.2，落在 `borderline`
- 不打 flag（接近临界但未触发）

如要更精确，可对所有 `wos_subjects` 求加权平均 benchmark，但 v0.1 不做这层复杂度。

### 货币转换

汇率年度更新即可，不要实时拉：

```python
GBP_USD = 1.27   # 2026-04 中位
EUR_USD = 1.08   # 2026-04 中位
```

## 维护

==每年 Q1 刷新一次==。来源建议：

1. DOAJ API 大批拉 OA 期刊 APC 字段 → 按 letpub wos_subjects 分组聚合
2. Springer / Elsevier / Wiley 官方公布的 OA 价目（如 Springer 的 OA Journal List CSV）
3. 抽样 100 个领域代表期刊验证

刷新后在本文件顶部更新 "当前数据 (YYYY-MM)" 和数据来源段。
