---
id: omp-paper-versioning
name: omp-paper-versioning
version: 1.0.0
description: |
  Oh My Paper 论文版本管理系统。提供自动版本归档、版本对比、分阶段快照、
  回滚操作、版本历史可视化等全套功能。确保论文修改可追溯、可对比、可回退。
stages: ["publication"]
tools: ["read_file", "write_file", "Bash"]
summary: |
  论文版本管理系统，用于管理论文草稿的版本历史、分阶段快照、版本对比和回滚操作。
primaryIntent: paper-version-management
intents: ["version", "draft", "history", "diff", "rollback"]
capabilities: ["version-control", "diff-analysis", "manifest-tracking"]
domains: ["academic"]
keywords: ["paper", "version", "draft", "diff", "rollback", "history"]
source: builtin
status: experimental
---

# OMP Paper Version Manager

## 功能概述

| 功能 | 说明 |
|------|------|
| 自动归档 | 每次 write 后自动保存版本到 drafts/ |
| 版本清单 | manifest.json 记录所有版本元数据 |
| 版本对比 | 生成版本间的 diff 报告 |
| 分章节快照 | 支持章节级别版本管理 |
| 回滚操作 | 支持回退到任意历史版本 |
| 版本历史 | 生成可视化的版本演进图 |

## 目录结构

```
paper/
├── main.tex                    # 当前版本
├── drafts/                    # 版本归档
│   └── v{N}_{timestamp}.tex   # v1_20260406_2354.tex
├── diffs/                     # diff 对比报告
│   └── v{N}_vs_v{M}.md
└── versions/
    ├── manifest.json           # 版本心脏
    └── sections/              # 章节级版本（可选）
        ├── abstract/
        ├── introduction/
        └── ...
```

## manifest.json 结构

```json
{
  "version": "1.0",
  "current": "v3",
  "total_versions": 3,
  "last_modified": "2026-04-06T23:54:00",
  "versions": [
    {
      "id": "v3",
      "date": "2026-04-06T23:54:00",
      "timestamp": "20260406_2354",
      "sections_changed": ["abstract", "method"],
      "word_count": 4820,
      "lines": 156,
      "summary": "重写了abstract，增加了方法论描述",
      "author": "OMP Agent",
      "archived_file": "v3_20260406_2354_main.tex",
      "diff_from_previous": "v2_vs_v3.md"
    },
    {
      "id": "v2",
      "date": "2026-04-03T09:15:00",
      "timestamp": "20260403_0915",
      "sections_changed": ["introduction"],
      "word_count": 4500,
      "lines": 142,
      "summary": "扩展了引言文献综述",
      "author": "OMP Agent",
      "archived_file": "v2_20260403_0915_main.tex",
      "diff_from_previous": "v1_vs_v2.md"
    },
    {
      "id": "v1",
      "date": "2026-04-01T14:30:00",
      "timestamp": "20260401_1430",
      "sections_changed": ["all"],
      "word_count": 3200,
      "lines": 98,
      "summary": "初始版本，从模板生成",
      "author": "OMP Agent",
      "archived_file": "v1_20260401_1430_main.tex",
      "diff_from_previous": null
    }
  ],
  "stats": {
    "total_words_added": 1620,
    "total_revisions": 3,
    "most_changed_section": "abstract"
  }
}
```

## 执行命令

### 1. 查看版本历史
```
/omp:version history
```
输出：所有版本的列表 + 变更摘要

### 2. 对比两个版本
```
/omp:version diff v1 v3
```
输出：v1 和 v3 之间的完整 diff 报告

### 3. 回滚到指定版本
```
/omp:version rollback v2
```
操作：
1. 备份当前 main.tex
2. 用 v2 版本替换 main.tex
3. 在 manifest 中记录回滚操作

### 4. 创建手动快照
```
/omp:version snapshot "修改了结论部分"
```
在自动归档之外，创建带注释的手动快照

### 5. 查看版本统计
```
/omp:version stats
```
输出：
- 总版本数
- 总字数变化趋势
- 各章节修改频率
- 平均每次修改字数

### 6. 生成版本演进图
```
/omp:version graph
```
输出：ASCII 版本的演进时间线

## 触发时机

### 自动触发（PostToolUse Hook）
每次检测到 paper/main.tex 或 paper/sections/*.tex 被写入时：
1. 读取 manifest.json 获取当前版本号
2. 复制 main.tex → drafts/v{N+1}_{timestamp}_main.tex
3. 如果有上一版本，生成 diff 报告
4. 更新 manifest.json

### 手动触发
用户主动调用 `/omp:version` 相关命令

## 回滚机制

### 安全回滚流程
```
rollback v2
    ↓
[确认] 备份当前 main.tex → v{current}_backup_{timestamp}.tex
    ↓
读取 v2 版本内容
    ↓
替换 main.tex
    ↓
manifest 中记录：
{
  "id": "v5",
  "type": "rollback",
  "rollback_from": "v3",
  "rollback_to": "v2",
  "date": "...",
  "summary": "回滚到 v2，原因：..."
}
```

## diff 报告格式

```markdown
# Version Diff Report
**对比版本**: v2 → v3
**生成时间**: 2026-04-06T23:54:00
**分析工具**: OMP Paper Version Manager

---

## 统计概览

| 指标 | v2 | v3 | 变化 |
|------|-----|-----|------|
| 总行数 | 142 | 156 | +14 |
| 总词数 | 4500 | 4820 | +320 |
| 总字符 | 28000 | 30100 | +2100 |

---

## 章节变更详情

### abstract
**状态**: 修改
**变化**: +23行 / -5行

```
--- v2/paper/sections/abstract.tex
+++ v3/paper/sections/abstract.tex
@@ -12,7 +12,8 @@
 遗传规律是高中生物教学中的重点与难点。
-本文提出了一种基于深度学习的系谱图生成方法。
+本文提出了一种基于知识图谱与生成式AI的系谱图虚拟实验方法。
+该方法通过构建遗传病知识图谱，为学生提供个性化反馈。
```

### introduction
**状态**: 新增
**变化**: +45行

---

## 变更类型分布

| 类型 | 数量 |
|------|------|
| 新增行 | 87 |
| 删除行 | 23 |
| 修改行 | 34 |
| **净变化** | **+98行** |

---

## 关键变更摘要

1. **abstract**: 修改了方法描述，从"深度学习"改为"知识图谱+生成式AI"
2. **introduction**: 新增了研究背景章节
3. **method**: 新增了实验设计描述
```

## 配置选项

在 `.pipeline/memory/settings.md` 中配置：

```markdown
# 论文版本管理
PAPER_VERSIONING: true          # 启用版本管理
AUTO_SNAPSHOT: true             # 自动快照
MAX_VERSIONS: 50                # 最多保留版本数（超出时删除最旧的）
KEEP_MINOR_VERSIONS: true        # 保留小版本（如 v1.1, v1.2）
DIFF_CONTEXT_LINES: 3            # diff 上下文行数
```

## 注意事项

1. **首次运行**：需要初始化 versions/ 目录和 manifest.json
2. **Hook 冲突**：如果已有 PostToolUse Hook，会自动合并
3. **大文件**：超过 1MB 的 tex 文件会被压缩存储
4. **并发安全**：写入 manifest 时使用文件锁
