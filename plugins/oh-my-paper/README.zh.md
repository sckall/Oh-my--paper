# Oh My Paper (OMP) 使用指南

> AI 辅助学术研究全流程工具 — 从选刊到发表

---

## 目录

- [快速开始](#快速开始)
- [科研工作流](#科研工作流)
- [命令参考](#命令参考)
- [期刊选刊](#期刊选刊)
- [子代理](#子代理)
- [论文数据库](#论文数据库)
- [插件更新](#插件更新)
- [常见问题](#常见问题)

---

## 快速开始

```bash
# 1. 先选刊（写作前的准备）
/journal-research-orchestrator     # 英文/SCI 期刊选刊
# 或 /cn-orchestrator              # 中文核心期刊选刊

# 2. 初始化项目
/omp:setup

# 3. 文献调研
/omp:survey

# 4. 交互式教程（推荐新手先走一遍）
/omp:guide
```

---

## 科研工作流

OMP 将科研分为**两个阶段**：

```
阶段一：选题准备（确定投什么）
  /journal-research-orchestrator 或 /cn-orchestrator（选刊）
  → /omp:plan（基于目标期刊制定研究计划）

阶段二：研究写作（写什么、怎么写）
  /omp:setup → /omp:survey → /omp:ideate → /omp:experiment
  → /omp:write → /omp:review → /omp:export
```

**核心理念：先选刊再动手。** 期刊决定格式要求、方向侧重、审稿难度和发表周期。
选刊是写作前的准备阶段，不是写作中间的步骤。确定目标期刊后，再围绕期刊要求规划研究方案和实验设计。

---

## 命令参考

### 研究流程

| 命令 | 说明 |
|------|------|
| `/omp:setup` | 初始化 `.pipeline/` 研究项目结构 |
| `/omp:survey` | 文献调研 |
| `/omp:ideate` | 生成研究创新点 |
| `/omp:plan` | 制定研究计划 |
| `/omp:experiment` | 实验设计、实现和分析 |
| `/omp:write` | 论文写作冲刺 |
| `/omp:review` | 同行评审论文质量 |
| `/omp:export` | 导出论文为 PDF |
| `/omp:debate` | 多 Agent 辩论验证假设 |
| `/omp:mega` | 25 阶段研究流水线（自动驾驶/半自动/单步） |

### 辅助工具

| 命令 | 说明 |
|------|------|
| `/omp:analyze` | 扫描并分析期刊论文库 |
| `/omp:progress` | 查看项目进展 |
| `/omp:recover` | 从快照恢复项目状态 |
| `/omp:update` | 检查并更新 OMP 插件 |
| `/omp:guide` | 交互式教程（模拟项目引导） |
| `/omp:help` | 命令速查 |

### 期刊选刊（v0.3.0 新增）

| 命令 | 说明 |
|------|------|
| `/journal-research-orchestrator` | 英文/SCI 期刊选刊全流程（2 主投 + 2 备选 + 1 不建议） |
| `/cn-orchestrator` | 中文期刊选刊全流程（北核/CSSCI/CSCD/CSTPCD） |
| `/ai-journal-match` | AI 智能匹配期刊（JANE 路径） |
| `/openalex-explore` | OpenAlex 学术数据库探索 |
| `/crossref-validator` | Crossref 元数据校验 |
| `/letpub-sci-journal-review` | LetPub SCI 期刊画像（IF/分区/审稿周期/APC） |
| `/predatory-risk-check` | 掠夺刊风险筛查 |
| `/cn-discover-by-catalog` | 中文核心期刊目录发现 |
| `/cn-discover-by-paper` | 通过已发表论文反推中文期刊 |
| `/easyscholar-rank` | EasyScholar 期刊等级标签查询 |
| `/muchong-cn-journal-review` | 小木虫中文期刊投稿口碑 |
| `/nppa-validator` | 国家新闻出版署官方刊号核验 |

---

## 子代理

运行 `/omp:setup` 后，每次开启 Claude Code 会自动询问工作模式并指派对应 agent：

| Agent | 职责 |
|-------|------|
| **conductor** | 总指挥，统筹全局 |
| **literature-scout** | 文献侦察兵 |
| **experiment-driver** | 实验驾驶员 |
| **paper-writer** | 论文作家 |
| **reviewer** | 质量审查员 |

---

## 论文数据库

### 数据位置

OMP 将论文存储在项目内的 `.my-paper/` 目录：

```
.my-paper/
└── journals/
    └── computers-and-education/
        ├── metadata.yaml          # 期刊元数据
        ├── papers/                # 论文文件
        │   ├── computers-and-education-2023-001.md
        │   ├── computers-and-education-2023-001.yaml
        │   └── ...
        ├── embeddings/            # 向量索引（可选）
        └── analysis/
            └── runs/              # 分析结果
```

### 添加论文

```bash
# API 自动抓取（已配置期刊会自动执行）
/omp:journal-crawl

# 手动上传 PDF
/omp:journal-crawl --pdf ./my-paper.pdf

# 直接放入 Markdown 到 papers/ 目录
```

---

## 插件更新

```bash
# 检查更新
/omp:update --check-only

# 执行更新
/omp:update
```

### 版本历史

- **v0.3.0** (2026-05-04)：整合期刊选刊模块（17 skills），93 skills / 10 commands
- **v0.2.3** (2026-05-04)：修复 disable-model-invocation（16 个技能）
- **v0.1.0** (2026-04)：初始版本

---

## 常见问题

### Q: 为什么选刊要在研究之前？
A: 不同期刊对创新程度、实验规模、写作风格的要求不同。确定目标期刊后可以针对性设计实验，避免写完论文才发现不符合期刊要求。

### Q: 英文期刊和中文期刊选刊有什么区别？
A: `/journal-research-orchestrator` 走英文路线（OpenAlex/Crossref/LetPub），适合 SCI/SSCI 投稿；`/cn-orchestrator` 走中文路线（国家新闻出版署/小木虫/EasyScholar），适合北核/CSSCI/CSCD 投稿。

### Q: 如何选择选刊命令？
A: 如果不确定走哪个流程，直接说「帮我选刊」或「帮我做期刊调研」，OMP 会根据你的研究主题自动推荐。

### Q: 论文数据库在哪里？
A: 在项目目录的 `.my-paper/journals/` 下。每个期刊一个文件夹。

### Q: 如何更新插件？
A: 运行 `/omp:update`，或手动通过 `claude plugin install omp@oh-my-paper -s user` 重新安装。
