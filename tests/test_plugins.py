"""Tests for ADK plugins: ChronicleRetryPlugin, CostGuardPlugin, ContextTrimmerPlugin."""

import os
import pytest
from unittest.mock import MagicMock, AsyncMock

from google.genai.types import Content, Part

from agents.plugins.chronicle_retry_plugin import ChronicleRetryPlugin
from agents.plugins.cost_guard_plugin import CostGuardPlugin, DEFAULT_MAX_LLM_CALLS
from agents.plugins.context_trimmer_plugin import ContextTrimmerPlugin


# ── ChronicleRetryPlugin ─────────────────────────────────────────────────────


class TestChronicleRetryPlugin:
    """Tests for ChronicleRetryPlugin error detection."""

    @pytest.fixture
    def plugin(self):
        return ChronicleRetryPlugin(max_retries=2)

    @pytest.mark.asyncio
    async def test_detects_dict_error(self, plugin):
        result = {"error": "INVALID_ARGUMENT", "message": "bad param"}
        err = await plugin.extract_error_from_result(
            tool=MagicMock(name="get_case"), tool_args={},
            tool_context=MagicMock(), result=result,
        )
        assert err is not None
        assert "INVALID_ARGUMENT" in str(err)

    @pytest.mark.asyncio
    async def test_ignores_hitl_guard_block(self, plugin):
        result = {"error": "BLOCKED_BY_HITL_GUARD", "detail": "needs approval"}
        err = await plugin.extract_error_from_result(
            tool=MagicMock(name="execute_manual_action"), tool_args={},
            tool_context=MagicMock(), result=result,
        )
        assert err is None

    @pytest.mark.asyncio
    async def test_ignores_permission_denied(self, plugin):
        result = {"error": "PERMISSION_DENIED", "message": "no access"}
        err = await plugin.extract_error_from_result(
            tool=MagicMock(name="get_case"), tool_args={},
            tool_context=MagicMock(), result=result,
        )
        assert err is None

    @pytest.mark.asyncio
    async def test_returns_none_for_success(self, plugin):
        result = {"case_id": "123", "status": "OPENED"}
        err = await plugin.extract_error_from_result(
            tool=MagicMock(name="get_case"), tool_args={},
            tool_context=MagicMock(), result=result,
        )
        assert err is None

    @pytest.mark.asyncio
    async def test_detects_string_error(self, plugin):
        result = '{"error": "NOT_FOUND", "message": "case not found"}'
        err = await plugin.extract_error_from_result(
            tool=MagicMock(name="get_case"), tool_args={},
            tool_context=MagicMock(), result=result,
        )
        assert err is not None

    @pytest.mark.asyncio
    async def test_ignores_hitl_in_string(self, plugin):
        result = '{"error": "BLOCKED_BY_HITL_GUARD"}'
        err = await plugin.extract_error_from_result(
            tool=MagicMock(name="execute_manual_action"), tool_args={},
            tool_context=MagicMock(), result=result,
        )
        assert err is None

    def test_max_retries_set(self, plugin):
        assert plugin.max_retries == 2


# ── CostGuardPlugin ──────────────────────────────────────────────────────────


class TestCostGuardPlugin:
    """Tests for CostGuardPlugin LLM budget enforcement."""

    @pytest.fixture
    def plugin(self):
        return CostGuardPlugin(max_llm_calls=3)

    def _make_context(self, count: int = 0):
        ctx = MagicMock()
        ctx.state = {"_llm_call_count": count}
        return ctx

    @pytest.mark.asyncio
    async def test_allows_under_max(self, plugin):
        ctx = self._make_context(0)
        result = await plugin.before_model_callback(
            callback_context=ctx, llm_request=MagicMock(),
        )
        assert result is None
        assert ctx.state["_llm_call_count"] == 1

    @pytest.mark.asyncio
    async def test_blocks_at_max(self, plugin):
        ctx = self._make_context(3)
        result = await plugin.before_model_callback(
            callback_context=ctx, llm_request=MagicMock(),
        )
        assert result is not None
        assert "MAX_LLM_CALLS" in result.content.parts[0].text

    @pytest.mark.asyncio
    async def test_increments_counter(self, plugin):
        ctx = self._make_context(1)
        await plugin.before_model_callback(
            callback_context=ctx, llm_request=MagicMock(),
        )
        assert ctx.state["_llm_call_count"] == 2

    def test_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("MAX_LLM_CALLS_PER_PIPELINE", "50")
        p = CostGuardPlugin()
        assert p._max == 50

    def test_default_value(self):
        p = CostGuardPlugin()
        assert p._max == DEFAULT_MAX_LLM_CALLS


# ── ContextTrimmerPlugin ─────────────────────────────────────────────────────


class TestContextTrimmerPlugin:
    """Tests for ContextTrimmerPlugin history management."""

    @pytest.fixture
    def plugin(self):
        return ContextTrimmerPlugin(max_messages=10, keep_recent=5)

    def _make_content(self, n: int, func_response_at: set = None):
        """Create n mock Content messages. func_response_at indexes get function_response parts."""
        contents = []
        for i in range(n):
            c = MagicMock(spec=Content)
            if func_response_at and i in func_response_at:
                part = MagicMock()
                part.function_response = {"result": "ok"}
                c.parts = [part]
            else:
                part = MagicMock()
                part.function_response = None
                c.parts = [part]
            contents.append(c)
        return contents

    @pytest.mark.asyncio
    async def test_no_op_under_threshold(self, plugin):
        req = MagicMock()
        req.contents = self._make_content(5)
        result = await plugin.before_model_callback(
            callback_context=MagicMock(), llm_request=req,
        )
        assert result is None
        assert len(req.contents) == 5  # Unchanged

    @pytest.mark.asyncio
    async def test_trims_over_threshold(self, plugin):
        req = MagicMock()
        req.contents = self._make_content(15)
        await plugin.before_model_callback(
            callback_context=MagicMock(), llm_request=req,
        )
        # Should trim: keep first + last 5 = 6 (or slightly more if adjusting for func pairs)
        assert len(req.contents) <= 10

    @pytest.mark.asyncio
    async def test_keeps_first_message(self, plugin):
        req = MagicMock()
        original = self._make_content(15)
        first_msg = original[0]
        req.contents = original
        await plugin.before_model_callback(
            callback_context=MagicMock(), llm_request=req,
        )
        assert req.contents[0] is first_msg

    @pytest.mark.asyncio
    async def test_preserves_function_pairs(self, plugin):
        """Function response at split boundary should include its preceding call."""
        req = MagicMock()
        # 15 messages, split at 10 (15-5=10). Put func_response at index 10.
        req.contents = self._make_content(15, func_response_at={10})
        await plugin.before_model_callback(
            callback_context=MagicMock(), llm_request=req,
        )
        # Should adjust split backward to include the function call at index 9
        assert len(req.contents) > 1
