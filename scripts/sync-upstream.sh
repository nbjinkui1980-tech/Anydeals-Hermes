#!/bin/bash
# ============================================
# 上游同步脚本
# 用于从官方 Hermes 仓库拉取更新
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
    echo ""
    exit 1
}

echo ""
echo -e "${BLUE}5. 推送到你的 GitHub...${NC}"
git push origin main

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  同步完成！${NC}"
echo -e "${GREEN}============================================${NC}"
