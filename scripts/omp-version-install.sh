#!/bin/bash
# omp-version-install.sh
# 为 OMP 项目安装论文版本管理模块
# 用法: bash omp-version-install.sh <项目路径>

set -e

PROJECT_DIR="${1:-.}"

echo "📦 安装 OMP 论文版本管理模块..."

# 1. 创建目录结构
mkdir -p "$PROJECT_DIR/paper/drafts"
mkdir -p "$PROJECT_DIR/paper/diffs"
mkdir -p "$PROJECT_DIR/paper/versions/sections"
mkdir -p "$PROJECT_DIR/.pipeline/.hook-events"

# 2. 初始化 manifest
if [ ! -f "$PROJECT_DIR/paper/versions/manifest.json" ]; then
  cat > "$PROJECT_DIR/paper/versions/manifest.json" << 'EOF'
{
  "version": "1.0",
  "current": null,
  "total_versions": 0,
  "last_modified": null,
  "versions": [],
  "stats": {
    "total_words_added": 0,
    "total_revisions": 0,
    "most_changed_section": null
  }
}
EOF
  echo "✅ 已创建 manifest.json"
fi

# 3. 复制版本管理模块
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)/../skills/omp-paper-versioning"
if [ -d "$SKILL_DIR" ]; then
  mkdir -p "$PROJECT_DIR/skills"
  cp -r "$SKILL_DIR" "$PROJECT_DIR/skills/omp-paper-versioning"
  echo "✅ 已复制版本管理模块到 skills/"
fi

# 4. 更新 settings.json 注册 Hook
SETTINGS="$PROJECT_DIR/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
  if ! grep -q "omp-paper-versioning" "$SETTINGS"; then
    echo "ℹ️  需要在 settings.json 中添加 PostToolUse Hook"
    echo "   请手动添加以下内容到 PostToolUse hooks:"
    echo '   { "matcher": "Write", "type": "command", "command": "cd $PROJECT && node skills/omp-paper-versioning/index.mjs archive" }'
  fi
fi

# 5. 测试版本管理
echo ""
echo "🧪 测试版本管理..."
cd "$PROJECT_DIR"
if node skills/omp-paper-versioning/index.mjs stats 2>/dev/null; then
  echo "✅ 版本管理模块工作正常"
else
  echo "⚠️  版本管理模块测试失败，请检查 Node.js 环境"
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "使用方法："
echo "  cd $PROJECT_DIR"
echo "  node skills/omp-paper-versioning/index.mjs history    # 查看版本历史"
echo "  node skills/omp-paper-versioning/index.mjs stats     # 查看统计"
echo "  node skills/omp-paper-versioning/index.mjs graph      # 版本演进图"
echo "  node skills/omp-paper-versioning/index.mjs diff v1 v2 # 对比v1和v2"
echo "  node skills/omp-paper-versioning/index.mjs rollback v2 # 回滚到v2"
