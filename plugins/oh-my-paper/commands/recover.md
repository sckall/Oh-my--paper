---
description: 从快照恢复项目状态，防止会话崩溃导致进度丢失
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Recovery Manager。

## 第一步：检查快照目录

```bash
ls .pipeline/memory/snapshots/ 2>/dev/null || echo "NO_SNAPSHOTS"
```

如果 `NO_SNAPSHOTS`：

> 📸 暂无快照。
> 快照会在以下时机自动创建：
> - 阶段切换前（`on-stage-transition` hook）
> - 任务完成前（`on-task-complete` hook）
> - 关键命令（/omp:write、/omp:plan 等）执行前
>
> 如果你刚初始化项目，还没有自动快照。后续操作中会自动生成。

**停止**，不要继续执行。

## 第二步：列出所有快照

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/list-snapshots.mjs" --json
```

解析 JSON 输出，提取所有快照的：
- `file` — 文件名
- `timestamp` — 创建时间
- `stage` — 当时所在阶段
- `tasks_summary` — 任务完成度
- `label` — 快照标签

## 第三步：展示快照列表并让用户选择

用 `AskUserQuestion` 展示：

> **📸 选择要恢复的快照**
>
> | # | 时间 | 阶段 | 任务进度 |
> |---|------|------|----------|
> | 1 | 2026-05-02 11:30 | experiment | 5/12 done |
> | 2 | 2026-05-01 09:15 | ideation | 3/8 done |
> | 3 | 2026-04-30 16:20 | survey | 8/8 done |
>
> 选择要恢复的快照：

选项：列出每个快照（格式：`快照 #1：2026-05-02 11:30 [experiment]`），额外加一个 `取消` 选项。

## 第四步：读取选中快照的详情

```bash
cat ".pipeline/memory/snapshots/{selected_file}"
```

解析 JSON，提取 `research_brief`、`tasks_summary`、`files` 中每个文件的预览（前 200 字符）。

## 第五步：显示恢复预览

> **📋 恢复预览：{snapshot_file}**
>
> **快照时间**：{timestamp}
> **当时阶段**：{stage}
> **任务状态**：{done}/{total} 完成
>
> **将恢复以下文件**：
> - `docs/research_brief.json` ({xxxx 字符})
> - `tasks/tasks.json` ({xxxx 字符})
> - `memory/project_truth.md` ({xxxx 字符})
> - `memory/orchestrator_state.md` ({xxxx 字符})
> - `memory/decision_log.md` ({xxxx 字符})
>
> ⚠️ **警告**：恢复将覆盖当前文件。当前未保存的修改将丢失。
>
> 是否确认恢复？

选项：
- `确认恢复` — 执行恢复
- `查看差异` — 显示快照与当前文件的详细差异
- `取消` — 中止恢复

## 第六步（可选）：查看差异

如果用户选择 `查看差异`：

对每个有差异的文件，显示：

```
## 差异：docs/research_brief.json

 快照内容（前 500 字符）：
 ---
 {snapshot preview}
 ---

 当前内容（前 500 字符）：
 ---
 {current file preview}
 ---
```

用 `AskUserQuestion` 再次询问是否恢复。

## 第七步：执行恢复

对快照 `files` 中的每个条目：

```bash
# 确保目标目录存在
mkdir -p ".pipeline/$(dirname {relPath})"

# 从快照恢复文件内容
node -e "
const fs = require('fs');
const path = require('path');
const snapshot = JSON.parse(fs.readFileSync('.pipeline/memory/snapshots/{snapshot_file}', 'utf8'));
const content = snapshot.files['{relPath}'];
if (content !== undefined) {
  fs.mkdirSync(path.dirname('.pipeline/{relPath}'), { recursive: true });
  fs.writeFileSync('.pipeline/{relPath}', content, 'utf8');
  console.log('Restored: .pipeline/{relPath}');
} else {
  console.log('Not in snapshot: .pipeline/{relPath}');
}
"
```

恢复完成后：

> ✅ **恢复完成！**
>
> 已从快照 `{snapshot_file}` 恢复 {n} 个文件。
>
> **恢复详情**：
> - docs/research_brief.json ✅
> - tasks/tasks.json ✅
> - memory/project_truth.md ✅
> - ...
>
> 建议运行 `/omp:progress` 查看当前进度。

## 第八步：创建恢复记录

在 `.pipeline/memory/recovery_log.md` 追加记录：

```markdown
## Recovery: {timestamp}

- **Snapshot**: {snapshot_file}
- **Snapshot time**: {snapshot_timestamp}
- **Recovered files**: {file_list}
- **Recovered by**: auto-detected user
```

---

## 错误处理

### 快照文件损坏

> ⚠️ 快照文件 `{file}` 无法解析（JSON 格式错误）。
> 跳过此快照，请选择其他快照。

### 快照中缺少某文件

> ⚠️ 快照中不包含 `memory/xxx.md`，该文件将不会被恢复（保持当前状态）。

### 恢复失败

> ❌ 恢复失败：`{file_path}` 写入错误。
> 部分文件可能已恢复，建议检查 `.pipeline/` 目录状态。
