"""
vault-sync — Hermes plugin: write turn summaries to Obsidian vault after each turn.

Hook: post_llm_call
Trigger: every turn where the assistant produced a non-empty text or tool response
Action: append a structured entry to 00.Daily/<date>.md and update INDEX.md

Install: drop this folder into ~/.hermes/plugins/ and restart Hermes.
Config (optional): VAULT_PATH env var — defaults to ~/Documents/Obsidian Vault
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    str(Path.home() / "Documents" / "Obsidian Vault")
)

# Minimum assistant response length to trigger a vault write (bytes).
# Empty or very short responses are skipped.
MIN_RESPONSE_BYTES = 3

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vault() -> Path:
    path = Path(VAULT_PATH)
    if not path.exists():
        logger.warning("vault-sync: vault not found at %s", VAULT_PATH)
    return path


def _daily_path(vault: Path, when: datetime) -> Path:
    """Return path to 00.Daily/YYYY-MM-DD.md, creating the dir if needed."""
    daily_dir = vault / "00.Daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    return daily_dir / f"{when.strftime('%Y-%m-%d')}.md"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _strip_markdown(text: str) -> str:
    """Remove basic markdown noise before writing to vault."""
    text = re.sub(r"```[\s\S]*?```", "", text)      # code blocks
    text = re.sub(r"`[^`]*`", "", text)             # inline code
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # links → label
    text = re.sub(r"[*_~>#|]", "", text)           # bold/italic/strike/quote/table
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_key_content(
    user_message: Any,
    assistant_response: Any,
    messages: List[Dict[str, Any]],
    tool_calls_made: int,
) -> tuple[str, str]:
    """
    Extract a short subject + body from the turn.

    Returns (subject, body) where:
      - subject: one-line topic label (max 80 chars)
      - body: concise summary (max 500 chars)
    """
    # User message
    user_text = ""
    if user_message:
        if isinstance(user_message, str):
            user_text = user_message.strip()
        elif isinstance(user_message, list):
            for part in user_message:
                if isinstance(part, dict) and part.get("type") == "text":
                    user_text = part["text"].strip()
                    break

    # Assistant response
    assistant_text = ""
    if isinstance(assistant_response, str):
        assistant_text = assistant_response.strip()
    elif isinstance(assistant_response, dict):
        content = assistant_response.get("content", "")
        if isinstance(content, str):
            assistant_text = content.strip()

    # Subject: first meaningful line of user query (stripped of common prefixes)
    subject = ""
    if user_text:
        first_line = user_text.split("\n")[0].strip()
        # Strip common slash commands and prefixes
        first_line = re.sub(r"^(/|#\s*)", "", first_line)
        subject = first_line[:80]

    # Fallback subject based on what happened
    if not subject:
        if tool_calls_made > 0:
            subject = f"Tool work ({tool_calls_made} call{'s' if tool_calls_made > 1 else ''})"
        else:
            subject = "Conversation turn"

    # Body: stripped assistant text, truncated
    body = _strip_markdown(assistant_text)
    if len(body) > 500:
        body = body[:497] + "..."
    if not body:
        body = "(no text response)"

    return subject, body


def _turn_id(user_text: str, assistant_text: str) -> str:
    """Stable hash to detect duplicate writes."""
    combined = f"{user_text[:200]}|{assistant_text[:200]}"
    return hashlib.sha1(combined.encode()).hexdigest()[:8]


def _read_daily(path: Path) -> List[str]:
    """Return all existing turn-ID markers in a daily note."""
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8")
        return re.findall(r"^\{TURN-([a-f0-9]{8})\}", content, re.MULTILINE)
    except Exception:
        return []


def _append_to_daily(
    path: Path,
    when: datetime,
    turn_id: str,
    subject: str,
    body: str,
    tool_calls: int,
    session_id: str,
) -> bool:
    """
    Append a turn entry to the daily note.

    Returns True if appended, False if skipped (duplicate).
    """
    existing = _read_daily(path)
    if turn_id in existing:
        logger.debug("turn %s already in %s, skipping", turn_id, path.name)
        return False

    dt = when.strftime("%H:%M UTC")
    session_short = session_id[-8:] if session_id else "local"

    entry = f"""
## {dt} — {subject} [[{session_short}]]

**{tool_calls} tool call{'s' if tool_calls > 1 else ''}** — `{turn_id}`

{body}
"""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except Exception as e:
        logger.warning("vault-sync: failed to write %s: %s", path, e)
        return False


def _update_vault_index(vault: Path, when: datetime) -> None:
    """
    Ensure 00.Daily is listed in the vault root INDEX.md.
    Creates INDEX.md if it doesn't exist. Appends to end of file.
    """
    index_path = vault / "INDEX.md"
    marker = f"- [[00.Daily/{when.strftime('%Y-%m-%d')}.md]]\n"

    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        if marker.strip() in content or marker in content:
            return  # already listed

    # Simply append the marker to the end of the file.
    try:
        with open(index_path, "a", encoding="utf-8") as f:
            f.write(marker)
    except Exception as e:
        logger.warning("vault-sync: failed to update INDEX.md: %s", e)


# ---------------------------------------------------------------------------
# Write queue (thread-safe, deduped)
# ---------------------------------------------------------------------------

_write_lock = threading.Lock()
_seen_ids: Dict[str, bool] = {}   # turn_id → True, persists across calls


def _queue_write(
    user_message: Any,
    assistant_response: Any,
    messages: List[Dict[str, Any]],
    tool_calls_made: int,
    session_id: str,
) -> None:
    """Thread-safe, deduped vault write via the post_llm_call thread."""
    if tool_calls_made == 0 and len(str(assistant_response or "")) < MIN_RESPONSE_BYTES:
        logger.debug("vault-sync: skipping empty turn")
        return

    user_text = str(user_message or "")[:200]
    asst_text = str(assistant_response or "")[:200]
    turn_id = _turn_id(user_text, asst_text)

    with _write_lock:
        if turn_id in _seen_ids:
            return
        _seen_ids[turn_id] = True
        # Cap the seen set to avoid unbounded growth
        if len(_seen_ids) > 1000:
            # Prune half
            prune = list(_seen_ids.keys())[:500]
            for k in prune:
                del _seen_ids[k]

    subject, body = _extract_key_content(
        user_message, assistant_response, messages, tool_calls_made
    )
    when = _now_utc()
    vault = _vault()
    if not vault.exists():
        return

    daily_path = _daily_path(vault, when)
    appended = _append_to_daily(daily_path, when, turn_id, subject, body, tool_calls_made, session_id)
    if appended:
        _update_vault_index(vault, when)
        logger.info("vault-sync: wrote turn %s → %s", turn_id, daily_path.name)


# ---------------------------------------------------------------------------
# Hook callback
# ---------------------------------------------------------------------------

def on_post_llm_call(
    *,
    session_id: str = "",
    conversation_history: List[Dict[str, Any]] = None,
    user_message: Any = None,
    assistant_response: Any = None,
    tool_call_count: int = 0,
    **_: Any,
) -> None:
    """Called by Hermes after every LLM turn via the post_llm_call hook."""
    messages: List[Dict[str, Any]] = conversation_history if conversation_history is not None else []

    # Get the last user message for context
    user_msg = user_message
    if not user_msg:
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content") or m.get("parts")
                if isinstance(user_msg, list):
                    user_msg = user_msg[0].get("text") if user_msg else None
                break

    # Run the vault write on a background thread so we never block the turn
    t = threading.Thread(
        target=_queue_write,
        args=(user_msg, assistant_response, messages, tool_call_count, session_id),
        daemon=True,
    )
    t.start()


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """
    Called by Hermes when loading the plugin.
    ctx is a hermes_cli.plugins.PluginContext.
    """
    ctx.register_hook("post_llm_call", on_post_llm_call)
    logger.info("vault-sync: registered post_llm_call hook → %s", VAULT_PATH)
