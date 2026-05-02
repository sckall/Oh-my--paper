---
id: research-literature-trace
name: Research Literature Trace
version: 1.1.0
stages: [survey, ideation]
tools: [read_file, search_project, write_file]
description: 文献收集、筛选与追踪 — 写入 .workflow/literature-bank.yaml 作为唯一真相源，同时导出 paper_bank.json 和 literature_bank.md。
---

# Research Literature Trace

文献收集、筛选与来源追溯。

## 核心原则

**`.workflow/literature-bank.yaml` 是唯一真相源。**
所有文献记录必须先写入 YAML，markdown（`literature_bank.md`）和 JSON（`paper_bank.json`）由 YAML 自动导出或手动同步。

## 约束（必须遵守）

- MUST write to: `.workflow/literature-bank.yaml`（每篇文献必须追加到 YAML）
- MUST NOT overwrite: 已有记录只追加，不覆盖
- MUST include url: 每条记录必须包含真实可查的 URL（DOI 优先）
- MUST use array: `authors` 字段必须是字符串数组
- DERIVED OUTPUT: `literature_bank.md`（markdown 表格）和 `paper_bank.json` 是导出格式，必要时可手动从 YAML 同步

## 工作流程

1. 读取 `.workflow/literature-bank.yaml` 了解已有文献（避免重复）
2. 使用 `inno-deep-research`、`paper-finder` 等搜索论文
3. 按相关性 ≥ 0.7 筛选
4. 每篇文献追加到 YAML（见下方字段要求）
5. 追加到 `literature_bank.md`（markdown 表格）
6. 生成 `gap_matrix.md` 分析研究空白

## 文献字段（写入 YAML）

```yaml
papers:
  - id: LIT-001           # 唯一标识，自动递增
    title: "论文标题"
    authors:               # 必须为数组
      - "Author One"
      - "Author Two"
    venue: "NeurIPS 2022"  # 会议/期刊/预印本
    year: 2022
    tags:                  # 标签列表
      - "prompt-engineering"
      - "llm-evaluation"
    notes: "关键发现和对你研究的启发"  # 阅读笔记
    quality: high          # high / medium / low
    url: "https://doi.org/..."   # 必须真实可查
    relevance: 0.85       # 与当前研究的相关性 0.0-1.0
    status: accepted      # screened / accepted / cited / rejected
    added_at: "2026-04-08" # ISO 日期
```

## 旧格式兼容

`paper_bank.json`（JSON）和 `literature_bank.md`（markdown）仍可写，但它们是衍生品：
- 每次新增文献后，优先更新 YAML
- JSON/markdown 可由 YAML 导出，不必手动维护

## Expected Outputs

- `.workflow/literature-bank.yaml` — 唯一真相源
- `literature_bank.md` — markdown 表格（可选，由 YAML 导出）
- `gap_matrix.md` — 研究空白分析（供 ideation 使用）
