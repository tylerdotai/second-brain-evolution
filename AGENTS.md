# AGENTS.md — Development Conventions

Conventions for extending and maintaining the second-brain-evolution skill.

## Core Principle

**Read only. Never edit existing vault notes.**

The skill scans and creates — it does not modify what's already in the vault. If you need to update a note, create a new version alongside the old one, don't overwrite.

## Skill Naming

- Lowercase, hyphenated: `abc-community-posting`, `fitbit-migration`
- Max 64 chars
- Must match `/^[a-z0-9-]+$/`
- One skill per core concept

## Vault Path Convention

```python
import os
vault = os.environ.get("OBSIDIAN_VAULT_PATH")
if not vault:
    vault = os.path.expanduser("~/Documents/Obsidian Vault")
```

Always expand `~` — file tools don't resolve it automatically.

## What Gets Promoted to a Skill

| Note type | Becomes skill? | File location |
|---|---|---|
| Repeatable workflow | Yes | `~/.hermes/skills/` |
| Decision with rationale | Yes | `~/.hermes/skills/` |
| Tool/technique guide | Yes | `~/.hermes/skills/` |
| Resource collection | Yes (if 5+) | `~/.hermes/skills/` |
| Meeting notes | No | Project/Area folder |
| Daily log entry | No | `00.Daily/` |
| One-off observation | No | Resources folder |
| Template | No | `05.Templates/` |

## Skill Creation

Every skill needs:

1. YAML frontmatter with `name` and `description`
2. H1 heading
3. `## When to Use` section
4. Step-by-step procedure
5. `## Verification` section

## Cron Behavior

- Runs at 8am CT daily (configurable)
- Delivers to origin channel (Telegram/Discord DM by default)
- No user present — prompt must be self-contained
- Skills created by cron are reported in the delivery message

## Testing

Before updating the skill:

1. Run the scan on the test vault
2. Verify recent notes are identified
3. Verify skill creation would be correct
4. Verify vault INDEX would be updated
5. Check that no existing notes would be modified

## No External Dependencies

stdlib only. No `pip install`. If you need a new dep, it's the wrong approach.
