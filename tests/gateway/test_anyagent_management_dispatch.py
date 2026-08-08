"""H3: managed dispatch path conformance."""
import asyncio
import pytest


class TestManagedDispatchPolicy:

    def test_off_mode_passthrough(self):
        from gateway import managed_dispatch as md
        result = asyncio.run(md.should_bypass_for_management({}, {}))
        assert result is None

    def test_management_mode_blocks(self):
        from gateway import managed_dispatch as md
        result = asyncio.run(md.should_bypass_for_management(
            {"text": "hello"}, {"anyagent_management_only": True}))
        assert result is not None
        assert result["decision"] == "blocked"

    def test_is_management_only_helper(self):
        from gateway import managed_dispatch as md
        assert asyncio.run(md.is_management_only({"anyagent_management_only": True})) is True
        assert asyncio.run(md.is_management_only({})) is False


class TestGatewayConfigField:

    def test_default_is_false(self):
        from gateway.config import GatewayConfig
        cfg = GatewayConfig()
        assert cfg.anyagent_management_only is False
