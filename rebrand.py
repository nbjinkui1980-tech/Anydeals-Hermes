#!/usr/bin/env python3
"""
AnyDeals 品牌重塑脚本 — 将 Hermes 上游代码转换为 AnyDeals 品牌

用法:
    python rebrand.py              # 执行品牌重塑
    python rebrand.py --dry-run    # 预览模式，不实际修改
    python rebrand.py --check      # 仅检查是否有遗漏的 hermes 引用

场景:
    - 从 upstream 合并后，运行此脚本重新应用品牌变更
    - 在 CI 中验证品牌一致性
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ── 排除目录 ──────────────────────────────────────────────────────────
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".omc",
    ".claude",
    "*.egg-info",
    "AnyDeals.egg-info",
}

# Files that intentionally contain "hermes" references (describing upstream
# origin, defining replacement rules, or verifying they were removed).
# These are NOT checked by --check and NOT modified by text replacements.
# Uses filename stem matching — any file with this name at any path is skipped.
META_FILENAMES = {
    "rebrand.py",
    "sync-upstream.sh",
    "BRANDING.md",
    "CLAUDE.md",
    "README.md",
    "flake.nix",
    "AnyDeals-agent.rb",
    "test_completion.py",
}

# ── 处理文件扩展名 ─────────────────────────────────────────────────────
INCLUDE_EXTS = {
    ".py", ".toml", ".md", ".yaml", ".yml", ".json", ".sh", ".bat",
    ".txt", ".in", ".cfg", ".ini", ".conf", ".rst", ".nix", ".rb",
}

# ── 文本替换规则（按顺序应用，长模式优先）──────────────────────────────
# 格式: (old, new, description)
TEXT_REPLACEMENTS: List[Tuple[str, str, str]] = [
    # ── 多词短语（必须先于单词匹配）─────────────────────────────────
    ("Hermes Agent", "AnyDeals Agent", "产品名称"),
    ("hermes-container-entrypoint", "anydeals-container-entrypoint", "容器入口脚本"),
    ("hermes-config-merge", "anydeals-config-merge", "配置合并脚本"),
    ("hermes-documents", "anydeals-documents", "文档目录"),
    ("hermes-tools-provisioned", "anydeals-tools-provisioned", "工具标记文件"),
    ("hermes-kanban-dispatcher", "anydeals-kanban-dispatcher", "看板调度器"),

    # ── 包名 / 二进制名（- 连字符）───────────────────────────────────
    ("hermes-agent", "anydeals-agent", "包/二进制"),
    ("hermes-acp", "anydeals-acp", "ACP二进制"),
    ("hermes-tui", "anydeals-tui", "TUI包"),
    ("hermes-web", "anydeals-web", "Web包"),
    ("hermes-ink", "anydeals-ink", "Ink包"),
    ("hermes-lcm", None, "外部插件 - 保留"),       # 跳过，外部引用
    ("hermes-achievements", "anydeals-achievements", "成就插件"),
    ("hermes-bootstrap", "anydeals-bootstrap", "引导脚本"),

    # ── 环境变量 ─────────────────────────────────────────────────────
    ("HERMES_BUNDLED_SKILLS", "ANYDEALS_BUNDLED_SKILLS", "env"),
    ("HERMES_BUNDLED_PLUGINS", "ANYDEALS_BUNDLED_PLUGINS", "env"),
    ("HERMES_WEB_DIST", "ANYDEALS_WEB_DIST", "env"),
    ("HERMES_TUI_DIR", "ANYDEALS_TUI_DIR", "env"),
    ("HERMES_PYTHON", "ANYDEALS_PYTHON", "env"),
    ("HERMES_NODE", "ANYDEALS_NODE", "env"),
    ("HERMES_REVISION", "ANYDEALS_REVISION", "env"),
    ("HERMES_HOME", "ANYDEALS_HOME", "env"),
    ("HERMES_MANAGED", "ANYDEALS_MANAGED", "env"),
    ("HERMES_UID", "ANYDEALS_UID", "env"),
    ("HERMES_GID", "ANYDEALS_GID", "env"),
    ("HERMES_LOCAL_STT_COMMAND", "ANYDEALS_LOCAL_STT_COMMAND", "env"),
    ("HERMES_CONTAINER_MODE_EOF", "ANYDEALS_CONTAINER_MODE_EOF", "heredoc"),
    ("HERMES_NIX_ENV_EOF", "ANYDEALS_NIX_ENV_EOF", "heredoc"),
    ("HERMES_DOC_EOF", "ANYDEALS_DOC_EOF", "heredoc"),

    # ── Nix 变量名 ────────────────────────────────────────────────────
    ("hermesWithExtra", "anydealsWithExtra", "Nix变量"),
    ("hermesWithGroups", "anydealsWithGroups", "Nix变量"),
    ("hermesVenv", "anydealsVenv", "Nix变量"),
    ("hermesNpmLib", "anydealsNpmLib", "Nix变量"),
    ("hermesTui", "anydealsTui", "Nix变量"),
    ("hermesWeb", "anydealsWeb", "Nix变量"),
    ("hermesAgent", "anydealsAgent", "Nix变量"),

    # ── Python 模块名 ─────────────────────────────────────────────────
    ("hermes_cli", "AnyDeals_cli", "Python模块"),
    ("hermes_bootstrap", "AnyDeals_bootstrap", "Python模块"),
    ("hermes_constants", "AnyDeals_constants", "Python模块"),
    ("hermes_logging", "AnyDeals_logging", "Python模块"),
    ("hermes_state", "AnyDeals_state", "Python模块"),
    ("hermes_time", "AnyDeals_time", "Python模块"),
    ("hermes_home", "anydeals_home", "Python变量"),

    # ── Shell / 函数名 ───────────────────────────────────────────────
    ("_hermes_npm_stamp", "_anydeals_npm_stamp", "Shell函数"),
    ("_hermes_home", "_AnyDeals_home", "Shell/Python模块"),
    ("load_hermes_dotenv", "load_anydeals_dotenv", "函数名"),

    # ── 路径 ─────────────────────────────────────────────────────────
    ("/opt/hermes", "/opt/anydeals", "路径"),
    ("/home/hermes", "/home/anydeals", "路径"),
    ("/var/lib/hermes", "/var/lib/anydeals", "路径"),
    ("/etc/sudoers.d/hermes", "/etc/sudoers.d/anydeals", "路径"),

    # ── NixOS 服务名 ──────────────────────────────────────────────────
    ("services.hermes-agent", "services.anydeals-agent", "NixOS服务"),

    # ── npm scope ─────────────────────────────────────────────────────
    ("@hermes/", "@anydeals/", "npm scope"),

    # ── 通用（放在最后）───────────────────────────────────────────────
    # 注意：不替换 github.com/NousResearch/hermes-agent（上游URL）
    # 注意：不替换 rtk-hermes, hermes-lcm, hermes_agent.plugins（外部包）
]


def find_project_root() -> Path:
    """查找项目根目录（包含 pyproject.toml 的目录）"""
    d = Path.cwd()
    while d != d.parent:
        if (d / "pyproject.toml").exists():
            return d
        d = d.parent
    return Path.cwd()


class Rebrander:
    """Hermes → AnyDeals 品牌重塑器"""

    def __init__(self, root_dir: Path, dry_run: bool = False):
        self.root_dir = root_dir
        self.dry_run = dry_run
        self.stats = {"files_modified": 0, "files_renamed": 0, "dirs_renamed": 0}

    def _should_skip(self, path: Path) -> bool:
        """检查路径是否应该跳过"""
        parts = set(path.parts)
        if parts & EXCLUDE_DIRS:
            return True
        return False

    def _should_process_file(self, path: Path) -> bool:
        """检查文件是否应该处理"""
        if self._should_skip(path):
            return False
        if path.name in META_FILENAMES:
            return False
        return path.suffix in INCLUDE_EXTS or path.name in ("Dockerfile",)

    def replace_text(self) -> int:
        """在所有文件中执行文本替换"""
        count = 0
        files_checked = 0

        for file_path in sorted(self.root_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if not self._should_process_file(file_path):
                continue
            files_checked += 1

            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            original = content
            for old, new, _desc in TEXT_REPLACEMENTS:
                if new is None:
                    continue  # 跳过标记为保留的项
                if old in content:
                    content = content.replace(old, new)

            if content != original:
                rel = file_path.relative_to(self.root_dir)
                if not self.dry_run:
                    file_path.write_text(content, encoding="utf-8")
                count += 1
                print(f"  ✎ {rel}")

        self.stats["files_modified"] = count
        print(f"\n检查 {files_checked} 个文件，修改 {count} 个文件")
        return count

    def _two_step_rename(self, src: Path, dst: Path) -> bool:
        """两步重命名（兼容大小写不敏感的文件系统如 macOS APFS）"""
        if src == dst:
            return False
        if not src.exists():
            return False

        if self.dry_run:
            print(f"  [dry-run] {src.relative_to(self.root_dir)} → {dst.relative_to(self.root_dir)}")
            return True

        # 如果只是大小写不同，需要两步重命名
        if src.as_posix().lower() == dst.as_posix().lower():
            tmp = src.with_name(src.name + ".tmp_rename")
            src.rename(tmp)
            tmp.rename(dst)
        else:
            # 确保目标父目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
        return True

    def rename_items(self) -> int:
        """重命名文件和目录（hermes → AnyDeals）"""
        rename_map: Dict[str, str] = {
            # ── 根级脚本 ──────────────────────────────────────────
            "hermes": "AnyDeals",

            # ── Python 模块 ───────────────────────────────────────
            "hermes_bootstrap.py": "AnyDeals_bootstrap.py",
            "hermes_constants.py": "AnyDeals_constants.py",
            "hermes_logging.py": "AnyDeals_logging.py",
            "hermes_state.py": "AnyDeals_state.py",
            "hermes_time.py": "AnyDeals_time.py",

            # ── 目录 ──────────────────────────────────────────────
            "hermes_cli": "AnyDeals_cli",
            "tests/hermes_cli": "tests/AnyDeals_cli",
            "tests/hermes_state": "tests/AnyDeals_state",

            # ── 测试文件 ──────────────────────────────────────────
            "tests/test_hermes_bootstrap.py": "tests/test_AnyDeals_bootstrap.py",
            "tests/test_hermes_constants.py": "tests/test_AnyDeals_constants.py",
            "tests/test_hermes_logging.py": "tests/test_AnyDeals_logging.py",
            "tests/test_hermes_state.py": "tests/test_AnyDeals_state.py",
            "tests/test_hermes_state_wal_fallback.py": "tests/test_AnyDeals_state_wal_fallback.py",
            "tests/test_hermes_home_profile_warning.py": "tests/test_AnyDeals_home_profile_warning.py",

            # ── 脚本 ──────────────────────────────────────────────
            "setup-hermes.sh": "setup-AnyDeals.sh",
            "scripts/hermes-gateway": "scripts/AnyDeals-gateway",

            # ── Environments ──────────────────────────────────────
            "environments/hermes_base_env.py": "environments/AnyDeals_base_env.py",
            "environments/hermes_swe_env": "environments/AnyDeals_swe_env",
            "environments/tool_call_parsers/hermes_parser.py": "environments/tool_call_parsers/AnyDeals_parser.py",

            # ── 插件 ──────────────────────────────────────────────
            "plugins/hermes-achievements": "plugins/AnyDeals-achievements",

            # ── Nix ───────────────────────────────────────────────
            "nix/hermes-agent.nix": "nix/AnyDeals-agent.nix",

            # ── Homebrew ──────────────────────────────────────────
            "packaging/homebrew/hermes-agent.rb": "packaging/homebrew/AnyDeals-agent.rb",

            # ── Skills ────────────────────────────────────────────
            "skills/productivity/google-workspace/scripts/_hermes_home.py":
                "skills/productivity/google-workspace/scripts/_AnyDeals_home.py",
            "optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py":
                "optional-skills/migration/openclaw-migration/scripts/openclaw_to_anydeals.py",

            # ── UI ────────────────────────────────────────────────
            "ui-tui/packages/hermes-ink": "ui-tui/packages/anydeals-ink",

            # ── GitHub Actions ────────────────────────────────────
            ".github/actions/hermes-smoke-test": ".github/actions/AnyDeals-smoke-test",

            # ── Systemd ───────────────────────────────────────────
            "plugins/kanban/systemd/hermes-kanban-dispatcher.service":
                "plugins/kanban/systemd/anydeals-kanban-dispatcher.service",

            # ── Skills 目录 ───────────────────────────────────────
            "skills/productivity/hermes-gsuite": "skills/productivity/AnyDeals-gsuite",
            "skills/demos/hermes-ralph-loop": "skills/demos/AnyDeals-ralph-loop",
            "skills/document-skills/hermes-changelog": "skills/document-skills/AnyDeals-changelog",
            "optional-skills/migration/hermes-migration": "optional-skills/migration/AnyDeals-migration",
        }

        count = 0
        for old_rel, new_rel in rename_map.items():
            src = self.root_dir / old_rel
            dst = self.root_dir / new_rel

            if src.exists():
                if self._two_step_rename(src, dst):
                    print(f"  ⇄ {old_rel} → {new_rel}")
                    count += 1

        self.stats["dirs_renamed"] = count  # includes files
        print(f"\n重命名 {count} 个项目")
        return count

    def check_remaining(self) -> List[str]:
        """检查是否还有遗漏的 hermes 引用（排除外部引用）"""
        findings: List[str] = []

        # 已知的外部引用（不应被替换）
        external_patterns = [
            "github.com/NousResearch/hermes-agent",
            "hermes-lcm",
            "rtk-hermes",
            "hermes_agent.plugins",
        ]

        for file_path in sorted(self.root_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if self._should_skip(file_path):
                continue
            if file_path.name in META_FILENAMES:
                continue
            if not self._should_process_file(file_path):
                if file_path.name != "Dockerfile":
                    continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            for i, line in enumerate(content.splitlines(), 1):
                if "hermes" not in line.lower():
                    continue
                # 跳过已知外部引用
                if any(ep in line for ep in external_patterns):
                    continue
                rel = file_path.relative_to(self.root_dir)
                findings.append(f"  {rel}:{i}  {line.strip()[:120]}")

        return findings

    def run(self):
        """执行品牌重塑"""
        print("=" * 60)
        print("  AnyDeals 品牌重塑脚本")
        print("  Hermes → AnyDeals")
        print("=" * 60)

        if self.dry_run:
            print("\n  ⚠ 预览模式 — 不会实际修改文件\n")

        print(f"  项目根目录: {self.root_dir}")
        print()

        # ── 1. 文本替换 ──────────────────────────────────────────
        print("[1/3] 文本替换 (hermes → anydeals)")
        print("-" * 40)
        self.replace_text()

        # ── 2. 文件/目录重命名 ────────────────────────────────────
        print("\n[2/3] 文件/目录重命名")
        print("-" * 40)
        self.rename_items()

        # ── 3. 检查遗漏 ──────────────────────────────────────────
        print("\n[3/3] 检查遗漏的 hermes 引用")
        print("-" * 40)
        remaining = self.check_remaining()

        if remaining:
            print(f"  发现 {len(remaining)} 处可能遗漏的引用:")
            for r in remaining:
                print(r)
        else:
            print("  ✓ 没有发现遗漏的 hermes 引用（外部引用已排除）")

        # ── 总结 ──────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print(f"  完成: {self.stats['files_modified']} 文件修改, "
              f"{self.stats['dirs_renamed']} 项目重命名")

        if self.dry_run:
            print("\n  这是预览模式。去掉 --dry-run 参数实际执行。")

        if not self.dry_run:
            print("\n  后续步骤:")
            print("    git status")
            print("    git diff")
            print("    scripts/run_tests.sh")


def main():
    parser = argparse.ArgumentParser(
        description="AnyDeals 品牌重塑 — Hermes → AnyDeals",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="预览模式，不实际修改文件"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="仅检查遗漏的 hermes 引用，不做任何修改"
    )
    parser.add_argument(
        "--root", type=Path, default=None,
        help="项目根目录（默认自动检测）"
    )
    args = parser.parse_args()

    root = args.root or find_project_root()
    if not (root / "pyproject.toml").exists():
        print(f"错误: 在 {root} 中未找到 pyproject.toml", file=sys.stderr)
        sys.exit(1)

    rebrander = Rebrander(root, dry_run=args.dry_run)

    if args.check:
        print("检查遗漏的 hermes 引用...")
        remaining = rebrander.check_remaining()
        if remaining:
            print(f"\n发现 {len(remaining)} 处可能遗漏:")
            for r in remaining:
                print(r)
            sys.exit(1)
        else:
            print("✓ 没有遗漏")
            sys.exit(0)

    rebrander.run()


if __name__ == "__main__":
    main()
