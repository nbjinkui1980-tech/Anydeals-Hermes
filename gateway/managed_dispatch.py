"""
AnyAgent Managed Dispatch — H2.

Fail-closed policy, bounded async Bridge client, and session-custody
coordination for the AnyAgent management-only profile. All logic is
isolated in this module; no other Hermes gateway component imports it
unless the management profile is activated via typed config.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Public API called by the ingress guard and the wiring layer ──────────

async def is_management_only(config: Dict[str, Any]) -> bool:
    """Return True when the gateway must run in AnyAgent management-only mode."""
    return bool(config.get("anyagent_management_only", False))


async def should_bypass_for_management(
    event: Any, config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Called once per inbound message BEFORE any platform adapter processes it.

    Returns None → let stock Hermes handle normally.
    Returns a dict → the management-only decision (currently always a
    `blocked` envelope — no stock path is allowed in management mode).
    """
    if not await is_management_only(config):
        return None

    # In management mode, every inbound message is intercepted.
    # No stock bypass/queue/Agent branch ever runs.
    return {
        "decision": "blocked",
        "reason": "management_only_mode_active",
        "mode": "anyagent_management_only",
    }
