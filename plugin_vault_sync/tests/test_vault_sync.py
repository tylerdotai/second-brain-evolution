"""
Tests for vault-sync Hermes plugin.
Covers: deduplication, daily note creation, vault indexing, hook registration.
Run with: pytest ~/.hermes/plugins/vault_sync/tests/test_vault_sync.py -v
"""

from __future__ import annotations

import os
import sys
import threading
import time
from datetime import datetime
from importlib import util as importlib_util
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Load the plugin module via importlib (bypasses sys.path issues)
# ---------------------------------------------------------------------------

_plugin_init = Path(__file__).parent.parent / "__init__.py"
_spec = importlib_util.spec_from_file_location("vault_sync", _plugin_init)
_vs = importlib_util.module_from_spec(_spec)
sys.modules["vault_sync"] = _vs
_spec.loader.exec_module(_vs)
vs = _vs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_vault(tmp_path: Path) -> Path:
    """Create a minimal vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "INDEX.md").write_text("# Vault Index\n\n")
    return vault


def _reset_module():
    """Reset VAULT_PATH and seen-IDs for each test."""
    vs.VAULT_PATH = str(Path("__not_set__"))
    vs._seen_ids.clear()


# ---------------------------------------------------------------------------
# Test: deduplication — same turn_id not written twice
# ---------------------------------------------------------------------------

def test_dedup_same_turn_id_not_written_twice(tmp_path: Path):
    """
    When on_post_llm_call is called twice with the same (user, assistant) pair,
    the second call must NOT append a second entry to the daily note.
    """
    vault = _mock_vault(tmp_path)
    _reset_module()
    vs.VAULT_PATH = str(vault)

    user_msg = "What is the weather in Dallas?"
    asst_resp = "It's sunny and 82°F in Dallas right now."

    # First call — should write
    vs.on_post_llm_call(
        session_id="test-sess-001",
        conversation_history=[],
        user_message=user_msg,
        assistant_response=asst_resp,
        tool_call_count=0,
    )
    time.sleep(0.15)  # let background thread finish

    daily_file = vault / "00.Daily" / (datetime.now().strftime("%Y-%m-%d") + ".md")
    assert daily_file.exists(), "Daily note should be created"
    first_content = daily_file.read_text()
    first_count = first_content.count("## ")

    # Second call — identical inputs, should be deduped
    vs.on_post_llm_call(
        session_id="test-sess-001",
        conversation_history=[],
        user_message=user_msg,
        assistant_response=asst_resp,
        tool_call_count=0,
    )
    time.sleep(0.15)

    second_content = daily_file.read_text()
    assert second_content.count("## ") == first_count, (
        f"Duplicate entry written! First had {first_count} headers, second has {second_content.count('## ')}"
    )


# ---------------------------------------------------------------------------
# Test: different sessions produce separate entries
# ---------------------------------------------------------------------------

def test_different_sessions_produce_separate_entries(tmp_path: Path):
    """Different session IDs with different content produce separate entries."""
    vault = _mock_vault(tmp_path)
    _reset_module()
    vs.VAULT_PATH = str(vault)

    vs.on_post_llm_call(
        session_id="session-alpha",
        conversation_history=[],
        user_message="Deploy the API to production",
        assistant_response="Deploying...",
        tool_call_count=1,
    )
    vs.on_post_llm_call(
        session_id="session-beta",
        conversation_history=[],
        user_message="Check the logs",
        assistant_response="Here are the logs...",
        tool_call_count=0,
    )
    time.sleep(0.15)

    daily_file = vault / "00.Daily" / (datetime.now().strftime("%Y-%m-%d") + ".md")
    content = daily_file.read_text()
    assert "Deploy the API to production" in content, "Deploy entry missing"
    assert "Check the logs" in content, "Check logs entry missing"


# ---------------------------------------------------------------------------
# Test: INDEX.md is updated with daily note reference
# ---------------------------------------------------------------------------

def test_index_updated_after_first_write(tmp_path: Path):
    """INDEX.md gains a pointer to the daily note on first write."""
    vault = _mock_vault(tmp_path)
    _reset_module()
    vs.VAULT_PATH = str(vault)

    initial_index = (vault / "INDEX.md").read_text()
    assert "00.Daily" not in initial_index

    vs.on_post_llm_call(
        session_id="test-sess-002",
        conversation_history=[],
        user_message="Log this",
        assistant_response="Logged.",
        tool_call_count=0,
    )
    time.sleep(0.15)

    updated_index = (vault / "INDEX.md").read_text()
    today = datetime.now().strftime("%Y-%m-%d")
    assert f"00.Daily/{today}.md" in updated_index, (
        f"INDEX.md not updated. Got:\n{updated_index}"
    )


# ---------------------------------------------------------------------------
# Test: vault directory created if missing
# ---------------------------------------------------------------------------

def test_creates_daily_dir_if_missing(tmp_path: Path):
    """If 00.Daily doesn't exist, on_post_llm_call creates it."""
    vault = _mock_vault(tmp_path)
    daily_dir = vault / "00.Daily"
    assert not daily_dir.exists()
    _reset_module()
    vs.VAULT_PATH = str(vault)

    vs.on_post_llm_call(
        session_id="test-sess-003",
        conversation_history=[],
        user_message="Start a new project",
        assistant_response="What shall we build?",
        tool_call_count=0,
    )
    time.sleep(0.15)

    assert daily_dir.exists(), "00.Daily directory should be auto-created"


# ---------------------------------------------------------------------------
# Test: thread safety — concurrent calls don't corrupt the file
# ---------------------------------------------------------------------------

def test_concurrent_calls_thread_safe(tmp_path: Path):
    """Multiple simultaneous calls don't race and corrupt the daily note."""
    vault = _mock_vault(tmp_path)
    _reset_module()
    vs.VAULT_PATH = str(vault)

    errors = []

    def make_call(i: int):
        try:
            vs.on_post_llm_call(
                session_id=f"concurrent-{i}",
                conversation_history=[],
                user_message=f"Request number {i}",
                assistant_response=f"Response number {i} with some content here",
                tool_call_count=1,
            )
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=make_call, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    time.sleep(0.2)

    assert not errors, f"Errors during concurrent calls: {errors}"

    daily_file = vault / "00.Daily" / (datetime.now().strftime("%Y-%m-%d") + ".md")
    assert daily_file.exists()
    content = daily_file.read_text()
    for i in range(20):
        assert f"Request number {i}" in content, f"Entry {i} missing from daily note"


# ---------------------------------------------------------------------------
# Test: turn_id is stable across calls
# ---------------------------------------------------------------------------

def test_turn_id_stable(tmp_path: Path):
    """Same user+assistant text produces the same turn_id."""
    vault = _mock_vault(tmp_path)
    _reset_module()
    vs.VAULT_PATH = str(vault)

    user = "Fix the bug in auth"
    asst = "The issue was a missing null check."

    id1 = vs._turn_id(user, asst)
    id2 = vs._turn_id(user, asst)
    assert id1 == id2, "turn_id must be deterministic"

    id3 = vs._turn_id("Different request", asst)
    assert id1 != id3


# ---------------------------------------------------------------------------
# Test: register() calls ctx.register_hook with correct hook name
# ---------------------------------------------------------------------------

def test_register_hooks_post_llm_call(tmp_path: Path):
    """register() calls register_hook with 'post_llm_call'."""
    vault = _mock_vault(tmp_path)
    _reset_module()
    vs.VAULT_PATH = str(vault)

    registered_hooks = []

    class MockCtx:
        def register_hook(self, name, cb):
            registered_hooks.append((name, cb))

    vs.register(MockCtx())

    assert ("post_llm_call", vs.on_post_llm_call) in registered_hooks, (
        f"Expected post_llm_call to be registered, got: {registered_hooks}"
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
