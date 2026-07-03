# SKILL.md — Second Brain Evolution

Scans the Obsidian vault for new and updated notes, identifies patterns and reusable knowledge, and creates skills from what's found.

Does NOT edit existing notes — only reads and creates new skills or updates skill references.

stdlib only — no external dependencies.

## When to Use

- "scan my second brain"
- "evolve my vault"
- "create skills from my notes"
- "check what's new in my vault"
- "find patterns in my notes"

## Vault Path

Default: `~/Documents/Obsidian Vault`

Override via `OBSIDIAN_VAULT_PATH` environment variable.

## How to Run

1. List recent notes via `search_files` with `target: "files"`, `pattern: "*.md"`, and `path: ~/Documents/Obsidian Vault`
2. Read the vault INDEX (`INDEX.md`) and inbox (`01.Inbox/Inbox.md`)
3. Identify new or recently updated notes
4. Extract patterns — repeated topics, workflows, decisions, or insights
5. For each pattern, either create a new skill or link to an existing skill
6. Update the vault INDEX or skill library with new findings

## Procedure

### Step 1 — Scan for New Notes

Use `execute_code` to find recently modified markdown files:

```python
import os
from datetime import datetime, timedelta

vault = os.path.expanduser("~/Documents/Obsidian Vault")
cutoff = datetime.now() - timedelta(days=7)  # last 7 days

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
    print(datetime.fromtimestamp(mtime).isoformat(), path)
```

### Step 2 — Read New Notes

For each new note, extract:
- Core idea or insight
- Any explicit workflows or processes
- Key decisions or conclusions
- Topics and tags

Skip: template notes (`{{date}}`, `{{project-name}}`), meeting notes without conclusions.

### Step 3 — Identify Skill Opportunities

A note becomes a skill when it contains:
- A repeatable process or workflow (step-by-step)
- A decision pattern (context → choice → outcome)
- A technique or approach worth reusing
- A collection of related links/resources on a topic

### Step 4 — Create the Skill

Use `skill_manage(action='create')`:

```python
skill_manage(
    action='create',
    name='<skill-name>',  # lowercase-hyphenated
    content='---\nname: <skill-name>\ndescription: <one-line description>\n---\n\n# <Skill Title>\n\n<body>',
    category='general'  # or relevant category
)
```

The skill goes into `~/.hermes/skills/<skill-name>/SKILL.md`.

### Step 5 — Update Vault

After creating skills, add a link to the new skill in the vault:
- Update the source note's "Notes" section with `[[Skill Name]]`
- Update `INDEX.md` to reflect new skills created

## Pitfalls

**Inbox zero failure** — If `01.Inbox/` piles up, nothing gets processed. File notes into projects/areas/daily, not just the inbox.

**Over-skill-ification** — Not every note needs to become a skill. Meeting notes, raw captures, and one-off observations belong in the project or daily notes.

**Template notes** — Notes with `{{date}}` or `{{project-name}}` are templates. Don't scan templates for skill extraction.

**Large vaults** — Scan only recent notes (last 7 days) by default. Full vault scans are slow on large vaults.

## Verification

1. Recent notes are identified correctly
2. New skills were created in `~/.hermes/skills/`
3. Vault INDEX was updated to reflect new skills
