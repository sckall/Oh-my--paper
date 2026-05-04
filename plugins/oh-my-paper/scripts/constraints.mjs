#!/usr/bin/env node
/**
 * constraints.mjs - HARD CONSTRAINTS 检查系统
 *
 * 基于论文AI提示词.md 的 HARD CONSTRAINTS 实现
 * 用于在实验和写作阶段进行约束检查
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ============================================================
// 约束检查主函数
// ============================================================

/**
 * 执行所有约束检查
 * @param {string} type - 'experiment' | 'paper' | 'all'
 * @param {string} projectRoot - 项目根目录
 */
export async function runConstraintsCheck(type = 'all', projectRoot = process.cwd()) {
  const results = {
    passed: [],
    failed: [],
    warnings: [],
    timestamp: new Date().toISOString()
  };

  if (type === 'all' || type === 'experiment') {
    const expResults = await checkExperimentConstraints(projectRoot);
    results.passed.push(...expResults.passed);
    results.failed.push(...expResults.failed);
    results.warnings.push(...expResults.warnings);
  }

  if (type === 'all' || type === 'paper') {
    const paperResults = await checkPaperConstraints(projectRoot);
    results.passed.push(...paperResults.passed);
    results.failed.push(...paperResults.failed);
    results.warnings.push(...paperResults.warnings);
  }

  return results;
}

// ============================================================
// 1. 计算与资源守卫 (Computation & Resource Guard)
// ============================================================

async function checkResourceGuard(projectRoot) {
  const results = { passed: [], failed: [], warnings: [] };

  // 检查 Pilot 是否运行
  const pilotPath = path.join(projectRoot, '.pipeline/mega/logs/pilot_result.md');
  if (fs.existsSync(pilotPath)) {
    const pilotContent = fs.readFileSync(pilotPath, 'utf8');
    if (pilotContent.includes('TIME_ESTIMATE')) {
      results.passed.push('✅ Pilot 运行完成，已记录 TIME_ESTIMATE');
    } else {
      results.failed.push('❌ Pilot 运行但未记录 TIME_ESTIMATE');
    }
  } else {
    results.warnings.push('⚠️ Pilot 结果文件不存在');
  }

  // 检查 experiment_plan 中的资源估算
  const expPlanPath = path.join(projectRoot, '.pipeline/docs/experiment_plan.md');
  if (fs.existsSync(expPlanPath)) {
    const expPlan = fs.readFileSync(expPlanPath, 'utf8');
    if (expPlan.includes('compute_budget') || expPlan.includes('gpu_hours')) {
      results.passed.push('✅ 实验计划包含资源预算');
    } else {
      results.warnings.push('⚠️ 实验计划缺少资源预算估算');
    }
  }

  return results;
}

// ============================================================
// 2. 真实性红线 (Truthfulness Code Red Lines)
// ============================================================

async function checkTruthfulnessRedLines(projectRoot) {
  const results = { passed: [], failed: [], warnings: [] };

  const expDir = path.join(projectRoot, 'experiments');

  if (!fs.existsSync(expDir)) {
    results.warnings.push('⚠️ experiments/ 目录不存在，跳过真实性检查');
    return results;
  }

  // 遍历所有 Python 文件
  const pyFiles = getPythonFiles(expDir);

  for (const file of pyFiles) {
    const content = fs.readFileSync(file, 'utf8');

    // 检查禁止的模式
    const forbiddenPatterns = [
      { pattern: /random\.uniform\s*\(/, name: 'random.uniform() 伪造数据' },
      { pattern: /np\.random\.rand\s*\(/, name: 'np.random.rand() 伪造数据' },
      { pattern: /np\.nan_to_num\s*\(/, name: 'np.nan_to_num() 掩盖错误' },
    ];

    for (const { pattern, name } of forbiddenPatterns) {
      if (pattern.test(content)) {
        results.failed.push(`❌ ${path.relative(projectRoot, file)}: 包含 ${name}`);
      }
    }

    // 检查必需的模式
    const requiredPatterns = [
      { pattern: /convergence|converge/i, name: '收敛检查' },
      { pattern: /seed/i, name: '随机种子' },
    ];

    for (const { pattern, name } of requiredPatterns) {
      if (pattern.test(content)) {
        results.passed.push(`✅ ${path.relative(projectRoot, file)}: 包含 ${name}`);
      }
    }

    // 检查 time_guard
    if (content.includes('time_guard') || content.includes('time.time()')) {
      results.passed.push(`✅ ${path.relative(projectRoot, file)}: 包含 time_guard`);
    }

    // 检查 checkpoint
    if (content.includes('checkpoint') || content.includes('save')) {
      results.passed.push(`✅ ${path.relative(projectRoot, file)}: 包含 checkpoint 保存`);
    }
  }

  if (pyFiles.length === 0) {
    results.warnings.push('⚠️ experiments/ 中没有找到 Python 文件');
  }

  return results;
}

// ============================================================
// 3. 顶会论文标准 (Top-tier Paper Standards)
// ============================================================

async function checkPaperStandards(projectRoot) {
  const results = { passed: [], failed: [], warnings: [] };

  const sectionsDir = path.join(projectRoot, 'paper/sections');
  const figuresDir = path.join(projectRoot, 'paper/assets/figures');

  // 检查论文章节
  if (!fs.existsSync(sectionsDir)) {
    results.warnings.push('⚠️ paper/sections/ 目录不存在');
    return results;
  }

  const sections = ['introduction.tex', 'methodology.tex', 'experiments.tex'];
  for (const section of sections) {
    const sectionPath = path.join(sectionsDir, section);
    if (fs.existsSync(sectionPath)) {
      const content = fs.readFileSync(sectionPath, 'utf8');
      const wordCount = content.split(/\s+/).length;

      // 字数检查
      const minWords = {
        'introduction.tex': 800,
        'methodology.tex': 1000,
        'experiments.tex': 800
      };

      if (wordCount >= minWords[section]) {
        results.passed.push(`✅ ${section}: ${wordCount} 词 (≥ ${minWords[section]})`);
      } else {
        results.failed.push(`❌ ${section}: ${wordCount} 词 (< ${minWords[section]})`);
      }
    } else {
      results.warnings.push(`⚠️ ${section} 不存在`);
    }
  }

  // 检查 Figure 1
  if (fs.existsSync(figuresDir)) {
    const figures = fs.readdirSync(figuresDir);
    const hasArchitecture = figures.some(f =>
      f.includes('architecture') || f.includes('fig1') || f.includes('overview')
    );

    if (hasArchitecture) {
      results.passed.push('✅ Figure 1 (架构图) 存在');
    } else {
      results.warnings.push('⚠️ 未找到架构图 (建议命名为 architecture.png 或 fig1.png)');
    }
  } else {
    results.warnings.push('⚠️ paper/assets/figures/ 目录不存在');
  }

  // 检查消融实验
  const expPath = path.join(sectionsDir, 'experiments.tex');
  if (fs.existsSync(expPath)) {
    const content = fs.readFileSync(expPath, 'utf8');
    if (content.includes('ablation')) {
      results.passed.push('✅ 论文包含消融实验内容');
    } else {
      results.failed.push('❌ 论文缺少消融实验内容');
    }
  }

  // 检查基线数量
  const expContent = fs.readFileSync(expPath, 'utf8');
  const baselineMatches = expContent.match(/baseline|vs\.|对比/gi) || [];
  if (baselineMatches.length >= 3) {
    results.passed.push('✅ 论文包含足够的基线对比');
  } else {
    results.warnings.push('⚠️ 基线对比可能不足');
  }

  return results;
}

// ============================================================
// 4. 证据一致性 (Evidence Consistency)
// ============================================================

async function checkEvidenceConsistency(projectRoot) {
  const results = { passed: [], failed: [], warnings: [] };

  // 读取 result_summary
  const resultSummaryPath = path.join(projectRoot, '.pipeline/docs/result_summary.md');
  const experimentLedgerPath = path.join(projectRoot, '.pipeline/memory/experiment_ledger.md');

  if (!fs.existsSync(resultSummaryPath)) {
    results.warnings.push('⚠️ result_summary.md 不存在');
    return results;
  }

  if (!fs.existsSync(experimentLedgerPath)) {
    results.warnings.push('⚠️ experiment_ledger.md 不存在');
    return results;
  }

  const resultSummary = fs.readFileSync(resultSummaryPath, 'utf8');
  const ledger = fs.readFileSync(experimentLedgerPath, 'utf8');

  // 检查 result_summary 中的数值是否在 ledger 中有对应记录
  const metricsInSummary = resultSummary.match(/\d+\.?\d*/g) || [];
  const metricsInLedger = ledger.match(/\d+\.?\d*/g) || [];

  // 简单检查：ledger 应该包含更多数据点（因为是原始记录）
  if (metricsInLedger.length > metricsInSummary.length) {
    results.passed.push('✅ 实验记录一致性：ledger 包含原始数据');
  } else {
    results.warnings.push('⚠️ result_summary 和 experiment_ledger 数据量关系异常');
  }

  // 检查 NaN/Inf
  if (ledger.includes('NaN') || ledger.includes('Inf')) {
    results.failed.push('❌ experiment_ledger 包含 NaN/Inf 值');
  } else {
    results.passed.push('✅ 实验结果无 NaN/Inf');
  }

  return results;
}

// ============================================================
// 5. 环境兼容性 (Environment Compatibility)
// ============================================================

async function checkEnvironmentCompatibility(projectRoot) {
  const results = { passed: [], failed: [], warnings: [] };

  const expDir = path.join(projectRoot, 'experiments');

  if (!fs.existsSync(expDir)) {
    results.warnings.push('⚠️ experiments/ 目录不存在');
    return results;
  }

  const pyFiles = getPythonFiles(expDir);

  for (const file of pyFiles) {
    const content = fs.readFileSync(file, 'utf8');

    // NumPy 2.x 兼容性检查
    const numpy2Issues = [
      { pattern: /np\.trapz\s*\(/, name: 'np.trapz', fix: 'np.trapezoid' },
      { pattern: /np\.erfinv\s*\(/, name: 'np.erfinv', fix: 'scipy.special.erfinv' },
      { pattern: /np\.bool\s*\(/, name: 'np.bool', fix: 'bool' },
      { pattern: /np\.int\s*\(/, name: 'np.int', fix: 'int' },
      { pattern: /np\.float\s*\(/, name: 'np.float', fix: 'float' },
      { pattern: /np\.math\s*\(/, name: 'np.math', fix: 'math' },
    ];

    for (const issue of numpy2Issues) {
      if (issue.pattern.test(content)) {
        results.failed.push(`❌ ${path.relative(projectRoot, file)}: 使用了 ${issue.name} (应改为 ${issue.fix})`);
      }
    }

    // 检查是否导入了 numpy
    if (content.includes('import numpy') || content.includes('from numpy')) {
      results.passed.push(`✅ ${path.relative(projectRoot, file)}: 使用 NumPy`);
    }
  }

  return results;
}

// ============================================================
// 辅助函数
// ============================================================

function getPythonFiles(dir, files = []) {
  if (!fs.existsSync(dir)) return files;

  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory() && !item.name.startsWith('.')) {
      getPythonFiles(fullPath, files);
    } else if (item.name.endsWith('.py')) {
      files.push(fullPath);
    }
  }
  return files;
}

async function checkExperimentConstraints(projectRoot) {
  const results = { passed: [], failed: [], warnings: [] };

  const resourceResults = await checkResourceGuard(projectRoot);
  results.passed.push(...resourceResults.passed);
  results.failed.push(...resourceResults.failed);
  results.warnings.push(...resourceResults.warnings);

  const truthResults = await checkTruthfulnessRedLines(projectRoot);
  results.passed.push(...truthResults.passed);
  results.failed.push(...truthResults.failed);
  results.warnings.push(...truthResults.warnings);

  const envResults = await checkEnvironmentCompatibility(projectRoot);
  results.passed.push(...envResults.passed);
  results.failed.push(...envResults.failed);
  results.warnings.push(...envResults.warnings);

  return results;
}

async function checkPaperConstraints(projectRoot) {
  const results = { passed: [], failed: [], warnings: [] };

  const paperResults = await checkPaperStandards(projectRoot);
  results.passed.push(...paperResults.passed);
  results.failed.push(...paperResults.failed);
  results.warnings.push(...paperResults.warnings);

  const evidenceResults = await checkEvidenceConsistency(projectRoot);
  results.passed.push(...evidenceResults.passed);
  results.failed.push(...evidenceResults.failed);
  results.warnings.push(...evidenceResults.warnings);

  return results;
}

// ============================================================
// CLI 入口
// ============================================================

if (import.meta.url === `file://${process.argv[1]}`) {
  const type = process.argv[2] || 'all';
  const projectRoot = process.argv[3] || process.cwd();

  console.log(`\n🔍 运行约束检查: ${type}`);
  console.log(`📁 项目目录: ${projectRoot}\n`);

  const results = await runConstraintsCheck(type, projectRoot);

  console.log('='.repeat(60));
  console.log('✅ 通过:');
  results.passed.forEach(p => console.log('  ' + p));

  if (results.warnings.length > 0) {
    console.log('\n⚠️ 警告:');
    results.warnings.forEach(w => console.log('  ' + w));
  }

  if (results.failed.length > 0) {
    console.log('\n❌ 失败:');
    results.failed.forEach(f => console.log('  ' + f));
    console.log('\n❌ 约束检查未通过，请修复上述问题');
    process.exit(1);
  }

  console.log('\n✅ 所有约束检查通过!\n');
  process.exit(0);
}

export default runConstraintsCheck;
