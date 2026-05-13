"""Resolve ANYDEALS_HOME for standalone skill scripts.

Skill scripts may run outside the Anydeals process (e.g. system Python,
nix env, CI) where ``AnyDeals_constants`` is not importable.  This module
provides the same ``get_AnyDeals_home()`` and ``display_AnyDeals_home()``
contracts as ``AnyDeals_constants`` without requiring it on ``sys.path``.

When ``AnyDeals_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``AnyDeals_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``ANYDEALS_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from AnyDeals_constants import display_AnyDeals_home as display_AnyDeals_home
    from AnyDeals_constants import get_AnyDeals_home as get_AnyDeals_home
except (ModuleNotFoundError, ImportError):

    def get_AnyDeals_home() -> Path:
        """Return the Anydeals home directory (default: ~/.AnyDeals).

        Mirrors ``AnyDeals_constants.get_AnyDeals_home()``."""
        val = os.environ.get("ANYDEALS_HOME", "").strip()
        return Path(val) if val else Path.home() / ".AnyDeals"

    def display_AnyDeals_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``AnyDeals_constants.display_AnyDeals_home()``."""
        home = get_AnyDeals_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
