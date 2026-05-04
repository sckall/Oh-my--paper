---
name: cn-discover-by-paper
description: 用于中文期刊 P0 调研第一层 B 路径"从研究方向反推 venue"时使用：输入中文研究方向或关键词，调用百度学术搜索、详情页 sources 和 easyScholar 画像，把论文样本出现频次最高的期刊聚合成 CandidateJournal 候选。触发关键词：研究方向找期刊、相似论文发哪、百度学术反推、venue frequency、paper-reverse、从论文找期刊。不用于学科目录浏览（那是 cn-discover-by-catalog）、不用于小木虫口碑抓取（那是 muchong-cn-journal-review）、不绕过百度 API key 或 quota。
---

# cn-discover-by-paper

## 一句话定位

论文反推路径 = “先看相似论文都发在哪”。输入研究方向，搜索百度学术论文样本，抓详情 sources，按 venue 频次聚合候选刊。

## Method-call

`/cn-discover-by-paper(query, limit=10, paper_limit=30)`

## 工具优先级

| 场景 | 工具 | 说明 |
|---|---|---|
| 搜索论文样本 | `scripts/baidu_search.sh` | 物理复制自 academic-suite，key 从 env/Keychain 读取 |
| 抓论文详情 | `scripts/fetch_baidu_detail.py` | 取 `journal.name` 和 `sources[].anchor` |
| 抓引用文本 | `scripts/fetch_baidu_citation.py` | 备用证据脚本，非主流程必跑 |
| 候选聚合 | `scripts/discover_by_paper.py` | venue 频次排序并调用 easyScholar |

==网络请求规则==：必须使用上表中的脚本访问百度学术和 easyScholar，**禁止使用 WebFetch 工具直接请求 xueshu.baidu.com 等中文域名**（会被 WebFetch 安全验证拦截）。

## Runtime

```bash
BAIDU_API_KEY="$(security find-generic-password -s baidu -w 2>/dev/null || echo "$BAIDU_API_KEY")" \
bash plugins/journal-research-cn/skills/cn-discover-by-paper/scripts/baidu_search.sh "配电网故障定位" 0 false

python3 plugins/journal-research-cn/skills/cn-discover-by-paper/scripts/discover_by_paper.py "配电网故障定位" --limit 10 --paper-limit 30
```

## Key 和节流

- 百度 key lookup：env `BAIDU_API_KEY` → macOS Keychain service `baidu`。
- 论文详情抓取每条至少 sleep 1s，避免放大 API/站点压力。
- easyScholar 画像由 `easyscholar-rank` 自带 2 req/s token bucket。
- key 不写入仓库、日志或输出 JSON。

## 输出 Schema

```json
{
  "query": "配电网故障定位",
  "status": "ok",
  "path": "B/baidu-paper-reverse",
  "searched_paper_count": 30,
  "candidate_count": 5,
  "candidates": [
    {
      "identity": {"title_cn": "电力系统自动化", "catalog_labels": []},
      "fit_score": 1.0,
      "rank_profile": {"officialRank": {"all": {}, "select": {}}},
      "trust_level": "paper-reverse-cn",
      "supporting_paper_ids": ["baidu-paper-id"],
      "evidence": [
        {"source": "baidu-scholar-search", "trust_level": "baidu-scholar"},
        {"source": "baidu-scholar-detail", "trust_level": "baidu-scholar"}
      ]
    }
  ]
}
```

## 物理复制边界

百度脚本已复制到本 skill 下，文件头必须保留：

- 来源：`plugins/academic-suite/skills/scholar-search/scripts/`
- 复制日期：`2026-04-29`
- 边界：本 plugin 不在 runtime 依赖 academic-suite。

## Anti-pattern

- 不在没有 `BAIDU_API_KEY` 时伪造候选；返回 blocked/error。
- 不把 sources 里的数据库站点名当期刊名；脚本只取短中文 anchor 或 journal 字段。
- 不对 venue 频次做过度精调；PLAN-3 只要求 P0 可用候选池。
- 不把百度学术样本频次当最终推荐；它只是探索层证据。

## 本 skill 的 deletion-spec

- **触发删除条件**：百度学术 API 不再可用、quota 模型不适合批量 P0 调研，或 OpenAlex/中文官方论文索引提供更稳定中文 venue 反推。
- **禁用方式**：删除 `plugins/journal-research-cn/skills/cn-discover-by-paper/`，bump `journal-research-cn` minor，重生成 marketplace 并刷新 Claude/Codex cache。
- **卸载清单**：同步更新 `cn-orchestrator` 的 B 路径、README 流程图、百度 key 使用说明，以及任何调用 `discover_by_paper.py` 的外部任务模板。
