---
description: 创建新子项目，自动建立独立的 .pipeline/ 目录
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Project Creator。

## 第一步：获取项目信息

用 `AskUserQuestion` 询问：

> 请输入新项目的名称（将用作目录名，如 `my-awesome-project`）：

同时询问研究主题：

> 该研究项目的主题是什么？（如：多模态医学影像分割）

## 第二步：检查 .omp.yml 是否存在

```bash
cat .omp.yml 2>/dev/null || echo "NOT_FOUND"
```

如果 `NOT_FOUND`：

创建初始 `.omp.yml`：

```bash
cat > .omp.yml << 'EOF'
# OMP Multi-Project Config
active_project: {name}
workspace: .
projects:
  - name: {name}
    path: projects/{name}
    topic: {topic}
EOF
```

否则（`.omp.yml` 已存在）：

读取内容，在 `projects:` 列表末尾追加新项目，并更新 `active_project` 为 `{name}`。

用 Node.js 实现 YAML 更新的可靠方式（避免破坏格式）：

```bash
node -e "
const fs = require('fs');
const content = fs.readFileSync('.omp.yml', 'utf8');
const lines = content.split('\n');
let inProjects = false;
const newEntry = [
  '  - name: {name}',
  '    path: projects/{name}',
  '    topic: {topic}',
];
// 找到 projects: 段落后插入
let insertIdx = -1;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].trim() === 'projects:') { inProjects = true; continue; }
  if (inProjects && lines[i].trim() && !lines[i].startsWith('  -')) { insertIdx = i; break; }
  if (inProjects && i === lines.length - 1) { insertIdx = i + 1; break; }
}
if (insertIdx >= 0) {
  lines.splice(insertIdx, 0, ...newEntry);
} else {
  lines.push(...newEntry);
}
// 更新 active_project
const updated = lines.join('\n').replace(/active_project:\s*\S+/, 'active_project: {name}');
fs.writeFileSync('.omp.yml', updated, 'utf8');
console.log('Updated .omp.yml');
"
```

## 第三步：创建项目目录和 .pipeline/ 结构

```bash
# 创建项目目录
mkdir -p "projects/{name}"

# 在项目目录下创建 .pipeline/ 结构
mkdir -p "projects/{name}/.pipeline/memory"
mkdir -p "projects/{name}/.pipeline/tasks"
mkdir -p "projects/{name}/.pipeline/docs"
mkdir -p "projects/{name}/.pipeline/.hook-events"

# 创建初始文件
echo '{"version": 1, "tasks": []}' > "projects/{name}/.pipeline/tasks/tasks.json"

echo '{
  "topic": "{topic}",
  "goal": "",
  "currentStage": "survey",
  "mode": "Legacy"
}' > "projects/{name}/.pipeline/docs/research_brief.json"

echo "# Project Truth

## 研究主题
{topic}

## 已确认决策
（待填充）
" > "projects/{name}/.pipeline/memory/project_truth.md"

# 创建空的 memory 文件
touch "projects/{name}/.pipeline/memory/orchestrator_state.md"
touch "projects/{name}/.pipeline/memory/execution_context.md"
touch "projects/{name}/.pipeline/memory/review_log.md"
touch "projects/{name}/.pipeline/memory/decision_log.md"
touch "projects/{name}/.pipeline/memory/agent_handoff.md"
touch "projects/{name}/.pipeline/memory/literature_bank.md"
touch "projects/{name}/.pipeline/memory/experiment_ledger.md"
```

## 第四步：完成提示

> ✅ **项目创建完成！**
>
> **项目名**：{name}
> **路径**：`projects/{name}/`
> **主题**：{topic}
>
> **下一步**：
> 1. 在终端运行：`cd projects/{name}`
> 2. 运行 `/omp:plan` 查看项目状态
> 3. 运行 `/omp:survey` 开始文献调研
>
> 当前活跃项目已切换为：**{name}**

选项：
- `帮我切换到该目录` — 提示用户手动 `cd`（AI 无法直接切换用户终端目录）
- `稍后自己切换`

## 可选：从现有 .pipeline/ 导入

如果当前目录有 `.pipeline/`，询问：

> 检测到当前目录有 `.pipeline/`（现有项目数据）。
> 是否将其迁移为第一个子项目（命名为 `default`）？

选项：`是，迁移现有项目` / `否，直接创建新项目`

如果选 `是`：

```bash
mkdir -p projects/default
mv .pipeline/ projects/default/
# 然后继续创建新项目...
```

---

## 错误处理

### 项目目录已存在

> ⚠️ 项目 `{name}` 的目录 `projects/{name}/` 已存在。
> 请选择其他项目名称，或先删除/重命名现有目录。

### .omp.yml 格式错误

> ⚠️ `.omp.yml` 格式异常，无法解析。
> 建议备份后删除，重新运行 `/omp:new-project` 重建配置文件。
