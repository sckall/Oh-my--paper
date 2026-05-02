# 门控阶段计划模板

## 门控概述

| 属性 | 值 |
|------|-----|
| 门控 ID | {gate_id} |
| 门控名称 | {gate_name} |
| 位置 | Group {group} |
| 下一门控 | {next_gate} |

## 检查清单

### {gate_id} {gate_name}

| 检查项 | 要求 | 当前状态 |
|--------|------|----------|
| 检查项 1 | {requirement} | {status} |
| 检查项 2 | {requirement} | {status} |
| 检查项 3 | {requirement} | {status} |

## 通过条件

{conditions}

## 决策选项

当门控未通过时：

- **补充/重做**: 返回上一阶段，补充不足
- **调整范围**: 调整研究问题或实验设计
- **放弃方向**: 记录到 decision_log.md，换方向

## 门控记录

| 日期 | 结果 | 决策 | 备注 |
|------|------|------|------|
| {date} | {result} | {decision} | {notes} |