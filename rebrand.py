#!/usr/bin/env python3
"""
Anydeals Agent 品牌重塑自动化脚本

功能：
1. 自动备份原始代码
2. 批量替换项目名、命令名、配置路径
3. 支持预览模式（不实际修改）
4. 自动生成品牌声明文档
5. 自动配置上游同步策略

使用方法：
    python rebrand.py <新项目名> <新命令名> [新作者名]

示例：
    python rebrand.py myagent ma "你的名字"
    python rebrand.py myagent ma --dry-run  # 预览模式
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple

# ============================================
# 颜色输出（让界面更好看）
# ============================================


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    NC = "\033[0m"  # No Color


def print_color(message, color=Colors.NC, end="\n"):
    """带颜色的打印函数"""
    print(f"{color}{message}{Colors.NC}", end=end)


def print_header(title):
    """打印标题"""
    print_color("\n" + "=" * 60, Colors.CYAN)
    print_color(f"  {title}", Colors.WHITE)
    print_color("=" * 60, Colors.CYAN)


def print_step(step_num, total, description):
    """打印步骤进度"""
    print_color(f"\n[{step_num}/{total}] {description}...", Colors.BLUE)


def print_success(message):
    """打印成功消息"""
    print_color(f"  ✓ {message}", Colors.GREEN)


def print_warning(message):
    """打印警告消息"""
    print_color(f"  ⚠ {message}", Colors.YELLOW)


def print_error(message):
    """打印错误消息"""
    print_color(f"  ✗ {message}", Colors.RED)


# ============================================
# 品牌重塑核心类
# ============================================


class AnydealsRebrander:
    """Anydeals 品牌重塑器"""

    def __init__(
        self,
        old_name: str,
        old_cmd: str,
        old_author: str,
        old_config_dir: str,
        new_name: str,
        new_cmd: str,
        new_author: str,
        new_config_dir: str,
        dry_run: bool = False,
    ):
        # 原始配置
        self.old_name = old_name
        self.old_cmd = old_cmd
        self.old_author = old_author
        self.old_config_dir = old_config_dir

        # 新配置
        self.new_name = new_name
        self.new_cmd = new_cmd
        self.new_author = new_author
        self.new_config_dir = new_config_dir

        # 运行模式
        self.dry_run = dry_run

        # 项目根目录
        self.root_dir = Path.cwd()

        # 备份目录
        self.backup_dir = None

        # 统计信息
        self.stats = {"files_modified": 0, "directories_renamed": 0, "conflicts": []}

        # 需要排除的目录和文件
        self.exclude_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "venv",
            ".venv",
            "env",
            "dist",
            "build",
            "*.egg-info",
        }
        self.exclude_files = {"*.pyc", "*.pyo", "*.so", "*.dll", "*.exe"}

        # 需要处理的文件扩展名
        self.include_extensions = {
            ".py",
            ".toml",
            ".md",
            ".yaml",
            ".yml",
            ".json",
            ".sh",
            ".bat",
            ".txt",
            ".in",
            ".cfg",
            ".ini",
            ".conf",
            ".rst",
        }

    def should_process_file(self, file_path: Path) -> bool:
        """判断是否应该处理这个文件"""
        # 检查是否在排除目录中
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return False

        # 检查文件扩展名
        return file_path.suffix in self.include_extensions

    def create_backup(self) -> bool:
        """创建项目备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = (
            self.root_dir.parent / f"{self.root_dir.name}_backup_{timestamp}"
        )

        if self.dry_run:
            print_success(f"预览模式: 将备份到 {self.backup_dir}")
            return True

        try:
            print(f"  备份目标: {self.backup_dir}")
            shutil.copytree(
                self.root_dir,
                self.backup_dir,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            print_success(f"备份已创建: {self.backup_dir}")
            return True
        except Exception as e:
            print_error(f"备份失败: {e}")
            return False

    def rename_directories(self) -> int:
        """重命名目录"""
        count = 0

        # 需要重命名的目录映射
        rename_map = {
            f"{self.old_name}_cli": f"{self.new_cmd}_cli",
            self.old_name: self.new_name,
            f"tests/{self.old_name}": f"tests/{self.new_name}",
        }

        for old_dir_name, new_dir_name in rename_map.items():
            old_path = self.root_dir / old_dir_name
            new_path = self.root_dir / new_dir_name

            if old_path.exists() and old_path.is_dir():
                if self.dry_run:
                    print(f"  预览: 重命名 {old_dir_name}/ → {new_dir_name}/")
                else:
                    shutil.move(str(old_path), str(new_path))
                    print_success(f"重命名: {old_dir_name}/ → {new_dir_name}/")
                count += 1

        self.stats["directories_renamed"] = count
        return count

    def replace_in_file(self, file_path: Path) -> int:
        """在单个文件中执行替换"""
        try:
            # 读取文件内容
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # 执行替换
            replacements = [
                (self.old_name, self.new_name),
                (self.old_cmd, self.new_cmd),
                (self.old_config_dir, self.new_config_dir),
                (self.old_author, self.new_author),
                # 变体形式（首字母大写）
                (self.old_name.capitalize(), self.new_name.capitalize()),
                (self.old_cmd.capitalize(), self.new_cmd.capitalize()),
                # 全大写形式
                (self.old_name.upper(), self.new_name.upper()),
                (self.old_cmd.upper(), self.new_cmd.upper()),
            ]

            for old_str, new_str in replacements:
                if old_str and new_str and old_str != new_str:
                    content = content.replace(old_str, new_str)

            # 如果有变化，写回文件
            if content != original_content:
                if not self.dry_run:
                    file_path.write_text(content, encoding="utf-8")
                return 1

            return 0

        except UnicodeDecodeError:
            # 二进制文件，跳过
            return 0
        except Exception as e:
            print_warning(f"处理 {file_path.relative_to(self.root_dir)} 时出错: {e}")
            return 0

    def process_files(self) -> int:
        """批量处理所有文件"""
        count = 0
        total_files = 0

        print("  扫描文件...")

        for file_path in self.root_dir.rglob("*"):
            if file_path.is_file() and self.should_process_file(file_path):
                total_files += 1
                if self.replace_in_file(file_path) > 0:
                    count += 1
                    if count % 20 == 0:
                        print(f"  已处理 {count} 个文件...")

        self.stats["files_modified"] = count
        print_success(f"共处理 {total_files} 个文件，修改了 {count} 个文件")
        return count

    def update_pyproject_toml(self) -> bool:
        """更新 pyproject.toml 文件"""
        toml_path = self.root_dir / "pyproject.toml"
        if not toml_path.exists():
            print_warning("未找到 pyproject.toml 文件")
            return False

        try:
            content = toml_path.read_text(encoding="utf-8")
            original_content = content

            # 更新项目名称
            content = re.sub(
                r'^name = "([^"]*)"',
                f'name = "{self.new_name}"',
                content,
                flags=re.MULTILINE,
            )

            # 更新命令入口
            content = re.sub(
                rf'{self.old_cmd} = "{self.old_cmd}_cli.main:cli"',
                f'{self.new_cmd} = "{self.new_cmd}_cli.main:cli"',
                content,
            )

            # 更新作者
            content = re.sub(
                r"authors = \[.*?\]",
                f'authors = ["{self.new_author}"]',
                content,
                flags=re.DOTALL,
            )

            # 更新版本号（可选）
            # content = re.sub(r'version = "[^"]*"', 'version = "1.0.0"', content)

            if content != original_content:
                if not self.dry_run:
                    toml_path.write_text(content, encoding="utf-8")
                print_success("已更新 pyproject.toml")
                return True

            return False

        except Exception as e:
            print_error(f"更新 pyproject.toml 失败: {e}")
            return False

    def update_config_py(self) -> bool:
        """更新 config.py 中的配置路径"""
        config_paths = [
            self.root_dir / self.new_name / "config.py",
            self.root_dir / f"{self.new_cmd}_cli" / "config.py",
            self.root_dir / "AnyDeals" / "config.py",  # 备用
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    content = config_path.read_text(encoding="utf-8")
                    original_content = content

                    # 更新配置目录
                    content = content.replace(
                        f'CONFIG_DIR = os.path.expanduser("~/{self.old_config_dir}")',
                        f'CONFIG_DIR = os.path.expanduser("~/{self.new_config_dir}")',
                    )

                    # 更新版本号
                    content = re.sub(
                        r'_config_version = "[^"]*"',
                        f'_config_version = "1.0.0"',
                        content,
                    )

                    if content != original_content and not self.dry_run:
                        config_path.write_text(content, encoding="utf-8")
                        print_success(
                            f"已更新 {config_path.relative_to(self.root_dir)}"
                        )
                        return True

                except Exception as e:
                    print_warning(f"更新 {config_path} 失败: {e}")

        return False

    def update_readme(self) -> bool:
        """更新 README.md 文件"""
        readme_path = self.root_dir / "README.md"
        if not readme_path.exists():
            print_warning("未找到 README.md 文件")
            return False

        # 准备品牌声明头
        header = f"""<!--
  品牌声明
  ============================================================
  本项目是基于 Anydeals Agent 的定制版本
  原作者: JINKUI | 遵循 MIT 许可证
  定制维护者: {self.new_author}
  项目名称: {self.new_name}
  命令名称: {self.new_cmd}
  ============================================================
-->

"""

        try:
            content = readme_path.read_text(encoding="utf-8")

            # 如果已经有品牌声明，跳过
            if "品牌声明" in content[:500]:
                print_success("README 已包含品牌声明")
                return True

            # 添加品牌声明
            new_content = header + content

            # 替换命令示例
            new_content = new_content.replace(f"`{self.old_cmd}`", f"`{self.new_cmd}`")
            new_content = new_content.replace(f"'{self.old_cmd}'", f"'{self.new_cmd}'")
            new_content = new_content.replace(f'"{self.old_cmd}"', f'"{self.new_cmd}"')

            if content != new_content and not self.dry_run:
                readme_path.write_text(new_content, encoding="utf-8")
                print_success("已更新 README.md")
                return True

            return False

        except Exception as e:
            print_error(f"更新 README 失败: {e}")
            return False

    def create_branding_file(self) -> bool:
        """创建品牌说明文件"""
        content = f"""# 品牌重塑说明

## 项目信息

| 项目 | 信息 |
|------|------|
| **原项目** | Anydeals Agent |
| **原项目地址** | https://github.com/nousresearch/AnyDeals-agent |
| **原作者** | JINKUI |
| **原始许可证** | MIT |

## 本定制版本信息

| 项目 | 信息 |
|------|------|
| **项目名称** | {self.new_name} |
| **命令名称** | {self.new_cmd} |
| **维护者** | {self.new_author} |
| **配置目录** | ~/{self.new_config_dir} |
| **定制日期** | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |

## 修改清单

本项目在 Anydeals Agent 基础上进行了以下品牌化修改：

1. ✅ 项目名称: `{self.old_name}` → `{self.new_name}`
2. ✅ 命令名称: `{self.old_cmd}` → `{self.new_cmd}`
3. ✅ 配置目录: `~/{self.old_config_dir}` → `~/{self.new_config_dir}`
4. ✅ 作者信息: `{self.old_author}` → `{self.new_author}`
5. ✅ README 品牌声明
6. ✅ pyproject.toml 配置更新

## 与上游同步策略

- 上游仓库: `git remote add upstream https://github.com/nousresearch/AnyDeals-agent.git`
- 同步命令: `git fetch upstream && git merge upstream/main`

## 许可证声明

根据 MIT 许可证要求，保留原始版权声明：
Copyright (c) JINKUI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:


## 维护者联系方式

如有问题，请联系: {self.new_author}
"""

        branding_path = self.root_dir / "BRANDING.md"

        if not self.dry_run:
            branding_path.write_text(content, encoding="utf-8")
            print_success("已创建 BRANDING.md")
        else:
            print("  预览: 将创建 BRANDING.md")

        return True

    def create_gitattributes(self) -> bool:
        """创建 .gitattributes 文件用于自动处理冲突"""
        content = """# Git 合并策略配置
# 当从上游同步时，自动处理品牌相关的冲突

# ============================================
# 品牌相关文件 - 优先保留本地版本
# ============================================
pyproject.toml    merge=ours
AnyDeals/config.py  merge=ours
BRANDING.md       merge=ours

# ============================================
# 核心代码 - 优先使用上游版本
# ============================================
AnyDeals/agent/     merge=union
AnyDeals/skills/    merge=union
AnyDeals/memory/    merge=union

# ============================================
# 文档 - 尝试自动合并
# ============================================
*.md              merge=union
*.txt             merge=union

# ============================================
# 二进制文件 - 不合并
# ============================================
*.png             binary
*.jpg             binary
*.ico             binary
"""

        gitattributes_path = self.root_dir / ".gitattributes"

        if not self.dry_run:
            gitattributes_path.write_text(content, encoding="utf-8")
            print_success("已创建 .gitattributes")
        else:
            print("  预览: 将创建 .gitattributes")

        return True

    def create_sync_script(self) -> bool:
        """创建上游同步脚本"""
        script_content = f"""#!/bin/bash
# ============================================
# 上游同步脚本
# 用于从官方 Anydeals 仓库拉取更新
# 创建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# ============================================

set -e

echo "============================================"
echo "  上游同步脚本"
echo "============================================"
echo ""

# 颜色定义
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

# 配置
UPSTREAM_REPO="https://github.com/nousresearch/AnyDeals-agent.git"
UPSTREAM_BRANCH="main"

echo -e "${{BLUE}}1. 添加/更新 upstream 远程仓库...${{NC}}"
if git remote | grep -q "^upstream$"; then
    echo "   upstream 已存在"
else
    git remote add upstream $UPSTREAM_REPO
    echo -e "${{GREEN}}   ✓ 已添加 upstream${{NC}}"
fi

echo ""
echo -e "${{BLUE}}2. 拉取官方更新...${{NC}}"
git fetch upstream

echo ""
echo -e "${{BLUE}}3. 切换到 main 分支...${{NC}}"
git checkout main

echo ""
echo -e "${{BLUE}}4. 合并官方更新...${{NC}}"
echo -e "${{YELLOW}}   注意: 如遇冲突，请手动解决${{NC}}"
git merge upstream/$UPSTREAM_BRANCH --no-edit || {{
    echo ""
    echo -e "${{RED}}⚠ 合并过程出现冲突${{NC}}"
    echo ""
    echo "冲突处理指南："
    echo "  1. 打开冲突文件，查找 <<<<<<< 标记"
    echo "  2. 保留你的品牌修改（~/.{self.new_config_dir} 等）"
    echo "  3. 保留官方的新功能代码"
    echo "  4. 删除 <<<<<<<、=======、>>>>>>> 标记"
    echo "  5. 执行: git add . && git commit -m 'merge: 同步官方更新'"
    echo ""
    exit 1
}}

echo ""
echo -e "${{BLUE}}5. 推送到你的 GitHub...${{NC}}"
git push origin main

echo ""
echo -e "${{GREEN}}============================================${{NC}}"
echo -e "${{GREEN}}  同步完成！${{NC}}"
echo -e "${{GREEN}}============================================${{NC}}"
"""

        scripts_dir = self.root_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        sync_path = scripts_dir / "sync-upstream.sh"

        if not self.dry_run:
            sync_path.write_text(script_content, encoding="utf-8")
            sync_path.chmod(0o755)
            print_success("已创建 scripts/sync-upstream.sh")
        else:
            print("  预览: 将创建 scripts/sync-upstream.sh")

        return True

    def print_summary(self):
        """打印操作总结"""
        print_header("操作完成总结")

        print(f"\n  项目名称: {self.old_name} → {self.new_name}")
        print(f"  命令名称: {self.old_cmd} → {self.new_cmd}")
        print(f"  配置目录: ~/{self.old_config_dir} → ~/{self.new_config_dir}")
        print(f"  作者信息: {self.old_author} → {self.new_author}")

        print(f"\n  📊 统计:")
        print(f"     - 修改文件数: {self.stats['files_modified']}")
        print(f"     - 重命名目录数: {self.stats['directories_renamed']}")

        if self.backup_dir:
            print(f"\n  💾 备份位置: {self.backup_dir}")

        if self.dry_run:
            print(f"\n  {'=' * 50}")
            print_warning("这是预览模式，未实际修改任何文件")
            print(f"  如需实际执行，请去掉 --dry-run 参数")

    def run(self) -> bool:
        """执行品牌重塑主流程"""
        print_header(f"Anydeals Agent 品牌重塑工具")

        print(f"\n  原配置:")
        print(f"    - 项目名: {self.old_name}")
        print(f"    - 命令名: {self.old_cmd}")
        print(f"    - 作者: {self.old_author}")
        print(f"    - 配置目录: ~/{self.old_config_dir}")

        print(f"\n  新配置:")
        print(f"    - 项目名: {self.new_name}")
        print(f"    - 命令名: {self.new_cmd}")
        print(f"    - 作者: {self.new_author}")
        print(f"    - 配置目录: ~/{self.new_config_dir}")

        if self.dry_run:
            print_warning("\n⚠ 预览模式: 不会实际修改任何文件")

        print("\n")

        # 确认执行
        if not self.dry_run:
            confirm = input("是否继续执行品牌重塑？(y/N): ")
            if confirm.lower() != "y":
                print_error("操作已取消")
                return False

        # 执行各项操作
        steps = [
            ("创建备份", self.create_backup),
            ("重命名目录", lambda: self.rename_directories() >= 0),
            ("批量替换文件内容", lambda: self.process_files() >= 0),
            ("更新 pyproject.toml", self.update_pyproject_toml),
            ("更新 config.py", self.update_config_py),
            ("更新 README", self.update_readme),
            ("创建 BRANDING.md", self.create_branding_file),
            ("创建 .gitattributes", self.create_gitattributes),
            ("创建同步脚本", self.create_sync_script),
        ]

        for i, (name, func) in enumerate(steps, 1):
            print_step(i, len(steps), name)
            try:
                func()
            except Exception as e:
                print_error(f"操作失败: {e}")
                if not self.dry_run:
                    print_warning(f"建议从备份恢复: {self.backup_dir}")
                    return False

        self.print_summary()

        # 打印后续操作指南
        if not self.dry_run:
            print_header("后续操作指南")
            print(f"""
  1. 查看修改:
     git status
     git diff

  2. 提交品牌修改:
     git add .
     git commit -m "rebrand: 项目更名为 {self.new_name}"

  3. 推送到 GitHub:
     git push origin main

  4. 设置上游同步:
     git remote add upstream https://github.com/nousresearch/AnyDeals-agent.git

  5. 安装测试:
     pip install -e .
     {self.new_cmd} --version

  6. 后续同步官方更新:
     ./scripts/sync-upstream.sh
""")

        return True


# ============================================
# 主函数
# ============================================


def main():
    parser = argparse.ArgumentParser(
        description="Anydeals Agent 品牌重塑工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s myagent ma "张三"                    # 正常执行
  %(prog)s myagent ma "张三" --dry-run          # 预览模式
  %(prog)s myagent ma "张三" --no-backup        # 不创建备份
        """,
    )

    parser.add_argument("new_name", help="新项目名称（如: myagent）")
    parser.add_argument("new_cmd", help="新命令名称（如: ma）")
    parser.add_argument(
        "new_author",
        nargs="?",
        default="Custom Maintainer",
        help="新作者/维护者名称（可选）",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="预览模式，不实际修改文件"
    )
    parser.add_argument("--no-backup", action="store_true", help="不创建备份（不推荐）")

    args = parser.parse_args()

    # 默认配置
    old_name = "AnyDeals"
    old_cmd = "AnyDeals"
    old_author = "JINKUI"
    old_config_dir = ".AnyDeals"

    new_config_dir = f".{args.new_cmd}"

    # 创建品牌重塑器
    rebrander = AnydealsRebrander(
        old_name=old_name,
        old_cmd=old_cmd,
        old_author=old_author,
        old_config_dir=old_config_dir,
        new_name=args.new_name,
        new_cmd=args.new_cmd,
        new_author=args.new_author,
        new_config_dir=new_config_dir,
        dry_run=args.dry_run,
    )

    # 执行
    success = rebrander.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
