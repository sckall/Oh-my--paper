#!/bin/bash
# OMP 插件快速清理脚本
# 在终端（非 Claude Code 内）运行: bash scripts/omp-cleanup.sh

echo "═══════════════════════════════════════════"
echo "  OMP 插件快速清理"
echo "═══════════════════════════════════════════"

# 1. 清除旧版安装记录
echo ""
echo "[1/4] 清除旧版安装记录..."
echo '{"version":2,"plugins":{}}' > ~/.claude/plugins/installed_plugins.json
echo "  ✅ 已清理"

# 2. 删除旧版缓存
echo ""
echo "[2/4] 删除旧版缓存..."
rm -rf ~/.claude/plugins/cache/oh-my-paper/
echo "  ✅ 已删除"

# 3. 删除旧版技能
echo ""
echo "[3/4] 删除旧版技能..."
rm -rf ~/.claude/skills/omp:*
echo "  ✅ 已删除"

# 4. 验证
echo ""
echo "[4/4] 验证清理结果..."
echo ""
echo "  安装列表记录:"
echo "  $(cat ~/.claude/plugins/installed_plugins.json)"
echo ""
echo "  项目目录: $(pwd)"
echo "  插件版本: $(cat plugins/oh-my-paper/.claude-plugin/plugin.json 2>/dev/null | grep version | head -1)"

echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ 清理完成！请重启 Claude Code"
echo "═══════════════════════════════════════════"
