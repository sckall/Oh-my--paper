---
description: C21 知识归档 — 归档研究成果，准备可复现性包
---

你是 Oh My Paper Orchestrator。此命令实现 C21 KNOWLEDGE_ARCHIVE 阶段。

## 🚀 一键执行

当调用此命令时，自动执行：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📦 C21 知识归档
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📚 正在归档研究成果...
  📦 正在打包可复现性资料...
  📝 正在记录经验教训...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 自动执行流程

### 1. 收集所有研究产物

```bash
# 收集各类文件
ls -la .pipeline/memory/
ls -la .pipeline/docs/
ls -la experiments/
ls -la paper/sections/
ls -la results/
```

### 2. 生成归档文档

```bash
cat > .pipeline/mega/knowledge_archive.md << 'EOF'
# Knowledge Archive

## 研究摘要

### 研究问题
[从 project_truth.md]

### 假设
[从 hypothesis.md]

### 方法
[从 methodology.tex]

### 关键发现
[从 result_summary.md]

## 可复现性包

### 代码
- 位置：experiments/
- 依赖：requirements.txt
- 规范：README.md

### 数据
- 位置：data/
- 格式：[说明]
- 来源：[说明]

### 模型
- 位置：checkpoints/
- 格式：[说明]

## 关键决策

| 日期 | 决策 | 原因 | 版本 |
|------|------|------|------|
| ... | ... | ... | ... |

## 经验教训

### 什么有效
[经验1]
[经验2]

### 什么无效
[教训1]
[教训2]

### 未来方向
[方向1]
[方向2]

## 归档清单

- [x] 代码归档
- [x] 数据归档
- [x] 结果归档
- [x] 决策日志
- [x] 经验总结

生成时间：[ISO 日期]
EOF
```

### 3. 打包可复现性包

```bash
# 创建归档目录
mkdir -p .pipeline/mega/archive

# 复制代码
cp -r experiments/ .pipeline/mega/archive/

# 复制数据
cp -r data/ .pipeline/mega/archive/ 2>/dev/null || echo "No data directory"

# 复制论文
cp -r paper/ .pipeline/mega/archive/

# 复制 requirements
pip freeze > .pipeline/mega/archive/requirements.txt

# 创建归档说明
cat > .pipeline/mega/archive/README.md << 'EOF'
# 可复现性包

## 如何复现

1. 安装依赖：`pip install -r requirements.txt`
2. 运行实验：`python experiments/main.py`
3. 生成论文：`cd paper && pdflatex main.tex`

## 硬件要求
[hardware_status.md 中的信息]

## 关键参数
[experiment_plan.md 中的参数]
EOF
```

## 归档内容清单

| 类型 | 内容 | 位置 |
|------|------|------|
| 代码 | experiments/ | .pipeline/mega/archive/ |
| 数据 | data/ | .pipeline/mega/archive/ |
| 论文 | paper/ | .pipeline/mega/archive/ |
| 决策 | decision_log.md | .pipeline/memory/ |
| 结果 | experiment_ledger.md | .pipeline/memory/ |
| 配置 | requirements.txt | .pipeline/mega/archive/ |

## 渐进式披露

### 概要展示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📦 C21 归档完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📚 代码: experiments/ (归档)
  📦 数据: data/ (归档)
  📝 论文: paper/ (归档)
  📋 决策日志: 12 条
  📖 经验教训: 5 条

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [查看归档]  [导出包]  [继续]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 与下一步衔接

归档完成后：
- 如果是 C21 → 自动推进到 C22 导出发布
- 如果需要导出 → 打包发送到指定位置

## 知乎原文对应

知乎提示词中的 C21：

> 21. KNOWLEDGE_ARCHIVE