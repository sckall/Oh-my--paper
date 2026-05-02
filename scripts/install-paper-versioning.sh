#!/bin/bash
# install-paper-versioning.sh
# 为 Oh My Paper 项目添加论文版本管理功能
# 用法: bash install-paper-versioning.sh <项目路径>

set -e

PROJECT_DIR="${1:-.}"

echo "📦 为项目安装论文版本管理..."

# 1. 创建必要的目录
mkdir -p "$PROJECT_DIR/paper/drafts"
mkdir -p "$PROJECT_DIR/paper/diff"
mkdir -p "$PROJECT_DIR/.pipeline/.hook-events"

# 2. 初始化 draft_manifest.json
if [ ! -f "$PROJECT_DIR/paper/draft_manifest.json" ]; then
  cat > "$PROJECT_DIR/paper/draft_manifest.json" << 'EOF'
{
  "current": null,
  "versions": [],
  "note": "此文件由 on-pipeline-write hook 自动管理，请勿手动编辑"
}
EOF
  echo "✅ 已创建 paper/draft_manifest.json"
else
  echo "ℹ️  draft_manifest.json 已存在，跳过"
fi

# 3. 复制 hook 文件
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_HOOK="$SCRIPT_DIR/../templates/harness/hooks/on-pipeline-write.mjs"

if [ -f "$TEMPLATE_HOOK" ]; then
  mkdir -p "$PROJECT_DIR/.claude/hooks"
  cp "$TEMPLATE_HOOK" "$PROJECT_DIR/.claude/hooks/on-pipeline-write.mjs"
  echo "✅ 已复制 on-pipeline-write.mjs"
else
  echo "⚠️  找不到模板 hook 文件: $TEMPLATE_HOOK"
fi

# 4. 注册 hook 到 settings.json
SETTINGS_FILE="$PROJECT_DIR/.claude/settings.json"

if [ -f "$SETTINGS_FILE" ]; then
  # 检查是否已经注册过
  if grep -q "on-pipeline-write" "$SETTINGS_FILE"; then
    echo "ℹ️  Hook 已注册，跳过"
  else
    # 备份原文件
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
    echo "✅ 已备份 settings.json"
    
    # 使用 node 添加 hook 注册（简化处理，直接追加或替换）
    node - << 'NODESCRIPT'
const fs = require('fs');
const path = process.argv[2];
const settings = JSON.parse(fs.readFileSync(path, 'utf8'));
// 在 PostToolUse hooks 中添加新 hook
if (settings.hooks && settings.hooks.PostToolUse) {
  const existing = settings.hooks.PostToolUse.find(h => 
    h.hooks && h.hooks.some(hook => 
      hook.command && hook.command.includes('on-pipeline-write')
    )
  );
  if (!existing) {
    // 添加到第一个 PostToolUse 条目
    if (settings.hooks.PostToolUse[0]) {
      settings.hooks.PostToolUse[0].hooks.push({
        "matcher": "Write",
        "type": "command",
        "command": "node .claude/hooks/on-pipeline-write.mjs"
      });
    }
  }
}
console.log(JSON.stringify(settings, null, 2));
NODESCRIPT
    echo "$SETTINGS_FILE 已更新"
  fi
else
  echo "⚠️  未找到 settings.json，请手动注册 hook"
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "效果：每次 /omp:write 执行后，paper/main.tex 会自动归档到 paper/drafts/"
echo "查看版本清单：cat paper/draft_manifest.json"
