#!/usr/bin/env node
/**
 * on-session-start.mjs
 * SessionStart hook — 注入当前任务上下文到 .pipeline/.session-context.md
 *
 * 更新检查是 fire-and-forget（spawn + 3s timeout），不阻塞主流程。
 */

import fs from "node:fs/promises";
import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, "..");
const PROJECT = process.cwd();
const SESSION_CONTEXT = path.join(PROJECT, ".pipeline", ".session-context.md");
const TTL_MS = 5 * 60 * 1000;

// Fire-and-forget 更新检查，3 秒超时自动杀死
function scheduleUpdateCheck() {
  try {
    const checkScript = path.join(PLUGIN_ROOT, "scripts", "check-update.mjs");
    if (!existsSync(checkScript)) return;

    const child = spawn("node", [checkScript], {
      cwd: PROJECT,
      stdio: "ignore",
      detached: false,
    });

    const timer = setTimeout(() => {
      child.kill("SIGKILL");
    }, 3000);

    child.on("exit", (code) => {
      clearTimeout(timer);
      if (code === 0) {
        process.stdout.write("\n🔔 OMP 插件有可用更新！运行 /omp:update 更新\n");
      }
    });

    child.on("error", () => {
      clearTimeout(timer);
    });
  } catch {
    // 更新检查失败不影响主流程
  }
}

function main() {
  const pipelineDir = path.join(PROJECT, ".pipeline");

  // 新用户引导：.pipeline/ 不存在时显示欢迎信息
  if (!existsSync(pipelineDir)) {
    process.stdout.write(
      "\n🔬 " + "=".repeat(50) + "\n" +
      "  Oh My Paper 科研助手已就绪\n" +
      "  " + "=".repeat(50) + "\n\n" +
      "  当前项目未初始化，试试以下命令开始：\n" +
      "  • /omp:help    — 查看所有可用命令\n" +
      "  • /omp:setup   — 初始化研究项目\n" +
      "  • /omp:analyze — 分析期刊论文\n\n"
    );
    return;
  }

  // 如果上下文 5 分钟内已生成，跳过（减少 hook 输出冗余）
  if (existsSync(SESSION_CONTEXT) && Date.now() - statSync(SESSION_CONTEXT).mtimeMs < TTL_MS) {
    return;
  }

  const lines = ["# Session Context (Auto-generated)", ""];

  const briefPath = path.join(pipelineDir, "docs", "research_brief.json");
  if (existsSync(briefPath)) {
    try {
      const brief = JSON.parse(readFileSync(briefPath, "utf8"));
      lines.push(`**当前阶段**: ${brief.currentStage || "unknown"}`);
      lines.push(`**研究主题**: ${brief.topic || ""}`);
      lines.push("");
    } catch {
      // research_brief 文件解析失败，跳过
    }
  }

  // 多项目模式：读取 .omp.yml 显示当前项目名
  const ompYmlPath = path.join(PROJECT, ".omp.yml");
  if (existsSync(ompYmlPath)) {
    try {
      const yml = readFileSync(ompYmlPath, "utf8");
      const activeMatch = yml.match(/active_project:\s*(\S+)/);
      if (activeMatch) {
        lines.push(`**多项目模式** — 当前项目: \`${activeMatch[1]}\``);
        lines.push("");
      }
    } catch {
      // .omp.yml 文件不存在或格式错误，跳过
    }
  }

  const contextPath = path.join(pipelineDir, "memory", "execution_context.md");
  if (existsSync(contextPath)) {
    const content = readFileSync(contextPath, "utf8").trim();
    if (content) {
      lines.push("## 当前任务");
      lines.push(content.split("\n").slice(0, 30).join("\n"));
      lines.push("");
    }
  }

  const handoffPath = path.join(pipelineDir, "memory", "agent_handoff.md");
  if (existsSync(handoffPath)) {
    const content = readFileSync(handoffPath, "utf8");
    const matches = [...content.matchAll(/^## Handoff:.+$/gm)];
    if (matches.length > 0) {
      const last = content.slice(matches[matches.length - 1].index).trim();
      lines.push("## 上一步交接");
      lines.push(last.split("\n").slice(0, 10).join("\n"));
      lines.push("");
    }
  }

  lines.push(`_生成时间: ${new Date().toISOString()}_`);
  lines.push("");

  // 判断是否有历史工作：agent_handoff.md 有内容说明有上一次会话
  const hasHistory = existsSync(handoffPath) && readFileSync(handoffPath, "utf8").trim().length > 0;

  if (hasHistory) {
    // 有历史工作 → 继续上次，不反复问角色
    lines.push("## 启动指令");
    lines.push("");
    lines.push("检测到 Oh My Paper 研究项目。上次会话有未完成的工作，请用 `AskUserQuestion` 询问用户：");
    lines.push("");
    lines.push("- `继续上次的工作` — 读取上一步交接内容，自动切换对应角色继续推进");
    lines.push("- `切换到其他角色` — 显示角色列表供选择");
    lines.push("- `查看当前状态` — 展示当前阶段、任务和进度");
    lines.push("");
    lines.push("用户选择后，读取对应角色的记忆文件，以该角色身份开始工作。");
  } else {
    // 首次初始化或 clean start → 问角色
    lines.push("## 启动指令");
    lines.push("");
    lines.push("检测到 Oh My Paper 研究项目。请立即用 `AskUserQuestion` 询问用户今天的工作模式，选项如下：");
    lines.push("");
    lines.push("- `统筹规划` — 以 Conductor 身份：查看全局进展，决定下一步，评审产出");
    lines.push("- `文献调研` — 以 Literature Scout 身份：搜索论文，整理 literature_bank");
    lines.push("- `实验执行` — 以 Experiment Driver 身份：设计/实现/运行实验，追踪结果");
    lines.push("- `论文写作` — 以 Paper Writer 身份：撰写章节，生成图表，审查引用");
    lines.push("- `论文评审` — 以 Reviewer 身份：同行评审，输出 review_log");
    lines.push("- `直接告诉我要做什么` — 跳过角色选择");
    lines.push("");
    lines.push("用户选择后，读取对应角色的记忆文件，以该角色身份开始工作。");
  }

  const output = lines.join("\n");

  // 输出到 stdout 供 Claude Code SessionStart hook 读取
  process.stdout.write(output + "\n");

  // 同时写文件备用
  fs.mkdir(path.dirname(SESSION_CONTEXT), { recursive: true })
    .then(() => fs.writeFile(SESSION_CONTEXT, output, "utf8"))
    .catch(() => {});

  // 每日更新检查（fire-and-forget，放在最后，不阻塞主流程）
  const lastCheckFile = path.join(pipelineDir, ".last-update-check");
  const today = new Date().toISOString().split("T")[0];
  let shouldCheck = true;
  if (existsSync(lastCheckFile)) {
    try {
      const lastCheck = readFileSync(lastCheckFile, "utf8").trim();
      if (lastCheck === today) shouldCheck = false;
    } catch {
      // ignore
    }
  }
  if (shouldCheck) {
    scheduleUpdateCheck();
    try {
      writeFileSync(lastCheckFile, today);
    } catch {
      // 写入检查标记失败不影响会话
    }
  }
}

main();

process.on("uncaughtException", (e) => {
  process.stdout.write(`⚠️ OMP on-session-start hook 失败: ${e.message}\n`);
});
