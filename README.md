# Second Brain Evolution

<!-- LOGO -->
<div align="center">
  <img src="images/logo.svg" alt="Second Brain Evolution logo" width="80" height="80">
</div>

<!-- SHIELDS -->
<div align="center">

![License](https://img.shields.io/github/license/tylerdotai/second-brain-evolution?style=flat-square&color=success)
![Stars](https://img.shields.io/github/stars/tylerdotai/second-brain-evolution?style=flat-square&color=blue)
![Issues](https://img.shields.io/github/issues/tylerdotai/second-brain-evolution?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/tylerdotai/second-brain-evolution?style=flat-square)

**Hermes Agent Skill** — compatible with [Hermes](https://github.com/nousresearch/hermes-agent)

</div>

---

A skill that scans your Obsidian vault for new and updated notes, identifies patterns, and automatically creates reusable skills from what it finds.

Built for the **SSH-only model**: the agent is the scribe, the human is the talker. No desktop app required.

---

## Table of Contents

- [About](#about-the-project)
- [Index](#index)
- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [File Map](#file-map)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## About The Project

Most agents capture notes but never revisit them. This skill closes the loop — a nightly cron job scans your Obsidian vault, extracts repeatable patterns from new notes, and creates reusable skills automatically.

```
You capture → Agent scans → Patterns surface → Skills emerge
```

The agent files notes on the human's behalf during conversations. A daily scan extracts what was captured, promotes patterns to reusable skills, and keeps the vault evolving.

---

## Index

Quick reference for what this skill produces and how to extend it.

| What | Where |
|------|-------|
| Skill definition | `SKILL.md` |
| Agent conventions | `AGENTS.md` |
| Vault structure | See [Vault structure](#vault-structure) below |
| Cron job (daily) | `second-brain-daily-scan` — runs at 8am CT |
| Skill library | `~/.hermes/skills/` |
| Issue tracker | `.github/ISSUE_TEMPLATE/feature-request.md` |

---

## Features

- **Vault scanning** — finds new and updated notes by modification time
- **Pattern extraction** — identifies workflows, decisions, and reusable processes
- **Skill creation** — creates new skills in `~/.hermes/skills/` from vault content
- **Wikilink support** — connects new skills back to source notes
- **Cron-ready** — designed to run daily with zero human intervention
- **Stdlib only** — no external Python dependencies

---

## Getting Started

### Prerequisites

- [Hermes Agent](https://github.com/nousresearch/hermes-agent) installed
- Obsidian vault at `~/Documents/Obsidian Vault` (or custom path)
- Python standard library (no pip packages required)

### Installation

**Option 1 — Clone the repo**

```bash
git clone https://github.com/tylerdotai/second-brain-evolution.git
cp -r second-brain-evolution ~/.hermes/skills/second-brain-evolution/
```

**Option 2 — Install via Hermes CLI**

```bash
hermes skills install https://github.com/tylerdotai/second-brain-evolution
```

**Option 3 — Copy manually**

```bash
mkdir -p ~/.hermes/skills/second-brain-evolution/
cp SKILL.md ~/.hermes/skills/second-brain-evolution/SKILL.md
```

### Configuration

Default vault path: `~/Documents/Obsidian Vault`

Override with the `OBSIDIAN_VAULT_PATH` environment variable (set in `~/.hermes/.env`):

```bash
OBSIDIAN_VAULT_PATH=~/path/to/your/vault
```

---

## Usage

### Manual trigger

Tell your agent:

> "Scan my second brain and create skills from new notes"

The agent loads the `second-brain-evolution` skill and runs the full scan.

### Cron job (recommended)

Create a daily scan job. The skill documents the procedure — use the `cronjob` tool:

```
Action: create
Name: second-brain-daily-scan
Skill: second-brain-evolution
Schedule: 0 8 * * *
Deliver: origin
Attach to session: true
```

The cron runs at 8am CT every day. It loads the skill, scans the vault for notes modified since the last run, promotes patterns to skills, and delivers a summary to your home channel.

### Vault structure

The skill works best with a structured vault:

```
~/Documents/Obsidian Vault/
├── 00.Daily/           ← daily notes (YYYY-MM-DD format)
├── 01.Inbox/           ← capture zone
├── 02.Projects/        ← project notes
├── 03.Areas/           ← ongoing focus areas
├── 04.Resources/        ← reference material
├── 05.Templates/       ← note templates
├── 06.Archive/         ← completed/inactive
└── INDEX.md             ← vault index
```

### When a note becomes a skill

The skill creates a new Hermes skill when a note contains:

- A **repeatable process** or step-by-step workflow
- A **decision pattern** (context → choice → outcome)
- A **technique** worth reusing across sessions
- A **collection** of related resources on a topic (5+ items)

The skill does NOT promote notes that are:

- Raw captures with no conclusion
- Meeting notes without decisions
- One-off observations
- Template notes (`{{date}}`, `{{project-name}}`)

---

## How It Works

```
1. Walk vault → find *.md files modified in last 7 days
2. Read each new note → extract core idea, workflows, decisions
3. Score each note → does it merit a skill?
4. For skill-worthy notes → create ~/.hermes/skills/<name>/SKILL.md
5. Update vault INDEX → reflect new skills created
6. Report → deliver summary to configured channel
```

---

## File Map

```
second-brain-evolution/
├── README.md
├── SKILL.md             ← Hermes skill definition
├── AGENTS.md            ← agent conventions for extending
├── LICENSE              ← public domain (Unlicense)
├── images/
│   └── logo.svg         ← skill logo
└── .github/
    └── ISSUE_TEMPLATE/
        └── feature-request.md
```

---

## Contributing

Contributions welcome. Open an issue or PR.

For conventions on extending this skill, see `AGENTS.md`.

---

## License

Released into the public domain under [The Unlicense](LICENSE). Do whatever you want with it.

---

## Acknowledgments

- [othneildrew / Best-README-Template](https://github.com/othneildrew/Best-README-Template) — README structure
- [Hermes Agent](https://github.com/nousresearch/hermes-agent) — the agent framework this skill runs on
- [Obsidian](https://obsidian.md/) — the vault this skill maintains
