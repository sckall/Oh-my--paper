# Mega 流水线设置

## 自动执行设置
AUTO_EXECUTE: true     # 启用自动驾驶
AUTO_DECISION: false   # 决策仍需确认
PAUSE_ON_PIVOT: true   # PIVOT 时暂停
PAUSE_ON_REFINE: true  # REFINE 时暂停

## 各 Group 配置

### Group A: 研究定义
AUTO_EXECUTE_A: true
PAUSE_ON_A8: true      # A8 研究决策需要确认

### Group B: 实验
AUTO_EXECUTE_B: true
PAUSE_ON_B10: true     # B10 实验门控需要确认
PAUSE_ON_B15: true     # B15 研究决策需要确认

### Group C: 论文
AUTO_EXECUTE_C: true
PAUSE_ON_C17: true     # C17 写作阶段按节暂停
PAUSE_ON_C20: true     # C20 质量门控需要确认

### Group D-I: 审核迭代
AUTO_EXECUTE_DI: true
PAUSE_ON_I25: true     # I25 Rebuttal 需要确认

## 硬件配置
hardware_check: true   # 启动前检测硬件