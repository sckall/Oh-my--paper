# 风险信号目录

5 类信号的完整判定规则 + critical 信号清单 + 网络抓取细节。

## Critical 信号清单

==出现任一 critical 信号自动判定为 `predatory_suspected`==：

| Flag | 含义 | 来源 |
|---|---|---|
| `oa_but_not_in_doaj` | 声称 OA 却不在 DOAJ | DOAJ 信号 |
| `scie_discontinued` | 已被踢出 SCIE | letpub 的 sci_index_status |
| `abnormal_apc_high` | APC > 学科均值 +3σ | APC 计算 |

非 critical 信号累计 ≥ 3 也升级为 `predatory_suspected`。

## 信号 1：DOAJ 白名单细则

```python
def signal_doaj(candidate):
    in_doaj = candidate.evidence.find_doaj_check().get("in_doaj")
    doaj_seal = candidate.evidence.find_doaj_check().get("doaj_seal")
    oa_status = candidate.cost_intel.get("open_access")

    flags = []
    safety = []

    # OA 但不在 DOAJ → critical
    if oa_status == "Yes" and in_doaj is False:
        flags.append("oa_but_not_in_doaj")

    # 高质量 OA 标记
    if doaj_seal:
        safety.append("doaj_sealed")

    # Hybrid OA 不在 DOAJ 不算 flag（hybrid 本就不进 DOAJ）
    # 不写 elif，避免误升级

    return flags, safety
```

==特例==：纯订阅刊（subscription-only）不在 DOAJ 是正常的，**不打 flag**。判断 `oa_status` 必须明确是 "Yes"（OA），不能是 "No" 或 "Hybrid"。

## 信号 2：Think.Check.Submit. (TCS) 防坑清单

### 抓取 URL

```
https://thinkchecksubmit.org/journals/
```

==TCS 实际是教育资源 + 自查清单，不一定有完整期刊数据库==。

抓取策略：

1. 试 `https://thinkchecksubmit.org/journals/?search={issn}`
2. 解析返回 HTML 看是否有期刊命中
3. 如 TCS 改版无搜索接口，标 `tcs_lookup: "not_available"` + 跳过

```bash
firecrawl scrape \
  'https://thinkchecksubmit.org/journals/' \
  --formats markdown \
  --only-main-content true
```

### 判定规则

```python
in_tcs = check_tcs_recommended(issn)
if in_tcs is True:
    safety.append("tcs_recommended")
# is False 或 not_available → 不打 flag（TCS 不全）
```

## 信号 3：Beall's List archive

### 抓取 URL

Beall 2017 关博，**Wayback Machine 仍存档**：

```
https://web.archive.org/web/2017*/https://scholarlyoa.com/publishers/
https://web.archive.org/web/2017*/https://scholarlyoa.com/individual-journals/
```

### 抓取策略

1. firecrawl 抓 archive 最后快照（2017-01）
2. 解析期刊名 / 出版社清单
3. 跟当前 candidate 的 publisher / journal_name 做模糊匹配

==非精确匹配是 OK 的==——Beall list 是历史信号，不要求严格 ISSN 匹配。

```bash
firecrawl scrape \
  'https://web.archive.org/web/20170105000000*/scholarlyoa.com/individual-journals/' \
  --formats markdown
```

### 判定规则

```python
on_beall = beall_archive_match(publisher, journal_name)
if on_beall:
    flags.append("beall_legacy_match")
    # 不是 critical——只是历史标记，仅当与其他 flag 累加时升级
```

==只看出版社匹配是误伤率最大的==——如 OMICS 集团整体在 Beall 上，但旗下也有正规期刊。匹配上加 flag 不直接判定。

## 信号 4：APC 异常检测

### 数据准备

输入：`candidate.cost_intel.apc`（letpub 已抓的 APC，多种货币）

统一转 USD（用静态汇率即可，不实时拉）：

```python
GBP_USD = 1.27
EUR_USD = 1.08

apc_usd = (
    apc.get("USD")
    or apc.get("GBP", 0) * GBP_USD
    or apc.get("EUR", 0) * EUR_USD
)
```

### 学科基准

读 `apc-field-benchmarks.md` 静态表，按 letpub 的 `wos_subjects[0].category` 取 `(field_mean, field_std)`。

### 计算

```python
z_score = (apc_usd - field_mean) / field_std

if z_score > 3:
    flags.append("abnormal_apc_high")     # critical
elif z_score < -2 and apc_usd > 200:
    flags.append("abnormal_apc_low")       # 可疑：低于均值太多 + APC 不为零
elif apc_usd == 0 and oa_status == "Yes":
    safety.append("free_oa")               # ✅ 真免费 OA（钻石 OA）
```

==z_score < -2 且 APC > 200 才打 low flag==——APC = 0 是钻石 OA，是好事不是坏事。

### 缺失字段

如 `cost_intel.apc` 为空：

```python
if not apc:
    # OA 期刊缺 APC 也可疑
    if oa_status == "Yes":
        flags.append("oa_apc_unspecified")
    # 订阅刊缺 APC 是正常的，不打 flag
```

## 信号 5：letpub 预警名单（消费上游）

```python
def signal_letpub_warning(candidate):
    flags = []

    # in_warning_list: 来自 letpub-sci-journal-review v0.1.3 patched schema
    # 形态：{<year>: {in_list: bool, reason: str|None}, sci_index_status: str}

    warning_data = candidate.risk_flags.get("in_warning_list", {})
    sci_status = candidate.risk_flags.get("sci_index_status")

    # 任何年份在预警 → flag
    any_year_warning = any(
        d.get("in_list") for d in warning_data.values()
        if isinstance(d, dict)
    )
    if any_year_warning:
        flags.append("letpub_warning_list_hit")

    # SCIE 状态特别信号
    if sci_status == "Discontinued":
        flags.append("scie_discontinued")    # critical
    elif sci_status == "Under Review":
        flags.append("scie_under_review")    # 强信号但非 critical

    return flags
```

## 完整合成函数

```python
def assess_predatory_risk(candidate: CandidateJournal) -> dict:
    flags = []
    safety = []

    f, s = signal_doaj(candidate); flags += f; safety += s
    f, s = signal_tcs(candidate); flags += f; safety += s
    flags += signal_beall(candidate)
    flags += signal_apc_anomaly(candidate)
    flags += signal_letpub_warning(candidate)

    verdict = compute_verdict(flags)  # safe / warning / predatory_suspected
    risk_score = compute_risk_score(flags)  # 0.0-1.0

    return {
        "issn": candidate.identity.issn,
        "verdict": verdict,
        "risk_score": risk_score,
        "risk_flags": flags,
        "safety_signals": safety,
        "evidence": build_evidence(...),
    }
```

## 边缘案例

| 场景 | 处理 |
|---|---|
| 候选缺关键字段（如 letpub 没抓到 APC）| 信号 4 跳过，error_log 记一条 |
| TCS / Beall 网络全挂 | 跳过这两类信号，verdict 仅基于 DOAJ + APC + letpub_warning |
| 期刊 ISSN 在 DOAJ 但同名出版社在 Beall archive | 不冲突——DOAJ 是当前事实，Beall 是历史。打 `beall_legacy_match` warning 但不升 critical |
| 多 ISSN（print + electronic）| 任一在 Beall / TCS 命中即算命中 |
