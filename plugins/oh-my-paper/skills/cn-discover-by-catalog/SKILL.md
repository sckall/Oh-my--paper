---
name: cn-discover-by-catalog
description: 用于中文期刊 P0 调研第一层 A 路径"按学科 + 收录目录浏览"时使用：下载/解析 PKU 北核、CSSCI、CSCD、CSTPCD 4 表 PDF，并用 ncpssd 学科检索扩召回，输出 trust_level=catalog-cn 的 CandidateJournal 候选。触发关键词：按学科找期刊、北大核心目录、CSSCI 目录、CSCD 目录、CSTPCD 目录、ncpssd、catalog discovery、目录白名单。不用于自由研究方向语义反推（那是 cn-discover-by-paper）、不用于等级画像（那是 easyscholar-rank）、不用于合法性/CN 号校验（那是 nppa-validator）。
---

# cn-discover-by-catalog

## 一句话定位

目录路径 = “先翻正规名单”。输入学科名，先从国内核心目录白名单找候选，再用 ncpssd 学科检索扩召回。

## Method-call

`/cn-discover-by-catalog(subject, limit=20)`

## 工具优先级

| 场景 | 工具 | 说明 |
|---|---|---|
| 4 表下载 | `scripts/download_catalogs.sh` | curl 直链下载，CSTPCD 二跳 best-effort |
| PDF 解析 | `scripts/parse_catalogs.py` | `pdfplumber` 表格优先，文本抽取兜底 |
| 学科扩召回 | `scripts/ncpssd_subject_query.py` | GBK 表达式 base64 landing URL + `/searchHandler/search` JSON rows；HTML 解析保留为兜底 |
| 主入口 | `scripts/discover_by_catalog.py` | merge 目录候选和 ncpssd 频次候选 |

## Runtime

```bash
bash plugins/journal-research-cn/skills/cn-discover-by-catalog/scripts/download_catalogs.sh
python3 plugins/journal-research-cn/skills/cn-discover-by-catalog/scripts/parse_catalogs.py
python3 plugins/journal-research-cn/skills/cn-discover-by-catalog/scripts/discover_by_catalog.py "经济学" --limit 20
```

ncpssd smoke：

```bash
python3 plugins/journal-research-cn/skills/cn-discover-by-catalog/scripts/test_ncpssd.py "经济学"
```

## 4 表来源

| Catalog | File | 处理策略 |
|---|---|---|
| PKU 北核 2023 | `data/catalogs/pku-core-2023.pdf` | 必须下载成功 |
| CSSCI 2023-2024 | `data/catalogs/cssci-2023-2024.pdf` | 必须下载成功 |
| CSCD 2023-2024 | `data/catalogs/cscd-2023-2024.pdf` | 必须下载成功 |
| CSTPCD 2024 | `data/catalogs/cstpcd-2024.pdf` | best-effort；失败时写 `references/cstpcd-mirrors.md` |

## 输出 Schema

```json
{
  "query": "经济学",
  "status": "ok",
  "path": "A/catalog+ncpssd",
  "candidate_count": 20,
  "candidates": [
    {
      "identity": {
        "title_cn": "经济研究",
        "issn": "0577-9154",
        "catalog_labels": ["pku", "cssci"]
      },
      "fit_score": 0.75,
      "trust_level": "catalog-cn",
      "evidence": [
        {"source": "pku-catalog", "trust_level": "catalog-cn"},
        {"source": "cssci-catalog", "trust_level": "catalog-cn"}
      ]
    }
  ]
}
```

## 解析边界

- `merged.json` 以中文刊名 normalize 后去重。
- 多目录收录合并到 `catalog_labels`，不覆盖原始 `catalog_entries`。
- `pdfplumber` 缺失时脚本明确提示安装，不静默降级成空结果。
- ncpssd landing URL 的查询表达式必须先 GBK 编码再 base64；当前站点的实际结果来自 `/searchHandler/search` POST JSON rows，HTML 解析作为页面结构兜底。

## Anti-pattern

- 不把 CSTPCD best-effort 下载失败当作整条中文路线失败。
- 不把 ncpssd 频次候选当目录收录；它的证据源是 `ncpssd-subject`。
- 不用字符串拼接硬猜 ISSN；只接受 PDF 或页面附近可见 ISSN。
- 不在 `data/catalogs/` 写手工伪造目录。

## 本 skill 的 deletion-spec

- **触发删除条件**：四表公开 PDF 全部停止可访问且无合法镜像，或 easyScholar/官方接口提供稳定等价目录全集，或项目切换到机构订阅数据库并取消公开目录路径。
- **禁用方式**：删除 `plugins/journal-research-cn/skills/cn-discover-by-catalog/`，bump `journal-research-cn` minor，重生成 marketplace 并刷新 Claude/Codex cache。
- **卸载清单**：同步更新 `cn-orchestrator` 的 A 路径、README 流程图、`_shared/adapter_utils.py` 中仅目录路径使用的 helper、以及 `references/cstpcd-mirrors.md` 的后续维护说明。
