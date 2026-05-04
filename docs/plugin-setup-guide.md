# OMP 插件安装与迁移指南

## 为什么需要这份指南

OMP 插件（Oh My Paper）通过项目目录下的 `plugins/oh-my-paper/` 加载，但 Claude Code 从多个配置源读取插件信息：
- `~/.claude/plugins/installed_plugins.json` — 安装记录
- `~/.claude/settings.json` — 全局配置
- `oh-my-paper/.claude/settings.json` — 项目配置
- `oh-my-paper/.claude/settings.local.json` — 项目本地配置

任一配置错误都会导致插件无法正常工作。

---

## 一、正确安装流程

### 步骤 1：确认插件文件存在

```bash
ls plugins/oh-my-paper/.claude-plugin/plugin.json
cat plugins/oh-my-paper/.claude-plugin/marketplace.json
```

### 步骤 2：安装插件（CLI 方式）

```bash
# 在项目目录下启动 Claude Code 后执行
claude plugins add --dir plugins/oh-my-paper
```

### 步骤 3：启用插件（关键步骤）

```bash
claude plugins enable omp@oh-my-paper
```

**重要**：安装后插件默认是 **disabled** 状态。必须执行 `enable` 命令才会激活。

### 步骤 4：验证

```bash
claude plugins list
# 应显示: omp@oh-my-paper — Status: ✔ enabled
```

或在 Claude Code 中输入 `/omp:guide` 验证命令是否出现。

---

## 二、多配置文件详解

### Claude Code 读取配置的优先级

1. `~/.claude/settings.json` — 全局用户配置
2. 项目目录 `.claude/settings.json` — 项目级配置
3. 项目目录 `.claude/settings.local.json` — 项目本地配置（不会提交到 git）

### 关键配置项说明

| 配置项 | 位置 | 作用 |
|--------|------|------|
| `installed_plugins.json` | `~/.claude/plugins/` | 记录已安装的插件（版本、路径、时间戳） |
| `enabledPlugins` | `settings.json` | **插件启用开关** — 插件必须在这里才能加载 |
| `extraKnownMarketplaces` | `settings.json` | 添加额外的 marketplace JSON 文件 |
| `additionalDirectories` | `settings.json` | 额外扫描的目录 |

### enabledPlugins 示例

```json
// settings.json
{
  "enabledPlugins": {
    "omp@oh-my-paper": true
  }
}
```

**插件即使安装正确，如果不在 `enabledPlugins` 里，就是 disabled 状态，命令不会出现在补全中。**

---

## 三、更新/迁移（从旧版升级）

### 快速清理命令

```bash
# 在终端（非 Claude Code 内）执行

# 1. 清空安装记录
echo '{"version":2,"plugins":{}}' > ~/.claude/plugins/installed_plugins.json

# 2. 删除缓存
rm -rf ~/.claude/plugins/cache/oh-my-paper/

# 3. 删除旧版技能
rm -rf ~/.claude/skills/omp:*
```

### 重新安装

```bash
cd /path/to/oh-my-paper
claude plugins add --dir plugins/oh-my-paper
claude plugins enable omp@oh-my-paper
```

---

## 四、插件清单格式

### 3.1 `.claude-plugin/plugin.json`

```json
{
  "name": "omp",
  "description": "Oh My Paper research harness",
  "version": "1.1.0",
  "author": { "name": "LigphiDonk" },
  "agents": ["./agents/conductor.md"],
  "commands": ["./commands/"],
  "skills": ["./skills/"]
}
```

注意：
- `agents` 必须使用显式文件路径（不能用目录）
- `commands` 和 `skills` 可以是目录路径
- `version` 必须填写

### 3.2 `marketplace.json`

```json
{
  "name": "oh-my-paper-local",
  "owner": { "name": "OMP Contributor" },
  "plugins": [
    {
      "name": "omp",
      "version": "1.1.0",
      "description": "Research pipeline automation",
      "source": "/absolute/path/to/plugins/oh-my-paper"
    }
  ]
}
```

注意：`source` 应使用**绝对路径**，不要用相对路径 `../`。

### 3.3 命令文件格式

每个命令文件（`commands/*.md`）需要 YAML frontmatter：

```markdown
---
description: 命令的简短描述，会显示在自动补全中
---

命令的详细内容...
```

`description` 字段**不能省略**，否则命令不会显示在补全中。

---

## 五、常见问题排查

### Q1: `claude plugins list` 显示插件为 "disabled"

**原因**：插件已安装但未在 `enabledPlugins` 里。

**解决**：
```bash
claude plugins enable omp@oh-my-paper
```

### Q2: 新命令不显示（如 `/omp:guide` 不出现）

排查顺序：
1. `claude plugins list` — 确认状态是 enabled 而不是 disabled
2. `claude plugins list` 查看版本是否正确（1.0.0 还是 1.1.0）
3. 检查 `installed_plugins.json` 中的版本号是否正确
4. 检查配置文件中的路径是否正确（版本号、目录名）

### Q3: 路径问题

配置文件中的路径必须正确，几个常见错误：
- 版本号写错（1.0.0 而不是 1.1.0）
- 目录名拼写错误（如 `Oh-my--paper` 双下划线）
- 使用相对路径而非绝对路径

### Q4: 命令重复出现

```bash
rm -rf ~/.claude/skills/omp:*
```

---

## 六、插件内部结构（v1.1.0）

```
oh-my-paper/
├── .claude-plugin/
│   ├── plugin.json        ← 声明 agents/commands/skills 路径
│   └── marketplace.json   ← 插件市场清单
├── agents/                ← Agent 定义文件
├── commands/              ← 命令执行层（与 skills/ 配对）
│   ├── plan.md
│   ├── survey.md
│   └── ...
└── skills/                ← 技能元数据层
    ├── omp:plan/
    │   └── SKILL.md       ← 定义 id, name, description, stages
    └── ...
```

**commands/ 与 skills/ 的关系**：

| 层 | 文件 | 作用 |
|----|------|------|
| 执行层 | `commands/*.md` | 提供实际系统提示词（中文指令） |
| 元数据层 | `skills/omp:*/SKILL.md` | 提供命令名、描述、阶段、tracker 信息 |

---

## 七、核心原则

1. **安装后必须 `enable`** — `claude plugins enable <name>` 是激活插件的命令
2. **`enabledPlugins` 是开关** — 插件不在此列表中就是 disabled 状态
3. **多配置文件同步** — 任何一层配置错误都会导致问题
4. **路径使用绝对路径** — marketplace.json 的 source 不要用相对路径
5. **版本号必须一致** — installed_plugins.json、settings.json、marketplace.json 中的版本号要统一