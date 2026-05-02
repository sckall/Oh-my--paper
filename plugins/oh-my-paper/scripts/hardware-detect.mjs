#!/usr/bin/env node
/**
 * hardware-detect.mjs - 硬件检测脚本
 *
 * 检测 NVIDIA CUDA / Apple MPS / CPU
 * 根据硬件类型调整代码生成策略
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ============================================================
// 硬件检测主函数
// ============================================================

/**
 * 检测系统硬件
 * @returns {Object} 硬件信息
 */
export function detectHardware() {
  const hardware = {
    type: 'unknown',
    device_name: '',
    memory: 0,
    compute_capability: '',
    cuda_version: '',
    warnings: [],
    recommendations: []
  };

  // 按优先级检测: CUDA > MPS > CPU
  if (detectCUDA(hardware)) {
    hardware.type = 'cuda';
  } else if (detectMPS(hardware)) {
    hardware.type = 'mps';
  } else {
    detectCPU(hardware);
    hardware.type = 'cpu';
  }

  // 根据硬件类型给出建议
  generateRecommendations(hardware);

  return hardware;
}

/**
 * 检测 NVIDIA CUDA
 */
function detectCUDA(hardware) {
  try {
    // 检查 nvidia-smi 是否可用
    const nvidiaSmi = execSync('which nvidia-smi', { encoding: 'utf8' }).trim();

    // 获取 GPU 信息
    const gpuInfo = execSync('nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader', {
      encoding: 'utf8',
      timeout: 5000
    }).trim();

    const [name, memory, compute] = gpuInfo.split(',').map(s => s.trim());

    hardware.device_name = name;
    hardware.memory = parseMemory(memory);
    hardware.compute_capability = compute;

    // 获取 CUDA 版本
    try {
      hardware.cuda_version = execSync('nvcc --version', { encoding: 'utf8', timeout: 5000 })
        .match(/release (\d+\.\d+)/)?.[1] || 'unknown';
    } catch {
      hardware.cuda_version = 'unknown';
    }

    return true;
  } catch {
    return false;
  }
}

/**
 * 检测 Apple MPS
 */
function detectMPS(hardware) {
  try {
    // 检查 Metal GPU
    const metalInfo = execSync('system_profiler SPDisplaysDataType', {
      encoding: 'utf8',
      timeout: 5000
    });

    if (metalInfo.includes('Metal')) {
      // 检查是否有 Apple Silicon
      const chipInfo = execSync('sysctl -n machdep.cpu.brand_string', { encoding: 'utf8' });

      hardware.device_name = chipInfo.includes('Apple') ? 'Apple Silicon (Metal)' : 'Unknown Metal GPU';
      hardware.memory = getAppleMemory();

      return true;
    }
  } catch {
    // MPS 不可用
  }

  return false;
}

/**
 * 检测 CPU
 */
function detectCPU(hardware) {
  try {
    const cpuBrand = execSync('sysctl -n machdep.cpu.brand_string', { encoding: 'utf8' }).trim();
    const cpuCores = execSync('sysctl -n hw.ncpu', { encoding: 'utf8' }).trim();

    hardware.device_name = cpuBrand;
    hardware.memory = 0;
    hardware.cpu_cores = parseInt(cpuCores, 10);

    hardware.warnings.push('未检测到 GPU，将使用 CPU-only 模式');
  } catch {
    hardware.device_name = 'Unknown CPU';
  }
}

/**
 * 获取 Apple Silicon 内存
 */
function getAppleMemory() {
  try {
    const totalMemory = execSync('sysctl -n hw.memsize', { encoding: 'utf8' }).trim();
    return Math.round(parseInt(totalMemory, 10) / (1024 * 1024 * 1024)); // GB
  } catch {
    return 0;
  }
}

/**
 * 解析内存字符串 (如 "16384 MB")
 */
function parseMemory(memoryStr) {
  const match = memoryStr.match(/(\d+)\s*(MB|GB|TB)?/i);
  if (match) {
    let value = parseInt(match[1], 10);
    const unit = (match[2] || 'MB').toUpperCase();

    if (unit === 'GB') value *= 1024;
    else if (unit === 'TB') value *= 1024 * 1024;

    return value; // MB
  }
  return 0;
}

/**
 * 根据硬件类型生成建议
 */
function generateRecommendations(hardware) {
  switch (hardware.type) {
    case 'cuda':
      hardware.recommendations = [
        '✓ 使用 PyTorch 或 TensorFlow 进行深度学习',
        '✓ 使用 CUDA 加速的 GPU 操作',
        '✓ 优先使用 GPU tensor 操作而非 CPU'
      ];

      // 根据显存给出警告
      if (hardware.memory < 8000) {
        hardware.warnings.push(`⚠️ 显存较小 (${hardware.memory}MB)，建议减小 batch size`);
      }

      // 根据算力给出警告
      if (hardware.compute_capability < '7.0') {
        hardware.warnings.push(`⚠️ 算力较低 (${hardware.compute_capability})，部分新特性可能不支持`);
      }
      break;

    case 'mps':
      hardware.recommendations = [
        '✓ 使用 PyTorch with MPS 后端',
        '✓ 注意：部分操作在 MPS 上可能较慢',
        '✓ 建议使用 float16 精度以提高性能',
        '⚠️ 某些 CUDA 特有操作在 MPS 上不可用'
      ];
      break;

    case 'cpu':
      hardware.recommendations = [
        '✓ 使用 NumPy 进行数值计算',
        '✓ 避免大型深度学习模型',
        '✓ 考虑使用 sklearn 替代 PyTorch',
        '⚠️ CPU 训练深度学习非常慢，建议小规模实验'
      ];
      break;
  }
}

// ============================================================
// 写入硬件状态文件
// ============================================================

/**
 * 检测并写入硬件状态到文件
 */
export function detectAndSave(projectRoot = process.cwd()) {
  const hardware = detectHardware();

  const outputPath = path.join(projectRoot, '.pipeline/mega/hardware_status.md');

  const content = `# 硬件检测状态
_Detected: ${new Date().toISOString()}_

## 硬件类型
**${hardware.type.toUpperCase()}**

## 设备信息
| 属性 | 值 |
|------|-----|
| 设备名称 | ${hardware.device_name} |
| 内存 | ${hardware.memory > 0 ? hardware.memory + ' MB' : 'N/A'} |
| ${hardware.compute_capability ? '算力' : ''} | ${hardware.compute_capability || ''} |
| ${hardware.cuda_version ? 'CUDA 版本' : ''} | ${hardware.cuda_version || ''} |

## 代码生成建议
${hardware.recommendations.map(r => `- ${r}`).join('\n')}

${hardware.warnings.length > 0 ? '## 警告\n' + hardware.warnings.map(w => `- ${w}`).join('\n') : ''}
`;

  // 确保目录存在
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(outputPath, content, 'utf8');

  return hardware;
}

// ============================================================
// CLI 入口
// ============================================================

if (import.meta.url === `file://${process.argv[1]}`) {
  const projectRoot = process.argv[2] || process.cwd();

  console.log('\n🔍 检测硬件...\n');

  const hardware = detectAndSave(projectRoot);

  console.log('='.repeat(60));
  console.log(`\n📊 硬件类型: ${hardware.type.toUpperCase()}`);
  console.log(`💻 设备: ${hardware.device_name}`);
  console.log(`📐 内存: ${hardware.memory > 0 ? hardware.memory + ' MB' : 'N/A'}`);

  console.log('\n📋 建议:');
  hardware.recommendations.forEach(r => console.log('  ' + r));

  if (hardware.warnings.length > 0) {
    console.log('\n⚠️ 警告:');
    hardware.warnings.forEach(w => console.log('  ' + w));
  }

  console.log(`\n✅ 硬件状态已写入: .pipeline/mega/hardware_status.md\n`);
}

export default detectHardware;
