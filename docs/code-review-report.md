# oh-my-paper 代码质量审计报告

> 审计视角：资深全栈工程师（10年+经验）
> 审计范围：TypeScript 前端、Rust 后端、架构设计、测试、安全、DevOps
> 项目规模：约 4000 行 App.tsx + 600 行 lib.rs + 20+ 服务模块 + 59 个 skills

---

## 📊 总体评价

**评分：7 / 10**

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | 8/10 | 模块划分清晰，职责分离良好，但部分模块过大 |
| 代码质量 | 6/10 | TypeScript 规范较好，但前端逻辑过于集中 |
| 类型安全 | 7/10 | 有类型定义，但存在过多 `string` 联合类型 |
| 测试覆盖 | 5/10 | 有 vitest 测试框架，实际测试用例极少 |
| Rust 代码 | 8/10 | 简洁规范，错误处理统一，async 处理得当 |
| 依赖管理 | 7/10 | 依赖较新，版本稳定，部分依赖版本过旧 |

---

## 🔴 严重问题（必须修复）

### 1. App.tsx 严重违反单一职责原则（SRP）

**问题**：`src/App.tsx` 约 **4000+ 行**，是整个应用的主协调器，承担了：

- 50+ 个 `useState` 状态
- 30+ 个 `useEffect` 副作用
- 15+ 个 `useMemo` 计算
- 所有协作逻辑（云同步、评论、Yjs）
- 所有文件操作（打开/保存/删除/重命名）
- 所有 AI Agent 交互
- 所有 LaTeX 编译流程
- 所有研究任务管理
- 所有模态框状态
- 所有键盘快捷键处理
- 所有菜单响应

**风险**：
- 无法独立测试任何业务逻辑
- 代码审查极其困难（diff 动不动上千行）
- 新人接手成本极高
- Bug 定位困难（逻辑散落各处）

**修复建议**：将 App.tsx 拆分为多个子组件和自定义 Hook：

```
src/
├── components/
│   ├── TopBar/
│   │   ├── WorkspaceMenuBar.tsx        # 菜单栏（独立组件）
│   │   └── CompileStatusIndicator.tsx  # 编译状态
│   ├── ResearchSurface/                 # 研究画布
│   │   ├── ResearchCanvas.tsx          # 已有，提取逻辑
│   │   ├── TaskPanel.tsx
│   │   └── StageNavigator.tsx
│   ├── WritingSurface/                 # 写作台
│   │   ├── EditorPane.tsx              # 已有
│   │   └── PreviewPane.tsx             # 已有
│   └── Collab/
│       ├── SyncStatus.tsx
│       └── CommentPanel.tsx
├── hooks/
│   ├── useAppState.ts                 # 合并所有 useState → 单一状态树
│   ├── useWorkspace.ts                # 工作区操作
│   ├── useCollaboration.ts             # 协作逻辑
│   ├── useAgent.ts                     # AI Agent 交互
│   └── useCompile.ts                   # 编译流程
└── App.tsx                             # 简化为布局 + 路由分发
```

---

### 2. 错误处理不一致（静默失败）

**问题**：代码中存在多种错误处理风格混用：

```typescript
// ❌ 风格 1：静默失败（危险）
async function handleSkillsChanged() {
  try {
    const fresh = await desktop.listSkills();
    setSnapshot((current) => current ? { ...current, skills: fresh } : current);
  } catch {
    // ignore  ← 吞掉所有错误，用户完全无感知
  }
}

// ❌ 风格 2：部分通知
} catch (error) {
  console.warn("[collab.sync] failed to upload blob", imagePath, error);
  // 警告但不阻断，用户可能不知道同步失败了
}

// ✅ 风格 3：正确示范
} catch (error) {
  setRuntimeNotice({
    tone: "error",
    text: summarizeRuntimeIssue(error, "应用任务建议失败"),
  });
  throw error; // 重要操作失败时应该抛出
}
```

**修复建议**：建立统一的错误处理策略

```typescript
// 建立错误分类
enum ErrorSeverity {
  IGNORABLE = "ignorable",   // ResizeObserver 等浏览器内部问题
  WARNING = "warning",        // 非关键操作失败，通知用户
  FATAL = "fatal",            // 关键操作失败，中断流程
}

// 统一错误处理 Hook
function useErrorHandler() {
  const notify = (severity, message, detail?) => {
    switch (severity) {
      case ErrorSeverity.WARNING:
        setRuntimeNotice({ tone: "error", text: message });
        console.warn(message, detail);
        break;
      case ErrorSeverity.FATAL:
        setRuntimeNotice({ tone: "error", text: message });
        throw detail; // 中断执行
    }
  };
  return notify;
}
```

---

### 3. Rust 中滥用 `.expect()` 导致 Panic

**问题**：`src-tauri/src/lib.rs` 中多处使用 `.expect()`：

```rust
// ❌ lib.rs:39 - 启动失败会导致整个 App Panic
let conn = db::init_db(&app_data_dir).expect("failed to init database");

// ❌ lib.rs:53
services::skill::refresh_skill_registry(&conn, &skills_dir, workspace_root.as_deref())
    .expect("failed to refresh skills");

// ❌ lib.rs:191
.expect("failed to start Oh My Paper")
```

**修复建议**：使用 `?` 运算符 + 统一错误传播

```rust
// ✅ 定义应用级错误类型
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("数据库初始化失败: {0}")]
    DbInit(#[from] rusqlite::Error),

    #[error("技能注册失败: {0}")]
    SkillRegistry(String),

    #[error("Tauri 启动失败: {0}")]
    Tauri(String),
}

// 在 main 中统一处理
fn main() {
    if let Err(e) = run() {
        eprintln!("Fatal error: {}", e);
        std::process::exit(1);
    }
}

pub fn run() -> Result<(), AppError> {
    // ... 使用 ? 替代 expect
    let conn = db::init_db(&app_data_dir)?;
    services::skill::refresh_skill_registry(&conn, &skills_dir, workspace_root.as_deref())?;
    // ...
}
```

---

## 🟡 中等问题（建议修复）

### 4. 类型定义过于宽松

**问题**：`src/types.ts` 中大量使用 `string` 而非字面量类型：

```typescript
// ❌ types.ts:71 - level 可以是任意字符串
level: "error" | "warning" | "info" | string,  // 应改为联合类型

// ❌ types.ts:77 - status 可以是任意字符串
status: CompileStatus | string,  // 应只用 CompileStatus

// ❌ types.ts:535 - 使用 any
runHistory: any[],  // 应定义具体类型

// ❌ types.ts:196, 201 等多处
stage: "planning" | "drafting" | "revision" | "submission" | "figures" | string
outputMode: "rewrite" | "outline" | "review" | string
```

**修复建议**：使用 TypeScript 的 `as const` + 派生类型

```typescript
// ✅ 定义受限的联合类型
type DiagnosticLevel = "error" | "warning" | "info";
type ProfileStage = "planning" | "drafting" | "revision" | "submission" | "figures";
type OutputMode = "rewrite" | "outline" | "review";

// ✅ 派生接口
interface Diagnostic {
  filePath: string;
  line: number;
  level: DiagnosticLevel;
  message: string;
}

// ✅ 实验历史记录具体类型
interface ExperimentHistoryEntry {
  timestamp: number;
  metricValue: number;
  params: Record<string, number>;
  status: "running" | "completed" | "failed";
}
```

---

### 5. 测试覆盖率严重不足

**问题**：项目有 `vitest` 配置和部分 `.test.ts` 文件，但实际测试用例极少。

**证据**：
```bash
# 搜索测试文件
find src -name "*.test.ts" | wc -l  # 结果极少
find src-tauri/src -name "*.rs" | xargs grep "#\[test\]" | wc -l  # Rust 仅 2 个测试
```

**修复建议**：

```
测试覆盖率目标：
- 工具函数：90%+
- 自定义 Hooks：80%+
- 组件（交互逻辑）：60%+
- Rust 服务：70%+

优先测试：
1. src/lib/workspace.ts - 文件操作工具函数
2. src/lib/outline.ts - 大纲解析逻辑
3. src/lib/pdf-source.ts - PDF 路径解析
4. src/lib/collaboration/doc-manager.ts - 协作同步逻辑
5. src-tauri/src/services/compile.rs - 编译流程
```

---

### 6. `services/mod.rs` 的 `enriched_path()` 函数过长

**问题**：185 行的函数，处理 macOS/Linux/Windows 三平台 PATH 扩展，没有任何拆分。

**修复建议**：按平台拆分 + 使用配置驱动

```rust
// services/mod.rs
pub(crate) fn enriched_path() -> String {
    let current = std::env::var("PATH").unwrap_or_default();
    let extra = collect_extra_paths();

    if extra.is_empty() {
        current
    } else {
        let sep = if cfg!(windows) { ";" } else { ":" };
        format!("{}{}{}", extra.join(sep), sep, current)
    }
}

#[cfg(target_os = "macos")]
fn collect_extra_paths() -> Vec<String> {
    let mut paths = Vec::new();
    paths.extend(home_bin_paths());    // ~/.local/bin, ~/.npm/bin, etc.
    paths.extend(standard_mac_paths()); // /opt/homebrew/bin, /Library/TeX/texbin
    paths.extend(texlive_paths());      // /usr/local/texlive/*/bin
    paths.extend(tinytex_paths());       // ~/Library/TinyTeX/bin
    paths
}
```

---

## 🟢 轻微问题（可优化）

### 7. 硬编码 Magic Numbers

```typescript
// ❌ 分散的魔法数字
const MAX_RECENT_WORKSPACES = 10;    // 有定义，但散落各处
const MAX_OPEN_WORKSPACES = 6;       // 有定义
// 但这些没有：
const AUTO_SAVE_DEBOUNCE_MS = 900;   // line 2075
const RELEASE_NOTES_TIMEOUT_MS = 8000; // line 518
const MAX_DEBUG_LOG_LINES = 120;     // line 801
const MAX_COLLAB_LOG_LINES = 240;   // line 839
```

**修复**：建立统一的常量文件 `src/constants.ts`

---

### 8. Hooks 中依赖数组过于庞大

```typescript
// ❌ line 2078 - 9 个依赖项
useEffect(() => {
  // ...
}, [
  activeFilePath, dirtyPaths, executeCompile,
  isAutoSaveEnabled, refreshResearchSnapshotIfNeeded,
  saveOpenFiles, snapshot
]);
```

**风险**：任何依赖变化都触发重新订阅，容易遗漏导致 Bug。

**建议**：
1. 拆分过大的 Effect 为多个小 Effect
2. 使用 `useCallback` / `useEffectEvent` 稳定引用
3. 考虑 Zustand / Jotai 状态管理，减少 Prop Drilling

---

### 9. 注释掉的死代码未清理

```typescript
// ❌ App.tsx line 2144-2176 - 大量注释代码
/* [unused – kept for future wiring]
const _handleNewSession = ...
const _handleSelectSession = ...
...
*/
```

**风险**：混淆代码审查，误导后续开发者。

**建议**：删除或移到独立的 `ARCHIVE.md` 文档中。

---

## ✅ 项目优点（值得保持）

1. **TypeScript 配置严格**：`strict: true`，类型覆盖率高
2. **Rust 错误处理规范**：统一使用 `thiserror`，异步使用 `tokio`
3. **服务模块化**：Rust 服务拆分清晰（agent, compile, literature, skill 等）
4. **自定义 Hook 抽象**：有 `useEffectEvent` 等良好的 Hook 封装模式
5. **错误边界**：React 有 `PaneErrorBoundary` 防止单组件崩溃
6. **国际化意识**：`locale === "zh-CN"` 双语切换
7. **多工作区支持**：Tab 系统管理多个项目

---

## 📋 修复优先级建议

| 优先级 | 问题 | 预计工时 | 影响 |
|--------|------|----------|------|
| P0 | App.tsx 拆分 | 3-5 天 | 代码可维护性大幅提升 |
| P0 | Rust `.expect()` 替换 | 1 天 | 稳定性提升 |
| P1 | 类型定义收紧 | 2 天 | 代码健壮性 |
| P1 | 错误处理统一 | 2 天 | 用户体验 |
| P2 | 测试覆盖率提升 | 持续 | 长期质量 |
| P2 | `enriched_path()` 拆分 | 0.5 天 | 可读性 |
| P3 | Magic Numbers 归拢 | 0.5 天 | 可读性 |
| P3 | 死代码清理 | 0.5 天 | 代码整洁 |

---

## 🎓 团队提升建议

### 短期（1-2周）
1. **Code Review 规范**：强制要求 PR 必须有测试
2. **结对重构 App.tsx**：我带你们拆分第一个子模块，作为示范

### 中期（1个月）
1. 建立测试文化（从 utils 测试开始，逐步覆盖关键路径）
2. 引入 Prettier + 统一格式化
3. 完善类型定义（从 `types.ts` 开始收紧）

### 长期
1. 考虑引入状态管理库（Zustand/Jotai）减少 App.tsx 状态
2. 建立 E2E 测试（Playwright）
3. CI/CD 中集成测试覆盖率 gate

---

*审计时间：2026-05-03 | 审计工具：CodeBuddy + 人工审查*
