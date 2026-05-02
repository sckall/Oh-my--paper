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

async function main() {
  const jsonOutput = process.argv.includes("--json");

  if (!existsSync(SNAPSHOT_DIR)) {
    if (jsonOutput) {
      console.log(JSON.stringify({ snapshots: [] }));
    } else {
      process.stdout.write("No snapshots found. Snapshots are created automatically before key operations.\n");
    }
    process.exit(0);
  }

  const files = (await fs.readdir(SNAPSHOT_DIR))
    .filter(f => f.startsWith("snapshot_") && f.endsWith(".json"))
    .sort()
    .reverse();

  if (files.length === 0) {
    if (jsonOutput) {
      console.log(JSON.stringify({ snapshots: [] }));
    } else {
      process.stdout.write("No snapshots found.\n");
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
      } catch {
        return { file: f, error: "unreadable" };
      }
    });
    console.log(JSON.stringify({ snapshots }, null, 2));
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
        lines.push(`  ${f}`);
        lines.push(`    Time: ${ts} | Stage: ${stage} | ${taskStr}`);
        lines.push("");
      } catch {
        lines.push(`  ${f}  (unreadable)`);
        lines.push("");
      }
    }
    lines.push("═════════════════════════════════════════════════════════");
    process.stdout.write(lines.join("\n") + "\n");
  }
}

main().catch(err => {
  process.stderr.write(`Error: ${err.message}\n`);
  process.exit(1);
});
