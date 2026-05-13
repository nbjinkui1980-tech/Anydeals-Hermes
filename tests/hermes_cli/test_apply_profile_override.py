"""Regression tests for _apply_profile_override ANYDEALS_HOME guard (issue #22502).

When ANYDEALS_HOME is set to the AnyDeals root (e.g. systemd hardcodes
ANYDEALS_HOME=/root/.AnyDeals), _apply_profile_override must still read
active_profile and update ANYDEALS_HOME to the profile directory.

When ANYDEALS_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _run_apply_profile_override(
    tmp_path, monkeypatch, *, AnyDeals_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["ANYDEALS_HOME"] after the call,
    or None if unset.
    """
    AnyDeals_root = tmp_path / ".AnyDeals"
    AnyDeals_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (AnyDeals_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (AnyDeals_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if AnyDeals_home is not None:
        monkeypatch.setenv("ANYDEALS_HOME", AnyDeals_home)
    else:
        monkeypatch.delenv("ANYDEALS_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["AnyDeals", "gateway", "start"])

    from AnyDeals_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("ANYDEALS_HOME")


class TestApplyProfileOverrideAnydealsHomeGuard:
    """Regression guard for issue #22502.

    Verifies that ANYDEALS_HOME pointing to the AnyDeals root does NOT suppress
    the active_profile check, while ANYDEALS_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_AnyDeals_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """ANYDEALS_HOME=/root/.AnyDeals + active_profile=coder must redirect
        ANYDEALS_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets ANYDEALS_HOME to the AnyDeals root
        and the user switches to a profile via `AnyDeals profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        AnyDeals_root = tmp_path / ".AnyDeals"
        AnyDeals_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            AnyDeals_home=str(AnyDeals_root),
            active_profile="coder",
        )

        assert result is not None, "ANYDEALS_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected ANYDEALS_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected ANYDEALS_HOME to end with 'coder', got: {result!r}"
        )

    def test_AnyDeals_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """ANYDEALS_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with ANYDEALS_HOME already set to a specific profile must stay in that
        profile.
        """
        AnyDeals_root = tmp_path / ".AnyDeals"
        profile_dir = AnyDeals_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (AnyDeals_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("ANYDEALS_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["AnyDeals", "gateway", "start"])

        from AnyDeals_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ANYDEALS_HOME") == str(profile_dir), (
            "ANYDEALS_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_AnyDeals_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: ANYDEALS_HOME unset + active_profile=coder must set
        ANYDEALS_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            AnyDeals_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_AnyDeals_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect ANYDEALS_HOME."""
        AnyDeals_root = tmp_path / ".AnyDeals"
        AnyDeals_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("ANYDEALS_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["AnyDeals", "gateway", "start"])
        (AnyDeals_root / "active_profile").write_text("default")

        from AnyDeals_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ANYDEALS_HOME") is None
