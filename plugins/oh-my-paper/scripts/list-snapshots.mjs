#!/usr/bin/env node
/**
 * list-snapshots.mjs
 * 列出所有可用快照
 * 用法：node list-snapshots.mjs [--json]
 */
import fs from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const PROJECT = process.cwd();
const SNAPSHOT_DIR = path.join(PROJECT, ".pipeline", "memory", "snapshots");

function emit(data) {
  process.stdout.write(data + "\n");
}
function warn(data) {
  process.stderr.write("⚠ " + data + "\n");
}

async function main() {
  const jsonOutput = process.argv.includes("--json");

  if (!existsSync(SNAPSHOT_DIR)) {
    if (jsonOutput) {
      emit(JSON.stringify({ snapshots: [] }));
    } else {
      emit("No snapshots found. Snapshots are created automatically before key operations.");
    }
    process.exit(0);
  }

  const files = (await fs.readdir(SNAPSHOT_DIR))
    .filter(f => f.startsWith("snapshot_") && f.endsWith(".json"))
    .sort()
    .reverse();

  if (files.length === 0) {
    if (jsonOutput) {
      emit(JSON.stringify({ snapshots: [] }));
    } else {
      emit("No snapshots found.");
    }
    process.exit(0);
  }

  if (jsonOutput) {
    const snapshots = files.map(f => {
      try {
        const data = JSON.parse(readFileSync(path.join(SNAPSHOT_DIR, f), "utf8"));
        return {
          file: f,
          timestamp: data.timestamp,
          label: data.label,
          stage: data.stage,
          tasks_summary: data.tasks_summary,
        };
      } catch (e) {
        warn(`unreadable snapshot: ${f} — ${e.message}`);
        return { file: f, error: "unreadable" };
      }
    });
    emit(JSON.stringify({ snapshots }, null, 2));
  } else {
    const lines = [
      "═════════════════════════════════════════════════════════",
      "  📸 Available Snapshots",
      "═════════════════════════════════════════════════════════",
      "",
    ];
    for (const f of files) {
      try {
        const data = JSON.parse(readFileSync(path.join(SNAPSHOT_DIR, f), "utf8"));
        const ts = (data.timestamp || "").replace("T", " ").slice(0, 19);
        const stage = data.stage || "?";
        const tasks = data.tasks_summary;
        const taskStr = tasks ? `tasks: ${tasks.done}/${tasks.total} done` : "";
        emit(`  ${f}`);
        emit(`    Time: ${ts} | Stage: ${stage} | ${taskStr}`);
        emit("");
      } catch (e) {
        warn(`unreadable snapshot: ${f} — ${e.message}`);
        emit(`  ${f}  (unreadable)`);
        emit("");
      }
    }
    emit("═════════════════════════════════════════════════════════");
  }
}

main().catch(err => {
  process.stderr.write(`Error: ${err.message}\n`);
  process.exit(1);
});
