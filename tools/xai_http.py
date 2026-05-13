"""Shared helpers for direct xAI HTTP integrations."""

from __future__ import annotations


def AnyDeals_xai_user_agent() -> str:
    """Return a stable Anydeals-specific User-Agent for xAI HTTP calls."""
    try:
        from AnyDeals_cli import __version__
    except Exception:
        __version__ = "unknown"
    return f"Anydeals-Agent/{__version__}"
