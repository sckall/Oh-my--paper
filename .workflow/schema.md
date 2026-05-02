# Tracker 系统字段说明与状态转换规则

> 本目录包含 Oh My Paper 项目使用的四个核心 tracker 文件，作为多 Agent 协作的交接介质。

---

## 1. paper-issues.yaml — 论文问题追踪

### 状态机

```
open → actionable → completed → cleaned
                ↘ wont-do   → reopened
```

| 状态 | 含义 | 触发条件 |
|------|------|----------|
| `open` | 被发现，尚未分类 | critique 或 reviewer 报告问题 |
| `actionable` | triage 判定需要修复 | 确认为有效问题 |
| `wont-do` | triage 判定跳过 | 问题无效或暂不处理，需附原因 |
| `completed` | 已修复 | 问题已被修复 |
| `reopened` | 再次发现 | completed 后又被发现仍存在 |
| `cleaned` | 确认清理 | 已验证修复有效，从活跃列表移除 |

### 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 格式：`OMP-NNN`（如 OMP-001） |
| `title` | string | ✅ | 问题简述，一句话 |
| `description` | string | ❌ | 详细描述 |
| `severity` | enum | ✅ | `critical` / `major` / `minor` / `trivial` |
| `status` | enum | ✅ | 当前状态（见状态机） |
| `source` | string | ❌ | 发现来源 |
| `hypothesis_id` | string | ❌ | 相关假设编号 |
| `assignee` | string | ❌ | 负责人 |
| `resolved_note` | string | ❌ | 修复说明或 wont-do 原因 |
| `created_at` | string | ✅ | ISO 8601 时间 |
| `updated_at` | string | ❌ | 最后更新时间 |

---

## 2. literature-bank.yaml — 文献库

### 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 格式：`LIT-NNN` |
| `title` | string | ✅ | 论文标题 |
| `authors` | list[string] | ✅ | 作者列表 |
| `venue` | string | ✅ | 发表 venue |
| `year` | int | ✅ | 发表年份 |
| `tags` | list[string] | ❌ | 标签 |
| `notes` | string | ❌ | 阅读笔记、关键发现、对你研究的启发 |
| `quality` | enum | ✅ | `high` / `medium` / `low` |
| `bibtex` | string | ❌ | BibTeX 条目 |
| `url` | string | ❌ | 论文链接 |
| `added_at` | string | ✅ | 收录时间 |

---

## 3. experiment-log.yaml — 实验记录

### 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 格式：`EXP-NNN` |
| `hypothesis_id` | string | ✅ | 对应假设编号（如 `H-001`） |
| `title` | string | ✅ | 实验简述 |
| `config` | map | ❌ | 实验配置/超参数 |
| `result` | string | ✅ | 实验结果描述 |
| `evidence` | string | ❌ | 证据（文件路径、日志摘要等） |
| `decision` | enum | ❌ | 实验后决策 |
| `notes` | string | ❌ | 额外说明、异常、改进思路 |
| `created_at` | string | ✅ | 实验执行时间 |

---

## 4. decision-log.yaml — 决策记录

### 决策类型

| 决策 | 触发条件 | 行动 |
|------|----------|------|
| `PROCEED` | 达标（≥ successThreshold）+ 证据充分 | 推进下一阶段，更新 tasks.json |
| `REFINE` | 接近达标（≥ 80%）或证据可修复 | 调整配置，版本 +0.1 |
| `PIVOT` | 完全不达标（< 50%）或假设被证伪 | 返回假设阶段，版本 +1.0 |

### 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 格式：`DEC-NNN` |
| `stage` | string | ✅ | 所处阶段 |
| `decision` | enum | ✅ | `PROCEED` / `REFINE` / `PIVOT` |
| `reason` | string | ✅ | 决策理由 |
| `confidence` | float | ✅ | 信心度 0.0 ~ 1.0 |
| `evidence` | string | ❌ | 支撑证据 |
| `timestamp` | string | ✅ | ISO 8601 时间 |
| `next_step` | string | ❌ | 后续行动描述 |

---

## 协作原则

1. **只追加，不覆盖** — tracker 文件只追加新记录，保留完整历史
2. **每个阶段必须有决策** — 进入下一阶段前必须记录 decision-log
3. **问题不过夜** — open 状态的问题应在当日完成 triage（actionable / wont-do）
4. **证据链必须完整** — decision 必须有 evidence 引用 experiment-log 或 paper-issues
5. **ID 连续递增** — 由写入方维护，使用最大 ID+1
