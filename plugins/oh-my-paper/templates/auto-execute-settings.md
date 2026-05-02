# 自动执行设置

此文件控制 Mega 流水线的自动执行行为。

## 基本设置

```markdown
# 是否启用自动执行模式
AUTO_EXECUTE: true

# 决策是否自动执行（无需人工确认）
# true = PROCEED 自动推进，REFINE/PIVOT 暂停
# false = 所有决策都需要人工确认
AUTO_DECISION: false
```

## 暂停条件

```markdown
# 门控检查时是否暂停
PAUSE_ON_GATE: true

# PIVOT 决策时是否暂停（强烈建议 true）
PAUSE_ON_PIVOT: true

# 发现 CRITICAL 问题时是否暂停
PAUSE_ON_CRITICAL: true

# 决策为 REFINE 时是否暂停
PAUSE_ON_REFINE: true
```

## 多智能体协作

```markdown
# A7 多 Agent 辩论是否自动执行
AUTO_DEBATE: true

# B14 独立分析是否自动执行
AUTO_ANALYZE: true

# C18 同行评审是否自动执行
AUTO_REVIEW: true
```

## 通知设置

```markdown
# 每阶段完成时是否通知用户
NOTIFY_ON_STAGE: true

# 决策前是否通知用户
NOTIFY_ON_DECISION: true

# 暂停时是否通知原因
NOTIFY_ON_PAUSE: true
```

## 示例配置

### 激进模式（最大自动化）

```markdown
AUTO_EXECUTE: true
AUTO_DECISION: true
PAUSE_ON_GATE: false
PAUSE_ON_PIVOT: true
PAUSE_ON_CRITICAL: true
PAUSE_ON_REFINE: false
AUTO_DEBATE: true
AUTO_ANALYZE: true
AUTO_REVIEW: true
NOTIFY_ON_STAGE: false
NOTIFY_ON_DECISION: false
NOTIFY_ON_PAUSE: true
```

### 保守模式（最大控制）

```markdown
AUTO_EXECUTE: true
AUTO_DECISION: false
PAUSE_ON_GATE: true
PAUSE_ON_PIVOT: true
PAUSE_ON_CRITICAL: true
PAUSE_ON_REFINE: true
AUTO_DEBATE: false
AUTO_ANALYZE: false
AUTO_REVIEW: false
NOTIFY_ON_STAGE: true
NOTIFY_ON_DECISION: true
NOTIFY_ON_PAUSE: true
```

### 推荐模式（平衡）

```markdown
AUTO_EXECUTE: true
AUTO_DECISION: false
PAUSE_ON_GATE: true
PAUSE_ON_PIVOT: true
PAUSE_ON_CRITICAL: true
PAUSE_ON_REFINE: true
AUTO_DEBATE: true
AUTO_ANALYZE: true
AUTO_REVIEW: true
NOTIFY_ON_STAGE: true
NOTIFY_ON_DECISION: true
NOTIFY_ON_PAUSE: true
```