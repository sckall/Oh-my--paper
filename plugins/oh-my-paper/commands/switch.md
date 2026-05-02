---
description: 在多项目间切换，或列出所有项目
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Project Switcher。

## 第一步：检查 .omp.yml 是否存在

```bash
cat .omp.yml 2>/dev/null || echo "NOT_FOUND"
```

如果 `NOT_FOUND`：

> 未检测到多项目配置（`.omp.yml`）。
> 当前为单项目模式，`.pipeline/` 位于当前目录。
>
> 如需启用多项目支持，请先运行 `/omp:new-project <项目名>` 创建第一个子项目。

**停止**，不继续执行。

如果 `.omp.yml` 存在，解析 YAML 内容（直接读取文件内容，手动解析 `active_project` 和 `projects` 列表）。

## 第二步：展示项目列表并让用户选择

读取 `.omp.yml` 后，用 `AskUserQuestion` 展示：

> **📁 多项目列表**
>
> 当前活跃项目：**{active_project}**
>
> | # | 项目名 | 路径 | 主题 |
> |---|--------|------|------|
> | 1 | project-a | projects/project-a | 多模态... |
> | 2 | project-b | projects/project-b | 小样本... |
>
> 选择要切换到的项目：

选项：每个项目名作为一个选项，额外加 `取消` 选项。

## 第三步：执行切换

用户选择项目后：

1. 更新 `.omp.yml` 中的 `active_project` 字段：

```bash
node -e "
const fs = require('fs');
const yaml = fs.readFileSync('.omp.yml', 'utf8');
const updated = yaml.replace(/active_project:\s*\S+/, 'active_project: {selected_project}');
fs.writeFileSync('.omp.yml', updated, 'utf8');
console.log('Switched to: {selected_project}');
"
```

2. 提示用户：

> ✅ 已切换到项目：**{selected_project}**
>
> **下一步**：请在终端中运行：
> ```bash
> cd {project_path}
> ```
> 然后重新启动 Claude Code 会话，以加载该项目的研究上下文。

## 可选：创建 .omp.yml（首次使用）

如果 `.omp.yml` 不存在，但当前目录有 `.pipeline/`，提示用户初始化：

> 检测到当前目录有 `.pipeline/`（单项目模式）。
> 是否将其转换为多项目结构？
>
> 转换后，当前项目将成为 `projects/default/`。

选项：`是，转换为多项目` / `暂不，继续使用单项目`

如果选 `是`：

```bash
# 创建 projects/default/ 目录
mkdir -p projects/default

# 移动 .pipeline/ 到 projects/default/
mv .pipeline/ projects/default/

# 创建 .omp.yml
echo 'active_project: default
projects:
  - name: default
    path: projects/default
    topic: ""' > .omp.yml
```

---

## 错误处理

### .omp.yml 格式错误

> ⚠️ `.omp.yml` 格式异常，无法解析项目列表。
> 请手动检查该文件，或删除后重新运行 `/omp:new-project` 重建。

### 项目路径不存在

> ⚠️ 项目 `{name}` 的路径 `{path}` 不存在。
> 请检查 `.omp.yml` 中的路径是否正确，或运行 `/omp:new-project` 重新创建。
