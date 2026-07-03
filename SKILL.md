---
name: second-brain-evolution
description: Scan the Obsidian vault for new notes and create reusable skills from patterns.
version: 1.0.0
author: Hermes Agent
license: Unlicense
metadata:
  hermes:
    tags:
      - obsidian
      - second-brain
      - knowledge-management
      - automation
    homepage: https://github.com/tylerdotai/second-brain-evolution
---

# Second Brain Evolution

Scans the Obsidian vault for new and updated notes, identifies patterns and reusable knowledge, and creates skills from what it finds.

**Does NOT edit existing notes** — only reads and creates new skills or updates skill references.

Stdlib only — no external Python dependencies.

## When to Use

- "scan my second brain"
- "evolve my vault"
- "create skills from my notes"
- "check what's new in my vault"
- "find patterns in my notes"

## Prerequisites

- Obsidian vault at `~/Documents/Obsidian Vault` (default) or `$OBSIDIAN_VAULT_PATH`
- Vault follows the standard folder structure (see below)
- `execute_code`, `read_file`, `search_files`, `skill_manage`, `patch`, and `write_file` tools available
- No external pip packages required

## Vault Path

```
Default:  ~/Documents/Obsidian Vault
Override: $OBSIDIAN_VAULT_PATH (set in ~/.hermes/.env)
```

## Vault Structure

The skill works best with this structure:

```
~/Documents/Obsidian Vault/
├── 00.Daily/           ← daily notes (YYYY-MM-DD.md)
├── 01.Inbox/           ← capture zone (raw notes)
├── 02.Projects/        ← project notes
├── 03.Areas/           ← ongoing focus areas
├── 04.Resources/        ← reference material
├── 05.Templates/       ← note templates
├── 06.Archive/        ← completed/inactive
└── INDEX.md            ← vault index
```

## How to Run

1. Scan for recent notes via `execute_code` (last 7 days)
2. Read the vault INDEX and inbox
3. Identify new or recently updated notes
4. Extract patterns — repeated topics, workflows, decisions, insights
5. For each pattern, either create a new skill or link to an existing skill
6. Update the vault INDEX or skill library with new findings

## Procedure

### Step 1 — Scan for New Notes

Use `execute_code` to find recently modified markdown files:

```python
import os
from datetime import datetime, timedelta

vault = os.environ.get("OBSIDIAN_VAULT_PATH") or os.path.expanduser("~/Documents/Obsidian Vault")
cutoff = datetime.now() - timedelta(days=7)  # last 7 days only

recent = []
for root, dirs, files in os.walk(vault):
    dirs[:] = [d for d in dirs if not d.startswith(".")]  # skip hidden
    for f in files:
        if not f.endswith(".md"):
            continue
        path = os.path.join(root, f)
        mtime = os.path.getmtime(path)
        if datetime.fromtimestamp(mtime) > cutoff:
            recent.append((path, mtime))

recent.sort(key=lambda x: x[1], reverse=True)
for path, mtime in recent:
    # print in ascending order so oldest appears first
    pass

# Sort ascending for reading order
recent.sort(key=lambda x: x[0])
for path, mtime in recent:
    print(datetime.fromtimestamp(mtime).isoformat(), "|", path)
```

Run this via `execute_code`. Print nothing if no recent notes found.

### Step 2 — Read New Notes

For each new note, use `read_file` to extract:

- Core idea or insight
- Any explicit workflows or step-by-step processes
- Key decisions or conclusions
- Topics and tags

**Skip** notes that are:
- Template files (`{{date}}`, `{{project-name}}`)
- Meeting notes without decisions
- Raw inbox captures without conclusions

### Step 3 — Identify Skill Opportunities

A note becomes a skill when it contains:

| Content type | Becomes skill? | Destination |
|---|---|---|
| Repeatable workflow | Yes | `~/.hermes/skills/<name>/SKILL.md` |
| Decision with rationale | Yes | `~/.hermes/skills/<name>/SKILL.md` |
| Tool/technique guide | Yes | `~/.hermes/skills/<name>/SKILL.md` |
| Resource collection (5+) | Yes | `~/.hermes/skills/<name>/SKILL.md` |
| Meeting notes | No | Project folder |
| Daily log entry | No | `00.Daily/` |
| One-off observation | No | Resources folder |
| Template | No | `05.Templates/` |

### Step 4 — Create the Skill

Use `skill_manage(action='create')`:

```
skill_manage(
  action: "create",
  name: "<lowercase-hyphenated-skill-name>",
  content: "---\nname: <name>\ndescription: <one-line description>\nversion: 1.0.0\n---\n\n# <Skill Title>\n\n<body>",
  category: "general"
)
```

The skill file is written to `~/.hermes/skills/<name>/SKILL.md`.

### Step 5 — Update the Vault

After creating skills, update the vault:

1. Add a `[[Skill Name]]` wikilink to the source note's "Notes" section
2. Update `INDEX.md` to list the new skill

---

## Pitfalls

**Inbox zero failure** — If `01.Inbox/` piles up, nothing gets processed. File notes into projects/areas/daily, not just the inbox.

**Over-skill-ification** — Not every note needs to become a skill. Meeting notes, raw captures, and one-off observations belong in the project or daily notes.

**Template notes** — Notes with `{{date}}` or `{{project-name}}` are templates. Don't scan templates for skill extraction.

**Large vaults** — Scan only recent notes (last 7 days) by default. Full vault scans are slow on large vaults.

---

## Verification

Run these checks after any change to this skill:

### Test 1 — Scan finds recent notes

```python
import os
from datetime import datetime, timedelta

vault = os.environ.get("OBSIDIAN_VAULT_PATH") or os.path.expanduser("~/Documents/Obsidian Vault")
cutoff = datetime.now() - timedelta(days=7)

found = []
for root, dirs, files in os.walk(vault):
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    for f in files:
        if not f.endswith(".md"):
            continue
        path = os.path.join(root, f)
        if datetime.fromtimestamp(os.path.getmtime(path)) > cutoff:
            found.append(path)

print(f"Found {len(found)} recent notes")
for p in found[:5]:
    print(p)
```

Expected: prints count and paths. If zero, create a test note and re-run.

### Test 2 — Skill creation produces valid SKILL.md

Create a test skill:

```
skill_manage(action="create", name="test-skill-verify", content="---\nname: test-skill-verify\ndescription: test\n---\n\n# Test\n\nTest body.", category="general")
```

Then verify:

```
read_file(path="~/.hermes/skills/test-skill-verify/SKILL.md")
```

Expected: file exists with correct frontmatter.

Clean up: `trash ~/.hermes/skills/test-skill-verify/` after verification.

### Test 3 — Vault INDEX updates correctly

Before running: note the current `INDEX.md` line count.
After running: verify it grew if new skills were created.

---

## Dependencies

None — Python stdlib only. No pip install required.
