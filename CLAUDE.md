# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## This is a Rebranded Fork

This is a fork of [Hermes Agent](https://github.com/nousresearch/hermes-agent) by Nous Research, rebranded as **AnyDeals** by JINKUI. See [BRANDING.md](BRANDING.md) for the full rebrand manifest.

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| CLI command | `anydeals` (lowercase) | `anydeals chat`, `anydeals profile create` |
| Config directory | `~/.anydeals` (lowercase in docs/user-facing) | `~/.anydeals/config.yaml` |
| Python package | `AnyDeals` (camelCase in imports) | `from AnyDeals_constants import get_AnyDeals_home` |
| Class names | `AnydealsCLI`, `AnydealsTokenStorage` | Capitalized camelCase |
| Shell functions | `_AnyDeals_profiles`, `_AnyDeals_completion` | Underscore prefix + camelCase |
| Environment variables | `ANYDEALS_*` (UPPER_SNAKE) | `ANYDEALS_HOME`, `ANYDEALS_TUI` |
| User-facing branding | `Anydeals Agent` | README, banners, help text |

### Upstream Sync

```bash
# Fetch upstream and merge into main
git fetch upstream && git merge upstream/main

# Run rebrand script if merge clobbers brand names
python rebrand.py --dry-run   # preview
python rebrand.py             # apply
```

**Merge conflict rules** (when merging from `upstream/main`):
1. Keep our brand modifications (`~/.anydeals`, `AnyDeals` names, anydeals CLI command)
2. Keep upstream's new feature code
3. Never silently drop upstream changes — resolve by combining both sides

## Essential Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests (always use the wrapper — matches CI environment)
scripts/run_tests.sh                                  # full suite
scripts/run_tests.sh tests/anydeals_cli/              # one directory
scripts/run_tests.sh tests/anydeals_cli/test_profiles.py::TestClass::test_name  # single test
scripts/run_tests.sh -v --tb=long                     # pass-through pytest flags

# TUI development
cd ui-tui && npm run dev     # watch mode
cd ui-tui && npm run build   # production build
cd ui-tui && npm test        # vitest

# Type checking (where available)
cd ui-tui && npm run type-check

# Linting
cd ui-tui && npm run lint
cd ui-tui && npm run fmt      # prettier
```

## Architecture Overview

The AGENTS.md at the repo root covers architecture in detail. Key files referenced here for quick orientation:

- [run_agent.py](run_agent.py) — `AIAgent` class, core conversation loop (~12k LOC)
- [cli.py](cli.py) — `AnydealsCLI` class, interactive CLI orchestrator (~11k LOC)
- [model_tools.py](model_tools.py) — tool orchestration, `discover_builtin_tools()`, `handle_function_call()`
- [toolsets.py](toolsets.py) — toolset definitions, `_ANYDEALS_CORE_TOOLS` list
- [anydeals_cli/commands.py](anydeals_cli/commands.py) — `COMMAND_REGISTRY`, central slash-command registry
- [anydeals_cli/profiles.py](anydeals_cli/profiles.py) — multi-profile management (create, delete, export, rename)
- [anydeals_cli/completion.py](anydeals_cli/completion.py) — bash/zsh/fish completion script generation
- [anydeals_constants.py](anydeals_constants.py) — `get_anydeals_home()`, profile-aware path resolution
- [tools/registry.py](tools/registry.py) — tool auto-discovery and registration (no deps, imported by all tool files)
- [gateway/run.py](gateway/run.py) — messaging gateway main entry point

**Plugin directory conventions:** `~/.anydeals/plugins/<name>/` — each with `plugin.yaml` + `__init__.py`.

**Profile isolation:** All path references must use `get_anydeals_home()` from `anydeals_constants`, never hardcoded `Path.home() / ".anydeals"`. User-facing messages use `display_anydeals_home()`.

**Test isolation:** Tests run under a hermetic temp `ANYDEALS_HOME` via `conftest.py`'s autouse fixture. Never write to `~/.anydeals/` in tests.
