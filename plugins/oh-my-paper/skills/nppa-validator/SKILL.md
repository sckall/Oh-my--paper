---
name: nppa-validator
description: 用于中文期刊 P0 调研按需合法性校验时使用：用户问"这刊合法吗""CN 号是什么""新闻出版署能查到吗"时，访问 NPPA/国家新闻出版署公开页面，尝试解析 CN 号、ISSN、主管单位、主办单位和类别；若验证码或结构变化触发，返回 captcha_required + manual_url，不绕过验证码。触发关键词：CN 号、新闻出版署、NPPA、期刊合法性、刊号查询、官方期刊身份、是不是正规期刊、水刊鉴别。不用于默认候选生成（那是 cn-orchestrator A/B 路径）、不用于等级画像（那是 easyscholar-rank）、不用于社区口碑（那是 muchong-cn-journal-review）。
---

# nppa-validator

## 一句话定位

NPPA 校验 = “官方身份查验”。只在用户关心合法性、CN 号或期刊身份时调用，不进入每次默认 P0 主流程。

## Method-call

`/nppa-validator(journal_name)`

## Runtime

```bash
python3 plugins/journal-research-cn/skills/nppa-validator/scripts/test_nppa.py "经济研究"
python3 plugins/journal-research-cn/skills/nppa-validator/scripts/nppa_validate.py "经济研究"
```

## 行为边界

1. 请求 NPPA 公开页面。
2. 页面可解析时输出 `status=ok` 和 `official_identity`。
3. 页面不可自动解析、触发验证码或访问失败时输出 `status=captcha_required`。
4. 调用方把 `manual_url` 交给用户人工核验。

本 skill 不做验证码识别、不模拟登录、不使用非公开接口。

==网络请求规则==：必须使用 Runtime 段中的 Python 脚本访问 NPPA 页面，**禁止使用 WebFetch 工具直接请求 nppa.gov.cn**（中文政府域名会被 WebFetch 安全验证拦截）。若脚本不可用，改用 curl：

```bash
curl -s -A 'Mozilla/5.0' 'https://www.nppa.gov.cn/bsfw/jggs/cbwzy/'
```

## 输出 Schema

```json
{
  "query": "经济研究",
  "status": "ok",
  "official_identity": {
    "title_cn": "经济研究",
    "cn_number": "CN11-1081/F",
    "issn": "0577-9154",
    "supervising_org": "中国社会科学院",
    "host_org": "中国社会科学院经济研究所",
    "publisher": "经济研究杂志社",
    "category": "期刊"
  },
  "manual_url": "https://www.nppa.gov.cn/bsfw/jggs/cbwzy/",
  "evidence": [
    {"source": "nppa-publication-query", "trust_level": "official-cn"}
  ]
}
```

验证码或结构变化时：

```json
{
  "query": "经济研究",
  "status": "captcha_required",
  "manual_url": "https://www.nppa.gov.cn/bsfw/jggs/cbwzy/",
  "evidence": [
    {"source": "nppa-publication-query", "trust_level": "official-cn"}
  ]
}
```

## Anti-pattern

- 不把 `captcha_required` 当失败；它是合法的人工核验返程。
- 不绕验证码、不使用付费代查、不存储用户查询历史。
- 不把小木虫或 easyScholar 的 CN 字段当官方 NPPA 结论。
- 不在没有用户合法性诉求时批量打 NPPA。

## 本 skill 的 deletion-spec

- **触发删除条件**：NPPA 页面长期强验证码导致自动查询无意义，或官方发布稳定开放 API/MCP 取代 HTML 页面解析。
- **禁用方式**：删除 `plugins/journal-research-cn/skills/nppa-validator/`，bump `journal-research-cn` minor，重生成 marketplace 并刷新 Claude/Codex cache。
- **卸载清单**：同步更新 `cn-orchestrator` 的合法性路由、README 工具优先级、相关 P0 知识库中“CN 号校验”段落，以及任何引用 `nppa_validate.py` 的 task contract。
