#!/bin/bash
# 上游同步脚本
# 用于从官方 Hermes 仓库拉取更新并重新应用品牌变更

set -e

echo "=== 开始同步官方更新 ==="

# 1. 获取官方最新代码
git fetch upstream

# 2. 切换到主分支
git checkout main

# 3. 合并官方更新
git merge upstream/main --no-edit || {
    echo ""
    echo "⚠ 合并冲突！请手动解决冲突后运行:"
    echo "  git add . && git commit -m 'merge: 同步官方更新'"
    echo "  python rebrand.py"
    exit 1
}

# 4. 运行品牌重塑脚本
python rebrand.py

# 5. 推送到你的 GitHub
git push origin main

echo "=== 同步完成 ==="
