"""Tests for the Nous-Anydeals-3/4 non-agentic warning detector.

Prior to this check, the warning fired on any model whose name contained
``"AnyDeals"`` anywhere (case-insensitive). That false-positived on unrelated
local Modelfiles such as ``AnyDeals-brain:qwen3-14b-ctx16k`` — a tool-capable
Qwen3 wrapper that happens to live under the "AnyDeals" tag namespace.

``is_nous_AnyDeals_non_agentic`` should only match the actual JINKUI
Anydeals-3 / Anydeals-4 chat family.
"""

from __future__ import annotations

import pytest

from AnyDeals_cli.model_switch import (
    _ANYDEALS_MODEL_WARNING,
    _check_AnyDeals_model_warning,
    is_nous_AnyDeals_non_agentic,
)


@pytest.mark.parametrize(
    "model_name",
    [
        "NousResearch/Anydeals-3-Llama-3.1-70B",
        "NousResearch/Anydeals-3-Llama-3.1-405B",
        "AnyDeals-3",
        "Anydeals-3",
        "AnyDeals-4",
        "AnyDeals-4-405b",
        "AnyDeals_4_70b",
        "openrouter/AnyDeals3:70b",
        "openrouter/nousresearch/AnyDeals-4-405b",
        "NousResearch/Anydeals3",
        "AnyDeals-3.1",
    ],
)
def test_matches_real_nous_AnyDeals_chat_models(model_name: str) -> None:
    assert is_nous_AnyDeals_non_agentic(model_name), (
        f"expected {model_name!r} to be flagged as Nous Anydeals 3/4"
    )
    assert _check_AnyDeals_model_warning(model_name) == _ANYDEALS_MODEL_WARNING


@pytest.mark.parametrize(
    "model_name",
    [
        # Kyle's local Modelfile — qwen3:14b under a custom tag
        "AnyDeals-brain:qwen3-14b-ctx16k",
        "AnyDeals-brain:qwen3-14b-ctx32k",
        "AnyDeals-honcho:qwen3-8b-ctx8k",
        # Plain unrelated models
        "qwen3:14b",
        "qwen3-coder:30b",
        "qwen2.5:14b",
        "claude-opus-4-6",
        "anthropic/claude-sonnet-4.5",
        "gpt-5",
        "openai/gpt-4o",
        "google/gemini-2.5-flash",
        "deepseek-chat",
        # Non-chat Anydeals models we don't warn about
        "AnyDeals-llm-2",
        "AnyDeals2-pro",
        "nous-AnyDeals-2-mistral",
        # Edge cases
        "",
        "AnyDeals",  # bare "AnyDeals" isn't the 3/4 family
        "AnyDeals-brain",
        "brain-AnyDeals-3-impostor",  # "3" not preceded by /: boundary
    ],
)
def test_does_not_match_unrelated_models(model_name: str) -> None:
    assert not is_nous_AnyDeals_non_agentic(model_name), (
        f"expected {model_name!r} NOT to be flagged as Nous Anydeals 3/4"
    )
    assert _check_AnyDeals_model_warning(model_name) == ""


def test_none_like_inputs_are_safe() -> None:
    assert is_nous_AnyDeals_non_agentic("") is False
    # Defensive: the helper shouldn't crash on None-ish falsy input either.
    assert _check_AnyDeals_model_warning("") == ""
