---
description: 列出期刊库分类，选择某类或某篇文章进行分析
---

# /omp:analyze — 期刊分析入口

> 所有选择步骤必须使用 AskUserQuestion 工具。

## 第一步：扫描并展示期刊列表

读取 `.my-paper/journals/*/metadata.yaml` 获取所有期刊信息：

- 每个期刊的 `name`、`impact_factor`、`paper_count`、`last_updated`
- 若无 `metadata.yaml`，使用目录名作为 fallback
- 若无 `.my-paper/journals/`，用 AskUserQuestion 问是否创建

使用以下格式展示：

```
📚 期刊库分类列表
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID                        期刊名称             论文数  IF
─────────────────────────────────────────────────────
computers-and-education   Computers & Ed.      5     11.9
```

## 第二步：一次性询问所有选项

**一次 AskUserQuestion 完成选择**，不要分步问：

> 请选择分析目标：  
> 1. 📂 整个期刊：**{期刊名称}**  
> 2. 📄 文章：**{期刊名称}** — 列出该期刊文章，选一篇分析  
> 3. ➕ 新增期刊分类 — 创建新目录  
> q. 退出

## 第三步：分支处理

### A) 分析整个期刊

1. **读取数据**：直接读取 `papers/*.yaml` 和 `papers/*.md`，无需 bash/python 解析
2. **分析维度**（缺省全做）：
   - 标题与行文风格 — 标题长度、结构、高频词、章节模式
   - 选题偏好 — 研究方向、热点归纳
   - 实证性倾向 — 实证/理论比例、方法论特点
   - 创新性特征 — 创新模式总结
   - 生成期刊画像 → `analysis/journal_profile.md`
   - 生成写作指南 → `analysis/style_guide.md`
3. **保存结果**到 `analysis/` 目录
4. **完成后**一次性 AskUserQuestion：
   > 完成！接下来：查看画像 | 查看指南 | 应用到项目 | 继续分析 | 完成

### B) 分析指定文章

1. 读取 `papers/*.yaml`，展示文章列表
2. 用户选中后，读取 `.md` 全文进行分析
3. 深度分析维度：摘要、方法论、实验、结果、贡献、局限性
4. 保存到 `analysis/papers/{paper_id}_analysis.md`

### C) 新增期刊分类

一次性 AskUserQuestion 收集：
> 期刊英文名称、期刊 ID（kebab-case）、出版社（可选）

然后创建目录和 `metadata.yaml`：
```bash
mkdir -p ".my-paper/journals/{id}/papers" \
        ".my-paper/journals/{id}/analysis" \
        ".my-paper/journals/{id}/embeddings"
```

## 错误处理

| 错误场景 | 处理方式 |
|----------|---------|
| `.my-paper/journals/` 不存在 | AskUserQuestion：是否创建？ |
| 期刊为空的 papers/ 目录 | AskUserQuestion：返回上级或创建示例 |
| YAML 解析失败 | 用 grep/sed 兜底读取 |
| 分析过程中任何步骤失败 | 明确提示并提供重试/返回选项 |

## 完成

分析完成后更新 `metadata.yaml` 中的 `last_updated` 字段。
