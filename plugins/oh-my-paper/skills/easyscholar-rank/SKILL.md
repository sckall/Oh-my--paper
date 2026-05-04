---
name: easyscholar-rank
description: 用于中文期刊 P0 调研第二层"等级标签/收录画像"时使用：输入中文或英文刊名，调用 easyScholar open API，保留 officialRank.all/select 原始字段并提取北大核心、CSSCI、CSCD、CSTPCD、AMI、FMS 等标签；key 从 EASYSCHOLAR_SECRET_KEY 或 macOS Keychain service easyscholar 读取，限速 2 req/s。触发关键词：easyscholar、期刊等级、北核 CSSCI 标签、官方收录画像、rank profile、journal rank、刊物等级查询。不用于论文候选生成（那是 cn-discover-by-paper）、不用于投稿口碑（那是 muchong-cn-journal-review）、不用于官方合法性校验（那是 nppa-validator）。
---

# easyscholar-rank

## 一句话定位

easyScholar 画像层 = “国内等级标签体检”。输入刊名，输出官方收录画像和 normalized labels，供 orchestrator 决策矩阵使用。

## Method-call

`/easyscholar-rank(publication_name, raw=false)`

## Runtime

```bash
EASYSCHOLAR_SECRET_KEY="$(security find-generic-password -s easyscholar -w 2>/dev/null || echo "$EASYSCHOLAR_SECRET_KEY")" \
python3 plugins/journal-research-cn/skills/easyscholar-rank/scripts/test_rank.py "经济研究"

python3 plugins/journal-research-cn/skills/easyscholar-rank/scripts/easyscholar_rank.py "经济研究"
```

## API 协议

```text
GET https://www.easyscholar.cc/open/getPublicationRank?secretKey=<KEY>&publicationName=<刊名>
```

Key lookup:

1. env `EASYSCHOLAR_SECRET_KEY`
2. macOS Keychain service `easyscholar`
3. 缺失时返回 `status=blocked`，不写假数据

## 输出 Schema

```json
{
  "query": "经济研究",
  "status": "ok",
  "code": 200,
  "msg": "SUCCESS",
  "rank_profile": {
    "customRank": {},
    "officialRank": {"all": {}, "select": {}},
    "field_count": 37,
    "catalog_labels_detected": {
      "pku": true,
      "cssci": true,
      "cscd": false,
      "cstpcd": false,
      "ami": false,
      "fms": false
    }
  },
  "evidence": [
    {"source": "easyscholar-open-api", "trust_level": "rank-cn"}
  ]
}
```

## 字段映射

完整字段说明见 `references/easyscholar-fields.md`。本 adapter 的原则：

- `officialRank` 原样保留，避免字段随 API 增加时丢失。
- `catalog_labels_detected` 只做 conservative alias detection。
- `field_count` 统计 flattened `officialRank` 字段数量，验收目标是 37+ 字段画像。
- API 返回 `code != 200` 时结构化返回错误，调用方不得把错误当空标签。

## Anti-pattern

- 不在仓库、README、日志或输出里写 secret key。
- 不把 easyScholar 标签当投稿难度；等级只是一列画像。
- 不把 `customRank` 当官方等级；官方等级来自 `officialRank`。
- 不在批量流程绕过 2 req/s 限速。

## 本 skill 的 deletion-spec

- **触发删除条件**：easyScholar open API 停止服务、字段授权不再覆盖中文核心目录，或官方公开接口提供同等 rank profile 且更稳定。
- **禁用方式**：删除 `plugins/journal-research-cn/skills/easyscholar-rank/`，bump `journal-research-cn` minor，重生成 marketplace 并刷新 Claude/Codex cache。
- **卸载清单**：同步更新 `cn-orchestrator` 第二层画像表、`cn-discover-by-paper` 的 rank enrichment、README 工具优先级、以及 `references/easyscholar-fields.md` 的维护说明。
