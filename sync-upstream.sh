#!/bin/bash
# 上游同步脚本

echo "=== 开始同步官方更新 ==="

# 1. 获取官方最新代码
git fetch upstream

# 2. 切换到主分支
git checkout main

# 3. 合并官方更新
git merge upstream/main --no-edit

# 4. 运行品牌脚本（如果有）
# python rebrand.py  如果你有自动脚本

# 5. 推送到你的 GitHub
git push origin main

echo "=== 同步完成 ==="