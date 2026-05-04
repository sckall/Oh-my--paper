#!/usr/bin/env node
/**
 * take-snapshot.mjs
 * 在关键操作前创建项目状态快照（保存完整文件内容）
 * 用法：node take-snapshot.mjs [label]
 */
import fs from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const PROJECT = process.cwd();
const SNAPSHOT_DIR = path.join(PROJECT, ".pipeline", "memory", "snapshots");
const MAX_SNAPSHOTS = 20;

const KEY_FILES = [
  "docs/research_brief.json",
  "tasks/tasks.json",
  "memory/project_truth.md",
  "memory/orchestrator_state.md",
  "memory/decision_log.md",
  "memory/execution_context.md",
];

function warn(msg) {
  process.stderr.write("⚠ " + msg + "\n");
}

async function main() {
  const label = process.argv[2] || "auto";
  const pipelineDir = path.join(PROJECT, ".pipeline");

  if (!existsSync(pipelineDir)) {
    process.stderr.write("No .pipeline/ directory found, skipping snapshot.\n");
    process.exit(0);
  }

  await fs.mkdir(SNAPSHOT_DIR, { recursive: true });

  // 收集快照数据（包含完整文件内容）
  const snapshot = {
    timestamp: new Date().toISOString(),
    label,
    stage: "unknown",
    research_brief: null,
    tasks_summary: null,
    files: {},
  };

  // 读取 research_brief.json
  const briefPath = path.join(pipelineDir, "docs", "research_brief.json");
  if (existsSync(briefPath)) {
    try {
      const brief = JSON.parse(readFileSync(briefPath, "utf8"));
      snapshot.stage = brief.currentStage || "unknown";
      snapshot.research_brief = {
        topic: brief.topic || "",
        currentStage: brief.currentStage || "",
        mode: brief.mode || "Legacy",
      };
    } catch (e) {
      warn("failed to parse research_brief.json: " + e.message);
    }
  }

  // 读取 tasks.json 并统计
  const tasksPath = path.join(pipelineDir, "tasks", "tasks.json");
  if (existsSync(tasksPath)) {
    try {
      const tasks = JSON.parse(readFileSync(tasksPath, "utf8"));
      const taskList = tasks.tasks || [];
      snapshot.tasks_summary = {
        total: taskList.length,
        done: taskList.filter(t => t.status === "done").length,
        in_progress: taskList.filter(t => t.status === "in_progress").length,
        pending: taskList.filter(t => t.status === "pending").length,
      };
    } catch {
      warn("任务文件 tasks.json 读取失败");
    }
  }

  // 保存关键文件的完整内容
  for (const relPath of KEY_FILES) {
    const fullPath = path.join(pipelineDir, relPath);
    if (existsSync(fullPath)) {
      try {
        snapshot.files[relPath] = readFileSync(fullPath, "utf8");
      } catch (e) {
        warn(`文件读取失败: ${relPath} — ${e.message}`);
      }
    }
  }

  // 写入快照文件
  const ts = new Date().toISOString().replace(/[-:]/g, "").slice(0, 15);
  const baseName = `snapshot_${ts}_${label}.json`;
  const snapshotFile = path.join(SNAPSHOT_DIR, baseName);
  await fs.writeFile(snapshotFile, JSON.stringify(snapshot, null, 2), "utf8");

  // 清理旧快照（保留最近 MAX_SNAPSHOTS 个）
  const files = (await fs.readdir(SNAPSHOT_DIR))
    .filter(f => f.startsWith("snapshot_") && f.endsWith(".json"))
    .sort()
    .reverse();
  for (const f of files.slice(MAX_SNAPSHOTS)) {
    try {
      await fs.unlink(path.join(SNAPSHOT_DIR, f));
    } catch {
      // 清理旧快照失败不影响主流程
    }
  }

  process.stdout.write(`Snapshot created: ${baseName}\n`);
}

main().catch(err => {
  process.stderr.write(`Snapshot failed: ${err.message}\n`);
  process.exit(0);
});
