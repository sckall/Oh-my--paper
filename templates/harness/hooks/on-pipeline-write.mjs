/**
 * on-pipeline-write.mjs
 *
 * 合并版 Hook：PostToolUse(Write) 触发
 * 1. 检查 tasks.json 写入 → 触发阶段推进检查（原有逻辑）
 * 2. 检查 paper/*.tex 写入 → 触发论文版本归档（新功能）
 *
 * 使用方式：
 * 将此文件复制到项目 .claude/hooks/ 目录，
 * 然后在 .claude/settings.json 中注册：
 * {
 *   "type": "command",
 *   "command": "node .claude/hooks/on-pipeline-write.mjs"
 * }
 */

import fs from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const PROJECT = process.env.OMP_PROJECT_ROOT || process.cwd();

async function main() {
  const toolInput = JSON.parse(process.env.CLAUDE_TOOL_INPUT || "{}");
  const filePath = toolInput.file_path || toolInput.path || "";

  // 两个任务并行执行
  await Promise.allSettled([
    checkStageTransition(filePath),
    checkPaperArchive(filePath),
  ]);
}

// ─────────────────────────────────────────────
// 任务1：阶段推进检查（来自 on-stage-transition）
// ─────────────────────────────────────────────
async function checkStageTransition(filePath) {
  if (!filePath.includes("tasks.json")) return;

  const tasksPath = path.join(PROJECT, ".pipeline", "tasks", "tasks.json");
  if (!existsSync(tasksPath)) return;

  let tasks;
  try {
    tasks = JSON.parse(readFileSync(tasksPath, "utf8"));
  } catch {
    return;
  }

  const briefPath = path.join(PROJECT, ".pipeline", "docs", "research_brief.json");
  let currentStage = "unknown";
  if (existsSync(briefPath)) {
    try {
      const brief = JSON.parse(readFileSync(briefPath, "utf8"));
      currentStage = brief.currentStage || "unknown";
    } catch {}
  }

  const stageTasks = (tasks.tasks || []).filter((t) => t.stage === currentStage);
  if (stageTasks.length === 0) return;

  const doneTasks = stageTasks.filter((t) => t.status === "done");
  const allDone = doneTasks.length === stageTasks.length;
  if (!allDone) return;

  const statePath = path.join(PROJECT, ".pipeline", "memory", "orchestrator_state.md");
  const timestamp = new Date().toISOString().slice(0, 16).replace("T", " ");
  const notice = `\n⚠️ [${timestamp}] 阶段 '${currentStage}' 的所有 ${stageTasks.length} 个任务已完成。Orchestrator 应评审并决定是否推进到下一阶段。\n`;

  await fs.mkdir(path.dirname(statePath), { recursive: true });
  await fs.appendFile(statePath, notice, "utf8");

  const eventsDir = path.join(PROJECT, ".pipeline", ".hook-events");
  await fs.mkdir(eventsDir, { recursive: true });
  await fs.writeFile(
    path.join(eventsDir, `${Date.now()}.json`),
    JSON.stringify({ type: "stage-complete", stage: currentStage, timestamp: Date.now() }),
    "utf8"
  );
}

// ─────────────────────────────────────────────
// 任务2：论文版本归档（新功能）
// ─────────────────────────────────────────────
async function checkPaperArchive(filePath) {
  if (!filePath.includes("paper/") || !filePath.endsWith(".tex")) return;

  const paperDir = path.join(PROJECT, "paper");
  const draftsDir = path.join(paperDir, "drafts");
  const diffDir = path.join(paperDir, "diff");
  const manifestPath = path.join(paperDir, "draft_manifest.json");

  await fs.mkdir(draftsDir, { recursive: true });
  await fs.mkdir(diffDir, { recursive: true });

  let currentVersion = 0;
  let manifest = { current: null, versions: [] };

  if (existsSync(manifestPath)) {
    try {
      manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
      const latest = manifest.versions[0];
      if (latest) {
        const v = parseInt(latest.id.replace("v", ""));
        currentVersion = isNaN(v) ? 0 : v;
      }
    } catch {}
  }

  const newVersion = currentVersion + 1;
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const versionId = `v${newVersion}`;
  const archiveName = `${versionId}_${timestamp}`;

  const mainTexPath = path.join(paperDir, "main.tex");
  const sectionsDir = path.join(paperDir, "sections");

  // 归档 main.tex
  if (existsSync(mainTexPath)) {
    const content = readFileSync(mainTexPath, "utf8");
    const archivePath = path.join(draftsDir, `${archiveName}_main.tex`);
    await fs.writeFile(archivePath, content, "utf8");

    // 生成 diff（对比上一版本）
    if (currentVersion > 0) {
      const prevVersion = manifest.versions[0];
      if (prevVersion) {
        const prevPath = path.join(draftsDir, `${prevVersion.id}_${prevVersion.timestamp}_main.tex`);
        if (existsSync(prevPath)) {
          const prevContent = readFileSync(prevPath, "utf8");
          const diff = generateDiff(prevContent, content);
          const diffPath = path.join(diffDir, `v${currentVersion}_vs_${versionId}.md`);
          await fs.writeFile(diffPath, diff, "utf8");
        }
      }
    }
  }

  // 统计修改的 sections
  let sectionsChanged = [];
  if (filePath.includes("sections/")) {
    try {
      const sections = await fs.readdir(sectionsDir);
      sectionsChanged = sections.filter(s => s.endsWith(".tex")).map(s => s.replace(".tex", ""));
    } catch {}
  } else if (filePath === mainTexPath) {
    sectionsChanged = ["main"];
  }

  const wordCount = await countWords(mainTexPath);

  const newEntry = {
    id: versionId,
    timestamp: timestamp,
    date: new Date().toISOString().slice(0, 16).replace("T", " "),
    sections_changed: sectionsChanged.length ? sectionsChanged : ["main"],
    word_count: wordCount,
    summary: `Auto-archived before write. Sections: ${sectionsChanged.join(", ") || "main"}`,
    archived_file: `${archiveName}_main.tex`,
  };

  manifest.versions.unshift(newEntry);
  manifest.current = versionId;

  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2), "utf8");

  const eventsDir = path.join(PROJECT, ".pipeline", ".hook-events");
  await fs.mkdir(eventsDir, { recursive: true });
  await fs.writeFile(
    path.join(eventsDir, `${Date.now()}.json`),
    JSON.stringify({
      type: "paper-archived",
      version: versionId,
      archived_file: `${archiveName}_main.tex`,
      word_count: wordCount,
      timestamp: Date.now(),
    }),
    "utf8"
  );

  console.error(`[on-pipeline-write] Paper archived to ${archiveName}, manifest updated.`);
}

// ─────────────────────────────────────────────
// 辅助函数
// ─────────────────────────────────────────────
function generateDiff(oldText, newText) {
  const oldLines = oldText.split("\n");
  const newLines = newText.split("\n");
  const diff = [];
  const maxLen = Math.max(oldLines.length, newLines.length);
  let changedCount = 0;

  diff.push(`# Diff Report — ${new Date().toISOString()}`);
  diff.push(`\n## Statistics`);
  diff.push(`- Old version lines: ${oldLines.length}`);
  diff.push(`- New version lines: ${newLines.length}`);
  diff.push(`- Net change: ${newLines.length - oldLines.length} lines`);
  diff.push(`\n## Changed Lines`);

  for (let i = 0; i < maxLen; i++) {
    const oldLine = oldLines[i] || "";
    const newLine = newLines[i] || "";
    if (oldLine !== newLine) {
      changedCount++;
      if (changedCount <= 50) {
        diff.push(`\n--- Line ${i + 1}`);
        diff.push(`- ${oldLine.substring(0, 120)}${oldLine.length > 120 ? "..." : ""}`);
        diff.push(`+ ${newLine.substring(0, 120)}${newLine.length > 120 ? "..." : ""}`);
      }
    }
  }

  if (changedCount > 50) diff.push(`\n... and ${changedCount - 50} more changes`);
  diff.push(`\n## Total: ${changedCount} changed lines`);

  return diff.join("\n");
}

async function countWords(texPath) {
  if (!existsSync(texPath)) return 0;
  const content = readFileSync(texPath, "utf8");
  const text = content
    .replace(/\\[a-zA-Z]+\{[^}]*\}/g, "")
    .replace(/\\[a-zA-Z]+/g, "")
    .replace(/\{[^}]*\}/g, "")
    .replace(/[%#$_^]/g, "")
    .replace(/\s+/g, " ").trim();
  return text.split(" ").filter(w => w.length > 0).length;
}

main().catch(() => process.exit(0));
