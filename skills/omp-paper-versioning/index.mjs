/**
 * omp-paper-versioning/index.mjs
 * OMP 论文版本管理核心执行器
 * 
 * 支持命令：
 *   node index.mjs archive           - 归档当前版本
 *   node index.mjs diff <v1> <v2>    - 对比两个版本
 *   node index.mjs rollback <v>      - 回滚到指定版本
 *   node index.mjs history           - 显示版本历史
 *   node index.mjs stats             - 显示版本统计
 *   node index.mjs graph             - 显示版本演进图
 *   node index.mjs snapshot <note>   - 创建手动快照
 */

import fs from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const PROJECT = process.env.OMP_PROJECT_ROOT || process.cwd();
const PAPER_DIR = path.join(PROJECT, "paper");
const DRAFTS_DIR = path.join(PAPER_DIR, "drafts");
const DIFFS_DIR = path.join(PAPER_DIR, "diffs");
const VERSIONS_DIR = path.join(PAPER_DIR, "versions");
const MANIFEST_PATH = path.join(VERSIONS_DIR, "manifest.json");

// ─────────────────────────────────────────────
// 初始化
// ─────────────────────────────────────────────
async function ensureInit() {
  await Promise.all([
    fs.mkdir(DRAFTS_DIR, { recursive: true }),
    fs.mkdir(DIFFS_DIR, { recursive: true }),
    fs.mkdir(VERSIONS_DIR, { recursive: true }),
  ]);

  if (!existsSync(MANIFEST_PATH)) {
    const initial = {
      version: "1.0",
      current: null,
      total_versions: 0,
      last_modified: null,
      versions: [],
      stats: {
        total_words_added: 0,
        total_revisions: 0,
        most_changed_section: null,
      },
    };
    await fs.writeFile(MANIFEST_PATH, JSON.stringify(initial, null, 2), "utf8");
  }
}

// ─────────────────────────────────────────────
// 读取 manifest
// ─────────────────────────────────────────────
async function readManifest() {
  await ensureInit();
  return JSON.parse(readFileSync(MANIFEST_PATH, "utf8"));
}

async function writeManifest(manifest) {
  manifest.last_modified = new Date().toISOString();
  await fs.writeFile(MANIFEST_PATH, JSON.stringify(manifest, null, 2), "utf8");
}

// ─────────────────────────────────────────────
// 归档当前版本（自动触发）
// ─────────────────────────────────────────────
async function archive(sectionsChanged = ["main"], summary = null) {
  await ensureInit();

  const manifest = await readManifest();
  const mainTexPath = path.join(PAPER_DIR, "main.tex");

  if (!existsSync(mainTexPath)) {
    console.error("[version] main.tex not found, skip archive");
    return;
  }

  const currentVersion = manifest.current
    ? parseInt(manifest.current.replace("v", ""))
    : 0;
  const newVersion = currentVersion + 1;
  const versionId = `v${newVersion}`;
  const timestamp = new Date()
    .toISOString()
    .replace(/[:.]/g, "-")
    .slice(0, 19)
    .replace("T", "_");
  const archiveName = `${versionId}_${timestamp}`;
  const archivePath = path.join(DRAFTS_DIR, `${archiveName}_main.tex`);

  // 读取当前内容
  const content = readFileSync(mainTexPath, "utf8");
  const wordCount = countWords(content);
  const lineCount = content.split("\n").length;

  // 保存归档
  await fs.writeFile(archivePath, content, "utf8");

  // 生成 diff（对比上一版本）
  let diffFile = null;
  if (manifest.current && manifest.versions.length > 0) {
    const prevVersion = manifest.versions[0];
    const prevPath = path.join(DRAFTS_DIR, `${prevVersion.archived_file}`);
    if (existsSync(prevPath)) {
      const prevContent = readFileSync(prevPath, "utf8");
      const diff = generateDiff(prevContent, content, prevVersion.id, versionId);
      const diffPath = path.join(DIFFS_DIR, `v${currentVersion}_vs_${versionId}.md`);
      await fs.writeFile(diffPath, diff, "utf8");
      diffFile = `v${currentVersion}_vs_${versionId}.md`;
    }
  }

  // 构建版本条目
  const entry = {
    id: versionId,
    date: new Date().toISOString(),
    timestamp: timestamp,
    sections_changed: sectionsChanged,
    word_count: wordCount,
    lines: lineCount,
    summary: summary || `Auto-archived. Sections: ${sectionsChanged.join(", ")}`,
    author: "OMP Auto",
    archived_file: `${archiveName}_main.tex`,
    diff_file: diffFile,
  };

  // 更新 manifest
  manifest.versions.unshift(entry);
  manifest.current = versionId;
  manifest.total_versions = manifest.versions.length;

  // 统计
  if (manifest.versions.length >= 2) {
    const prev = manifest.versions[1];
    manifest.stats.total_words_added += wordCount - prev.word_count;
  } else {
    manifest.stats.total_words_added = wordCount;
  }

  // 更新最常修改章节
  const sectionCounts = {};
  for (const v of manifest.versions) {
    for (const s of v.sections_changed) {
      sectionCounts[s] = (sectionCounts[s] || 0) + 1;
    }
  }
  const sorted = Object.entries(sectionCounts).sort((a, b) => b[1] - a[1]);
  if (sorted.length > 0) manifest.stats.most_changed_section = sorted[0][0];

  await writeManifest(manifest);

  console.log(`[version] Archived to ${versionId}, word_count=${wordCount}, lines=${lineCount}`);

  return entry;
}

// ─────────────────────────────────────────────
// 对比两个版本
// ─────────────────────────────────────────────
async function diff(v1Id, v2Id) {
  const manifest = await readManifest();

  const v1 = manifest.versions.find((v) => v.id === v1Id);
  const v2 = manifest.versions.find((v) => v.id === v2Id);

  if (!v1 || !v2) {
    console.error(`[version] Version not found: ${v1Id} or ${v2Id}`);
    return;
  }

  const v1Path = path.join(DRAFTS_DIR, v1.archived_file);
  const v2Path = path.join(DRAFTS_DIR, v2.archived_file);

  if (!existsSync(v1Path) || !existsSync(v2Path)) {
    console.error("[version] Archived files not found");
    return;
  }

  const v1Content = readFileSync(v1Path, "utf8");
  const v2Content = readFileSync(v2Path, "utf8");

  const report = generateDiff(v1Content, v2Content, v1Id, v2Id);

  console.log(report);

  return report;
}

// ─────────────────────────────────────────────
// 回滚到指定版本
// ─────────────────────────────────────────────
async function rollback(targetId) {
  await ensureInit();

  const manifest = await readManifest();

  const target = manifest.versions.find((v) => v.id === targetId);
  if (!target) {
    console.error(`[version] Version not found: ${targetId}`);
    return;
  }

  const mainTexPath = path.join(PAPER_DIR, "main.tex");
  const targetPath = path.join(DRAFTS_DIR, target.archived_file);

  if (!existsSync(targetPath)) {
    console.error("[version] Target archived file not found");
    return;
  }

  // 备份当前
  const backupTimestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const backupPath = path.join(
    DRAFTS_DIR,
    `rollback_backup_${backupTimestamp}_main.tex`
  );
  if (existsSync(mainTexPath)) {
    await fs.copyFile(mainTexPath, backupPath);
  }

  // 回滚
  await fs.copyFile(targetPath, mainTexPath);

  // 记录回滚（作为新版本）
  const currentVersion = manifest.current
    ? parseInt(manifest.current.replace("v", ""))
    : 0;
  const newVersion = currentVersion + 1;
  const rollbackEntry = {
    id: `v${newVersion}`,
    date: new Date().toISOString(),
    timestamp: backupTimestamp,
    sections_changed: ["main"],
    word_count: target.word_count,
    lines: target.lines,
    summary: `Rollback to ${targetId} from v${currentVersion}`,
    author: "OMP Rollback",
    archived_file: target.archived_file,
    type: "rollback",
    rollback_from: manifest.current,
    rollback_to: targetId,
  };

  manifest.versions.unshift(rollbackEntry);
  manifest.current = `v${newVersion}`;
  manifest.total_versions = manifest.versions.length;

  await writeManifest(manifest);

  console.log(`[version] Rolled back to ${targetId}, backed up to ${backupPath}`);
}

// ─────────────────────────────────────────────
// 显示版本历史
// ─────────────────────────────────────────────
async function history() {
  const manifest = await readManifest();

  if (manifest.versions.length === 0) {
    console.log("No versions yet. Run /omp:write to create the first version.");
    return;
  }

  console.log("\n📜 Paper Version History");
  console.log("═".repeat(60));
  console.log(
    `Current: ${manifest.current || "none"} | Total: ${manifest.total_versions} versions\n`
  );

  for (const v of manifest.versions) {
    const date = new Date(v.date).toLocaleString("zh-CN");
    const marker = v.id === manifest.current ? "👉 " : "  ";
    const type = v.type === "rollback" ? " [ROLLBACK]" : "";
    console.log(
      `${marker}${v.id} | ${date} | ${v.word_count} words | ${v.lines} lines${type}`
    );
    console.log(`   └─ ${v.summary}`);
    if (v.diff_file) {
      console.log(`   └─ diff: ${v.diff_file}`);
    }
    console.log("");
  }
}

// ─────────────────────────────────────────────
// 显示版本统计
// ─────────────────────────────────────────────
async function stats() {
  const manifest = await readManifest();

  console.log("\n📊 Paper Version Statistics");
  console.log("═".repeat(60));
  console.log(`Total versions: ${manifest.total_versions}`);
  console.log(`Current version: ${manifest.current || "none"}`);
  console.log(
    `Total words (latest): ${
      manifest.versions[0]?.word_count || 0
    }`
  );
  console.log(
    `Net words added: +${manifest.stats.total_words_added}`
  );
  console.log(
    `Most changed section: ${manifest.stats.most_changed_section || "N/A"}`
  );

  if (manifest.versions.length >= 2) {
    console.log("\n📈 Word Count Trend:");
    const sorted = [...manifest.versions].reverse();
    for (const v of sorted) {
      const bar = "█".repeat(Math.floor(v.word_count / 200));
      console.log(`  ${v.id.padEnd(4)} ${v.word_count.toString().padStart(5)} words  ${bar}`);
    }
  }
}

// ─────────────────────────────────────────────
// 生成版本演进图
// ─────────────────────────────────────────────
async function graph() {
  const manifest = await readManifest();

  console.log("\n📍 Paper Version Evolution Graph");
  console.log("═".repeat(60));

  if (manifest.versions.length === 0) {
    console.log("No versions yet.");
    return;
  }

  const sorted = [...manifest.versions].reverse();

  for (let i = 0; i < sorted.length; i++) {
    const v = sorted[i];
    const isFirst = i === 0;
    const prefix = isFirst ? "  v" : "  │";
    const node = `v${v.id.replace("v", "")}`;
    const conn = isFirst ? "●" : "○";
    const date = new Date(v.date).toLocaleDateString("zh-CN");

    console.log(`${prefix}   ${conn} ${node} (${date}) - ${v.summary}`);

    if (!isFirst) {
      console.log(`  │`);
    }
  }
}

// ─────────────────────────────────────────────
// 创建手动快照
// ─────────────────────────────────────────────
async function snapshot(note) {
  await archive(["snapshot"], `Manual snapshot: ${note}`);
  console.log(`[version] Snapshot created: ${note}`);
}

// ─────────────────────────────────────────────
// 辅助函数
// ─────────────────────────────────────────────
function countWords(text) {
  const cleaned = text
    .replace(/\\[a-zA-Z]+\{[^}]*\}/g, "")
    .replace(/\\[a-zA-Z]+/g, "")
    .replace(/\{[^}]*\}/g, "")
    .replace(/[%#$_^]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned.split(" ").filter((w) => w.length > 0).length;
}

function generateDiff(oldText, newText, v1Id, v2Id) {
  const oldLines = oldText.split("\n");
  const newLines = newText.split("\n");
  const diff = [];
  const maxLen = Math.max(oldLines.length, newLines.length);
  let changedCount = 0;
  let addedCount = 0;
  let removedCount = 0;

  diff.push(`# Version Diff Report`);
  diff.push(`**Compare**: ${v1Id} → ${v2Id}`);
  diff.push(`**Generated**: ${new Date().toISOString()}`);
  diff.push("");
  diff.push("## Statistics");
  diff.push(`| Metric | ${v1Id} | ${v2Id} | Change |`);
  diff.push(`|--------|-------|-------|--------|`);
  diff.push(`| Lines | ${oldLines.length} | ${newLines.length} | ${newLines.length - oldLines.length >= 0 ? "+" : ""}${newLines.length - oldLines.length} |`);
  diff.push(`| Words | ${countWords(oldText)} | ${countWords(newText)} | - |`);
  diff.push("");
  diff.push("## Changed Lines");

  for (let i = 0; i < maxLen; i++) {
    const oldLine = oldLines[i] || "";
    const newLine = newLines[i] || "";

    if (oldLine !== newLine) {
      changedCount++;
      if (newLine && oldLine === "") addedCount++;
      if (oldLine && newLine === "") removedCount++;

      if (changedCount <= 100) {
        diff.push("");
        diff.push(`### Line ${i + 1}`);
        if (oldLine) diff.push(`- ${oldLine.substring(0, 150)}${oldLine.length > 150 ? "..." : ""}`);
        if (newLine) diff.push(`+ ${newLine.substring(0, 150)}${newLine.length > 150 ? "..." : ""}`);
      }
    }
  }

  diff.push("");
  diff.push("## Summary");
  diff.push(`- Total changed lines: ${changedCount}`);
  diff.push(`- Lines added: ${addedCount}`);
  diff.push(`- Lines removed: ${removedCount}`);
  if (changedCount > 100) diff.push(`- (showing first 100 changes)`);

  return diff.join("\n");
}

// ─────────────────────────────────────────────
// CLI 入口
// ─────────────────────────────────────────────
const [command, arg1, arg2] = process.argv.slice(2);

switch (command) {
  case "archive":
    await archive(
      arg1 ? arg1.split(",") : ["main"],
      arg2 || null
    );
    break;

  case "diff":
    if (!arg1 || !arg2) {
      console.error("Usage: node index.mjs diff <v1> <v2>");
    } else {
      await diff(arg1, arg2);
    }
    break;

  case "rollback":
    if (!arg1) {
      console.error("Usage: node index.mjs rollback <version>");
    } else {
      await rollback(arg1);
    }
    break;

  case "history":
    await history();
    break;

  case "stats":
    await stats();
    break;

  case "graph":
    await graph();
    break;

  case "snapshot":
    await snapshot(arg1 || "manual snapshot");
    break;

  default:
    console.log(`
📜 OMP Paper Version Manager

Usage:
  node index.mjs archive [sections] [note]   Archive current version
  node index.mjs diff <v1> <v2>             Compare two versions
  node index.mjs rollback <version>          Rollback to version
  node index.mjs history                     Show version history
  node index.mjs stats                       Show version statistics
  node index.mjs graph                       Show version evolution graph
  node index.mjs snapshot <note>             Create manual snapshot

Examples:
  node index.mjs archive "abstract,method" "重写了方法论"
  node index.mjs diff v1 v3
  node index.mjs rollback v2
    `);
}

export { archive, diff, rollback, history, stats, graph, snapshot };
