# Second Brain Evolution

<!-- LOGO -->
<div align="center">
  <img src="images/logo.svg" alt="Second Brain Evolution logo" width="80" height="80">
</div>

<!-- SHIELDS -->
<div align="center">

[![License: Unlicense](https://img.shields.io/github/license/tylerdotai/second-brain-evolution?style=flat-square)](https://github.com/tylerdotai/second-brain-evolution)
[![Stars](https://img.shields.io/github/stars/tylerdotai/second-brain-evolution?style=flat-square)](https://github.com/tylerdotai/second-brain-evolution/stargazers)
[![Issues](https://img.shields.io/github/issues/tylerdotai/second-brain-evolution?style=flat-square)](https://github.com/tylerdotai/second-brain-evolution/issues)
[![Last Commit](https://img.shields.io/github/last-commit/tylerdotai/second-brain-evolution/master?style=flat-square)](https://github.com/tylerdotai/second-brain-evolution/commits/master)

</div>

## Index

| Section | Description |
|---------|-------------|
| [What This Is](#what-this-is) | Overview of the two components |
| [Quick Start](#quick-start) | Get up and running in 5 minutes |
| [Architecture](#architecture) | How vault-sync and the skill work together |
| [Plugin: vault-sync](#plugin-vault-sync) | Hermes plugin — auto-writes turns to vault |
| [Skill: second-brain-evolution](#skill-second-brain-evolution) | Pattern detection + skill creation |
| [Verification Tests](#verification-tests) | All 7 tests pass — not a proof of concept |
| [Vault Structure](#vault-structure) | Expected Obsidian vault layout |
| [Configuration](#configuration) | Customising VAULT_PATH and behavior |
| [Public API](#public-api) | Key functions for extension |

---

## What This Is

Two components that work together to evolve a second brain from conversation:

1. **vault-sync** — A Hermes plugin that writes every meaningful conversation turn to your Obsidian vault, automatically. No manual capture needed.
2. **second-brain-evolution** — A Hermes skill that scans the vault, finds patterns, and auto-creates reusable skills from what it learns.

**The mechanism:** Hermes already auto-creates skills via its `curator` module — iteration-count triggered, background forked agent, calls `skill_manage` to write skills. This system replicates that same pattern for the vault: every turn → daily note → pattern scan → new skill.

---

## Quick Start

### 1. Install the vault-sync plugin

```bash
# Clone into your Hermes plugins directory
git clone https://github.com/tylerdotai/second-brain-evolution.git ~/.hermes/plugins/vault_sync

# Restart Hermes to load the plugin
```

The plugin will automatically create `~/Documents/Obsidian Vault/00.Daily/YYYY-MM-DD.md` and write turn summaries there after every conversation.

### 2. Create your vault structure

```
~/Documents/Obsidian Vault/
├── INDEX.md
├── Start Here.md
├── Skill Inventory.md
├── 00.Daily/
│   └── YYYY-MM-DD.md        ← auto-created by vault-sync
├── 01.Inbox/
├── 02.Projects/
├── 03.Areas/
├── 04.Resources/
├── 05.Templates/
└── 06.Archive/
```

See [Vault Structure](#vault-structure) for the full spec.

### 3. Load the skill

```
/second-brain-evolution
```

Or trigger manually: *"scan my second brain"*

### 4. Verify it's working

```bash
# Run the verification tests
python -m pytest ~/.hermes/plugins/vault_sync/tests/test_vault_sync.py -v

# Check today's daily note
cat ~/Documents/Obsidian\ Vault/00.Daily/$(date +%Y-%m-%d).md
```

---

## Architecture

```
Conversation turn ends
       │
       ▼
turn_finalizer.py detects: nudge interval exceeded
       │
       ▼
post_llm_call hook fires (vault-sync plugin)
       │
       ▼                              Background thread, non-blocking
_writes turn to 00.Daily/YYYY-MM-DD.md   ← vault-sync
       │                                       │
       │                              deduplication check
       │                              (turn_id via SHA-1)
       ▼
second-brain-evolution skill             INDEX.md updated
       │                              (daily note linked)
       ▼
Scans vault for new notes
since last run
       │
       ▼
Finds patterns (≥3 occurrences OR high confidence)
       │
       ▼
skill_manage creates SKILL.md in ~/.hermes/skills/
       │
       ▼
INDEX.md updated with new skill reference
```

**Hermes's own curator mechanism (reverse-engineered):**

```
turn_finalizer.py checks: _iters_since_skill >= _skill_nudge_interval?
       │
       ▼
if true → spawns background AIAgent (background_review.py)
       │
       ▼
fork runs curator.py → skill_manage to create/update/archive skills
       │
       ▼
Writes go to ~/.hermes/skills/ — completely background
```

This system applies the same trigger logic to vault notes instead of skills.

---

## Plugin: vault-sync

**Location:** `~/.hermes/plugins/vault_sync/`

### What it does

- Listens to the `post_llm_call` hook — fires after every conversation turn
- Writes a structured entry to `00.Daily/YYYY-MM-DD.md`
- Updates `INDEX.md` with a link to the daily note
- Thread-safe, deduplicated (SHA-1 turn ID — same turn won't be written twice)
- Non-blocking — runs on a background thread

### Turn entry format

```markdown
## 14:32 UTC — What is the weather in Dallas? [[sess-1234]]

**0 tool calls** — `a1b2c3d4`

It's sunny and 82°F in Dallas right now.
```

### Key behaviors

| Behavior | Detail |
|----------|--------|
| **Deduplication** | SHA-1 hash of first 200 chars of user+assistant text. Same turn won't be written twice even across sessions. |
| **Minimal response gate** | Skips turns with < 3 bytes of assistant response. |
| **Thread safety** | `threading.Lock` around seen-IDs set and file writes. |
| **INDEX update** | Appends `- [[00.Daily/YYYY-MM-DD.md]]` to vault root `INDEX.md`. |

### Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `VAULT_PATH` | `~/Documents/Obsidian Vault` | Path to your vault |

---

## Skill: second-brain-evolution

**Location:** `~/.hermes/skills/second-brain-evolution/`

### What it does

Scans the vault for notes created or updated since the last run. Identifies patterns across notes (topics mentioned 3+ times, repeated workflows, shared contexts) and creates reusable skills from them.

### Trigger modes

1. **Manual** — invoke via `/second-brain-evolution` or say *"scan my second brain"*
2. **Automatic** — daily cron at 8am CT (`second-brain-daily-scan` job)
3. **On-demand** — any time you want to force a scan

### Pattern detection rules

- **Topic repetition** — same keyword/phrase appears in ≥ 3 distinct notes
- **Template candidate** — a note with a consistent structure used ≥ 2 times
- **High confidence** — single strong signal (e.g., explicit "this should be a skill" language)

### What it creates

Skills saved to `~/.hermes/skills/` with this structure:

```
~/.hermes/skills/
├── skill-name/
│   ├── SKILL.md          ← the skill file
│   └── references/      ← supporting files
│       ├── pattern.md    ← why this skill was created
│       └── examples.md   ← usage examples from the vault
```

---

## Verification Tests

**All 7 tests pass — production-ready, not a proof of concept.**

```
$ python -m pytest ~/.hermes/plugins/vault_sync/tests/test_vault_sync.py -v

test_dedup_same_turn_id_not_written_twice      PASSED
test_different_sessions_produce_separate_entries PASSED
test_index_updated_after_first_write            PASSED
test_creates_daily_dir_if_missing              PASSED
test_concurrent_calls_thread_safe              PASSED
test_turn_id_stable                            PASSED
test_register_hooks_post_llm_call              PASSED

7 passed in 1.00s
```

Test coverage:

- ✅ Deduplication — identical turns not written twice
- ✅ Separate entries — different content produces distinct entries
- ✅ INDEX updated — daily note linked in vault index
- ✅ Auto-creates directory — 00.Daily created on first write
- ✅ Thread safety — 20 concurrent calls, no data loss
- ✅ Stable turn ID — SHA-1 hash is deterministic
- ✅ Hook registration — `post_llm_call` correctly registered

---

## Vault Structure

```
~/Documents/Obsidian Vault/
├── INDEX.md                     ← entry point, links to all sections
├── Start Here.md                ← orientation for new readers
├── Skill Inventory.md           ← registry of all generated skills
├── 00.Daily/
│   ├── YYYY-MM-DD.md            ← auto-written by vault-sync
│   └── ...                      ← one per day
├── 01.Inbox/
│   └── Inbox.md                 ← capture zone
├── 02.Projects/
│   ├── Projects Index.md
│   └── <project-name>/
│       └── Hub.md               ← per-project notes
├── 03.Areas/
│   ├── Areas Index.md
│   └── <area-name>.md           ← ongoing responsibility areas
├── 04.Resources/
│   ├── Resources Index.md
│   └── <resource-name>.md       ← tools, references, links
├── 05.Templates/
│   ├── Daily Note Template.md
│   └── Project Template.md
└── 06.Archive/
    └── ...                      ← inactive projects and notes
```

### Folder semantics

| Folder | Purpose | Note count |
|--------|---------|------------|
| `00.Daily/` | Timestamped conversation turns | Grows daily |
| `01.Inbox/` | Raw capture — triage later | Low |
| `02.Projects/` | Active project work | Medium |
| `03.Areas/` | Ongoing responsibilities | Medium |
| `04.Resources/` | Reference material | High |
| `05.Templates/` | Reusable note structures | Low |
| `06.Archive/` | Inactive, kept for history | Grows over time |

---

## Configuration

### vault-sync plugin

```bash
# Custom vault path
export VAULT_PATH=/path/to/your/vault

# Or in your shell profile (~/.bashrc, ~/.zshrc)
echo 'export VAULT_PATH=~/my-vault' >> ~/.bashrc
```

### second-brain-evolution skill

No configuration required. The skill reads from the vault at `VAULT_PATH` and writes skills to `~/.hermes/skills/`.

---

## Public API

### vault-sync plugin

```python
from vault_sync import (
    on_post_llm_call,  # hook callback
    register,           # plugin registration
    VAULT_PATH,         # configured vault path
    _turn_id,           # stable SHA-1 hash of (user, assistant)
    _append_to_daily,   # write one turn entry
    _update_vault_index,# update vault INDEX.md
)
```

### second-brain-evolution skill

```bash
# Manual trigger
/second-brain-evolution

# Or via Hermes skill loader
skill_view(name='second-brain-evolution')
```

---

## License

Public domain — see [LICENSE](LICENSE).
