#!/bin/bash
# ============================================
# 上游同步脚本
# 用于从官方 Hermes 仓库拉取更新并重新应用品牌变更
# 创建时间: 2026-05-14 01:35:20
# ============================================

set -e

echo "============================================"
echo "  上游同步脚本"
echo "============================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
UPSTREAM_REPO="https://github.com/nousresearch/hermes-agent.git"
UPSTREAM_BRANCH="main"

echo -e "${BLUE}1. 添加/更新 upstream 远程仓库...${NC}"
if git remote | grep -q "^upstream$"; then
    echo "   upstream 已存在"
else
    git remote add upstream $UPSTREAM_REPO
    echo -e "${GREEN}   ✓ 已添加 upstream${NC}"
fi

echo ""
echo -e "${BLUE}2. 拉取官方更新...${NC}"
git fetch upstream

echo ""
echo -e "${BLUE}3. 切换到 main 分支...${NC}"
git checkout main

echo ""
echo -e "${BLUE}4. 合并官方更新...${NC}"
echo -e "${YELLOW}   注意: 如遇冲突，请手动解决${NC}"
git merge upstream/$UPSTREAM_BRANCH --no-edit || {
    echo ""
    echo -e "${RED}⚠ 合并过程出现冲突${NC}"
    echo ""
    echo "冲突处理指南："
    echo "  1. 打开冲突文件，查找 <<<<<<< 标记"
    echo "  2. 保留你的品牌修改（~/..anydeals 等）"
    echo "  3. 保留官方的新功能代码"
    echo "  4. 删除 <<<<<<<、=======、>>>>>>> 标记"
    echo "  5. 执行: git add . && git commit -m 'merge: 同步官方更新'"
    echo "  6. 重新运行此脚本的 rebrand 步骤（--rebrand-only）"
    echo ""
    exit 1
}

echo ""
echo -e "${BLUE}5. 检查上游是否有新的 hermes 引用...${NC}"

# Files renamed in our fork — if upstream adds new files with old names,
# they will re-appear as untracked/conflicting paths.
RENAMED_PATHS=(
    "hermes_bootstrap.py"
    "hermes_constants.py"
    "hermes_logging.py"
    "hermes_state.py"
    "hermes_time.py"
    "hermes_cli/"
    "tests/hermes_cli/"
    "tests/hermes_state/"
    "tests/test_hermes_bootstrap.py"
    "tests/test_hermes_constants.py"
    "tests/test_hermes_logging.py"
    "tests/test_hermes_state.py"
    "tests/test_hermes_state_wal_fallback.py"
    "tests/test_hermes_home_profile_warning.py"
    "setup-hermes.sh"
    "scripts/hermes-gateway"
    "environments/hermes_base_env.py"
    "environments/hermes_swe_env/"
    "environments/tool_call_parsers/hermes_parser.py"
    "plugins/hermes-achievements/"
    "skills/productivity/google-workspace/scripts/_hermes_home.py"
    "optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py"
)

for path in "${RENAMED_PATHS[@]}"; do
    if [ -e "$path" ]; then
        echo -e "${RED}  ⚠ 检测到已重命名路径重新出现: $path${NC}"
        echo "     请在提交前手动处理（合并或删除）"
    fi
done

echo ""
echo -e "${BLUE}6. 应用品牌变更（hermes → AnyDeals）...${NC}"

# Re-apply rebrand sed to files that upstream may have touched.
# This is the same set of replacements as the initial rebrand.
rebrand_file() {
    local f="$1"
    sed -i '' \
        -e 's|hermes-agent|anydeals-agent|g' \
        -e 's|hermes-acp|anydeals-acp|g' \
        -e 's|HERMES_BUNDLED_SKILLS|ANYDEALS_BUNDLED_SKILLS|g' \
        -e 's|HERMES_BUNDLED_PLUGINS|ANYDEALS_BUNDLED_PLUGINS|g' \
        -e 's|HERMES_WEB_DIST|ANYDEALS_WEB_DIST|g' \
        -e 's|HERMES_TUI_DIR|ANYDEALS_TUI_DIR|g' \
        -e 's|HERMES_PYTHON|ANYDEALS_PYTHON|g' \
        -e 's|HERMES_NODE|ANYDEALS_NODE|g' \
        -e 's|HERMES_REVISION|ANYDEALS_REVISION|g' \
        -e 's|HERMES_HOME|ANYDEALS_HOME|g' \
        -e 's|HERMES_MANAGED|ANYDEALS_MANAGED|g' \
        -e 's|HERMES_UID|ANYDEALS_UID|g' \
        -e 's|HERMES_GID|ANYDEALS_GID|g' \
        -e 's|hermes_cli|AnyDeals_cli|g' \
        -e 's|hermes_bootstrap|AnyDeals_bootstrap|g' \
        -e 's|hermes_constants|AnyDeals_constants|g' \
        -e 's|hermes_logging|AnyDeals_logging|g' \
        -e 's|hermes_state|AnyDeals_state|g' \
        -e 's|hermes_time|AnyDeals_time|g' \
        -e 's|hermes_home|anydeals_home|g' \
        -e 's|_hermes_npm|_anydeals_npm|g' \
        -e 's|hermesVenv|anydealsVenv|g' \
        -e 's|hermesNpmLib|anydealsNpmLib|g' \
        -e 's|hermesTui|anydealsTui|g' \
        -e 's|hermesWeb|anydealsWeb|g' \
        -e 's|hermesAgent|anydealsAgent|g' \
        -e 's|hermesWithExtra|anydealsWithExtra|g' \
        -e 's|hermesWithGroups|anydealsWithGroups|g' \
        -e 's|"hermes"|"anydeals"|g' \
        -e "s|'hermes'|'anydeals'|g" \
        -e 's| Hermes Agent| AnyDeals Agent|g' \
        -e 's|/opt/hermes|/opt/anydeals|g' \
        -e 's|/home/hermes|/home/anydeals|g' \
        -e 's|/var/lib/hermes|/var/lib/anydeals|g' \
        -e 's|/etc/sudoers\.d/hermes|/etc/sudoers.d/anydeals|g' \
        -e 's|load_hermes_dotenv|load_anydeals_dotenv|g' \
        -e 's|services\.hermes-agent|services.anydeals-agent|g' \
        -e 's|@hermes/|@anydeals/|g' \
        "$f"
}

# Apply rebrand to files that commonly contain hermes references.
# Focused on Python, nix, shell, and Dockerfile.
while IFS= read -r -d '' f; do
    # Skip .venv, .git, node_modules
    case "$f" in
        *.venv/*|*.git/*|*node_modules/*|*__pycache__/*) continue ;;
    esac
    if grep -q -i "hermes" "$f" 2>/dev/null; then
        rebrand_file "$f"
        echo "  已处理: $f"
    fi
done < <(find . -type f \( -name "*.py" -o -name "*.nix" -o -name "*.sh" -o -name "Dockerfile" \) -print0 2>/dev/null)

echo ""
echo -e "${BLUE}7. 推送到你的 GitHub...${NC}"
git push origin main

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  同步完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "如遇到冲突或问题，请检查："
echo "  • 冲突文件是否已正确解决（保留品牌修改 + 新功能）"
echo "  • 重命名的路径是否被上游新增的同名文件覆盖"
echo "  • 运行 git status 确认所有文件状态"
