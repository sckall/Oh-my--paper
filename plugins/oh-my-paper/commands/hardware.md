---
description: A+ 硬件检测：自动检测 GPU 类型并调整代码生成策略
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。此命令实现 A+ 硬件检测阶段，自动检测 GPU 类型并根据性能调整代码生成策略。

## 第一步：检测硬件

```bash
# 检测 NVIDIA GPU
nvidia-smi 2>/dev/null || echo "NO_NVIDIA"

# 检测 Apple MPS
python3 -c "import torch; print('MPS:', torch.backends.mps.is_available())" 2>/dev/null || echo "NO_MPS"

# 检测 CPU 核心数
sysctl -n hw.ncpu 2>/dev/null || echo "UNKNOWN_CPU"

# 内存情况
free -m 2>/dev/null || echo "UNKNOWN_MEMORY"
```

## 第二步：分析硬件能力

用 `AskUserQuestion` 展示硬件状态：

> **硬件检测结果**
>
> | 硬件类型 | 状态 | 备注 |
> |---------|------|------|
> | NVIDIA GPU | [有/无] | [型号/不适用] |
> | Apple MPS | [可用/不可用] | [设备名/不适用] |
> | CPU | [核心数] 核 | |
> | 内存 | [容量] GB | |
>
> **代码生成策略**：
> - 如果有 NVIDIA GPU → 使用 CUDA 优化
> - 如果有 Apple MPS → 使用 Metal 优化
> - 如果只有 CPU → 使用 NumPy 优化

## 第三步：写入硬件状态

```bash
# 创建硬件状态文件
cat > .pipeline/mega/hardware_status.md << 'EOF'
# 硬件状态

## 检测时间
[时间戳]

## GPU 检测
- NVIDIA CUDA: [是/否]
  - 型号: [型号]
  - CUDA 版本: [版本]
  - 显存: [容量]

- Apple MPS: [是/否]
  - 设备: [设备名]

## CPU
- 核心数: [N] 核
- 架构: [架构]

## 内存
- 总量: [容量] GB

## 代码生成策略
- 主后端: [cuda/mps/cpu]
- NumPy 优先: [true/false]
- GPU 加速: [true/false]

## 性能警告
[如有性能不足问题，在此记录]
EOF
```

## 硬件与代码策略映射

| 硬件 | 代码策略 | NumPy 版本 |
|------|---------|------------|
| NVIDIA GPU (CUDA) | torch/tensorflow with CUDA | NumPy 2.x |
| Apple MPS | PyTorch MPS | NumPy 2.x |
| CPU Only | NumPy only | NumPy 2.x |

## 性能不足警告

如果检测到硬件性能不足：

> ⚠️ **硬件性能警告**
>
> 问题：[描述性能问题]
>
> 建议：
> - [降低实验规模]
> - [减少随机种子次数]
> - [限制每轮优化步数]
>
> 选项：
> - `接受建议，调整实验配置`
> - `忽略警告，继续`

## 自动更新 research_brief.json

根据硬件检测结果，自动更新 `research_brief.json`：

```json
{
  "hardware": {
    "type": "cuda/mps/cpu",
    "gpu_model": "...",
    "memory_gb": ...,
    "cpu_cores": ...,
    "code_strategy": "..."
  }
}
```