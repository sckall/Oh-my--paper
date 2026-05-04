#!/usr/bin/env node
/**
 * on-stage-transition.mjs
 * PostToolUse(Write) hook — 检测阶段任务全部完成时提示推进
 */
import fs from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, "..");
const PROJECT = process.cwd();

async function main() {
  // 阶段切换前打快照
  try {
    const scriptPath = path.join(PLUGIN_ROOT, "scripts", "take-snapshot.mjs");
    if (existsSync(scriptPath)) {
      execSync(`node "${scriptPath}" before-stage-transition`, { stdio: "pipe" });
    }
  } catch {
    // 快照创建失败不影响主流程
  }

  const toolInput = JSON.parse(process.env.CLAUDE_TOOL_INPUT || "{}");
  const filePath = toolInput.file_path || toolInput.path || "";
  if (!filePath.includes("tasks.json")) return;

  const tasksPath = path.join(PROJECT, ".pipeline", "tasks", "tasks.json");
  if (!existsSync(tasksPath)) return;

  let tasks;
  try { tasks = JSON.parse(readFileSync(tasksPath, "utf8")); } catch { return; }

  const briefPath = path.join(PROJECT, ".pipeline", "docs", "research_brief.json");
  let currentStage = "unknown";
  if (existsSync(briefPath)) {
    try { currentStage = JSON.parse(readFileSync(briefPath, "utf8")).currentStage || "unknown"; } catch {
      // research_brief 不存在或格式错误，使用默认值
    }
  }

  const stageTasks = (tasks.tasks || []).filter(t => t.stage === currentStage);
  if (!stageTasks.length) return;
  if (stageTasks.filter(t => t.status === "done").length !== stageTasks.length) return;

  const statePath = path.join(PROJECT, ".pipeline", "memory", "orchestrator_state.md");
  const ts = new Date().toISOString().slice(0, 16).replace("T", " ");
  await fs.mkdir(path.dirname(statePath), { recursive: true });
  await fs.appendFile(
    statePath,
    `\n⚠️ [${ts}] 阶段 '${currentStage}' 所有任务已完成，请运行 /omp:plan 评审并决定是否推进。\n`,
    "utf8"
  );

  const eventsDir = path.join(PROJECT, ".pipeline", ".hook-events");
  await fs.mkdir(eventsDir, { recursive: true });
  await fs.writeFile(
    path.join(eventsDir, `${Date.now()}.json`),
    JSON.stringify({ type: "stage-complete", stage: currentStage, timestamp: Date.now() }),
    "utf8"
  );
}

main().catch((e) => {
  process.stdout.write(`⚠️ OMP on-stage-transition hook 失败: ${e.message}\n`);
  process.exit(0);
});
