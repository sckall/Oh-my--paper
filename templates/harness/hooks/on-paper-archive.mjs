/**
 * on-paper-archive.mjs
 *
 * PostToolUse(Write) 事件触发。
 * 当检测到 paper/main.tex 或 paper/sections/*.tex 被写入时，
 * 自动归档上一版本到 paper/drafts/，并更新 draft_manifest.json
 *
 * 用法：将此文件复制到项目的 .claude/hooks/ 目录
 */

import fs from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const PROJECT = process.env.OMP_PROJECT_ROOT || process.cwd();

async function main() {
  const toolInput = JSON.parse(process.env.CLAUDE_TOOL_INPUT || "{}");
  const filePath = toolInput.file_path || toolPath || "";

  // 只关心 paper 目录下的 .tex 文件
  if (!filePath.includes("paper/") || !filePath.endsWith(".tex")) return;

  console.error("[on-paper-archive] triggered for:", filePath);

  const paperDir = path.join(PROJECT, "paper");
  const draftsDir = path.join(paperDir, "drafts");
  const diffDir = path.join(paperDir, "diff");
  const manifestPath = path.join(paperDir, "draft_manifest.json");

  // 确保目录存在
  await fs.mkdir(draftsDir, { recursive: true });
  await fs.mkdir(diffDir, { recursive: true });

  // 读取当前版本号
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

  // 归档 main.tex（如果被修改的是 main.tex 或 sections/）
  const mainTexPath = path.join(paperDir, "main.tex");
  const sectionsDir = path.join(paperDir, "sections");

  let sectionsChanged = [];

  if (filePath === mainTexPath || filePath.includes("sections/")) {
    // 归档 main.tex
    if (existsSync(mainTexPath)) {
      const content = readFileSync(mainTexPath, "utf8");
      const archivePath = path.join(draftsDir, `${archiveName}_main.tex`);
      await fs.writeFile(archivePath, content, "utf8");

      // 生成 diff（如果有旧版本）
      if (currentVersion > 0) {
        const prevVersion = manifest.versions.find(v => v.id === `v${currentVersion}`);
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

    // 检查哪些 section 被修改
    try {
      const sections = await fs.readdir(sectionsDir);
      for (const sec of sections) {
        if (sec.endsWith(".tex")) {
          const secPath = path.join(sectionsDir, sec);
          const st = (await fs.stat(secPath)).mtimeMs;
          // 简单策略：所有 section 都标记为本次可能修改
          sectionsChanged.push(sec.replace(".tex", ""));
        }
      }
    } catch {}
  }

  // 更新 manifest
  const wordCount = await countWords(mainTexPath);
  const newEntry = {
    id: versionId,
    timestamp: timestamp,
    date: new Date().toISOString().slice(0, 16).replace("T", " "),
    sections_changed: sectionsChanged.length ? sectionsChanged : ["main"],
    word_count: wordCount,
    summary: `Auto-archived before write. Sections: ${sectionsChanged.join(", ") || "main"}`,
    archived_file: `${archiveName}_main.tex`
  };

  manifest.versions.unshift(newEntry);
  manifest.current = versionId;

  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2), "utf8");

  // 写 hook-event
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

  console.error(`[on-paper-archive] Archived to ${archiveName}, manifest updated.`);
}

function generateDiff(oldText, newText) {
  const oldLines = oldText.split("\n");
  const newLines = newText.split("\n");
  const diff = [];

  diff.push(`# Diff Report`);
  diff.push(`**Generated**: ${new Date().toISOString()}`);
  diff.push(`\n## Statistics`);
  diff.push(`- Old version lines: ${oldLines.length}`);
  diff.push(`- New version lines: ${newLines.length}`);
  diff.push(`- Net change: ${newLines.length - oldLines.length} lines`);
  diff.push(`\n## Changed Sections (line-based)`);

  const maxLen = Math.max(oldLines.length, newLines.length);
  let changedCount = 0;

  for (let i = 0; i < maxLen; i++) {
    const oldLine = oldLines[i] || "";
    const newLine = newLines[i] || "";
    if (oldLine !== newLine) {
      changedCount++;
      if (changedCount <= 50) { // 最多显示50处变化
        diff.push(`\n--- Line ${i + 1}`);
        diff.push(`- ${oldLine.substring(0, 100)}${oldLine.length > 100 ? "..." : ""}`);
        diff.push(`+ ${newLine.substring(0, 100)}${newLine.length > 100 ? "..." : ""}`);
      }
    }
  }

  if (changedCount > 50) {
    diff.push(`\n... and ${changedCount - 50} more changes`);
  }

  diff.push(`\n## Summary`);
  diff.push(`Total changed lines: ${changedCount}`);

  return diff.join("\n");
}

async function countWords(texPath) {
  if (!existsSync(texPath)) return 0;
  const content = readFileSync(texPath, "utf8");
  // 简单统计：移除 LaTeX 命令后统计词数
  const text = content
    .replace(/\\[a-zA-Z]+\{[^}]*\}/g, "")
    .replace(/\\[a-zA-Z]+/g, "")
    .replace(/\{[^}]*\}/g, "")
    .replace(/[%#$_^]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return text.split(" ").filter(w => w.length > 0).length;
}

main().catch(() => {
  console.error("[on-paper-archive] Error:", arguments);
  process.exit(0);
});
