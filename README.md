# Second Brain Evolution

A Hermes Agent skill that scans your Obsidian vault for new and updated notes, identifies patterns, and automatically creates reusable skills from what it finds.

Built for AI agents running [Hermes](https://github.com/nousresearch/hermes-agent) who want a self-evolving knowledge base — the vault gets smarter over time, not just bigger.

---

<!-- SHIELDS -->
[![Hermes Agent Skill](https://img.shields.io/badge/Hermes-Agent-Skill-00B8FF?style=flat-square)](#)
[![Unlicense](https://img.shields.io/badge/License-Unlicense-success?style=flat-square)](LICENSE)

---

## About The Project

Most agents capture notes but never revisit them. This skill closes the loop — a nightly cron job scans your Obsidian vault, extracts repeatable patterns from new notes, and creates reusable skills automatically.

```
You capture → Agent scans → Patterns surface → Skills emerge
```

The skill is designed for the **SSH-only model**: the agent is the scribe, the human is the talker. No desktop app required.

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
- Python stdlib (no pip packages required)

### Installation

**Option 1 — Copy the skill directory**

Copy `SKILL.md` to your Hermes skills directory:

```bash
mkdir -p ~/.hermes/skills/second-brain-evolution/
cp SKILL.md ~/.hermes/skills/second-brain-evolution/SKILL.md
```

**Option 2 — Clone the repo**

```bash
git clone https://github.com/tylerdotai/second-brain-evolution.git
cp -r second-brain-evolution ~/.hermes/skills/second-brain-evolution/
```

### Configuration

Set your vault path in `~/.hermes/.env` (optional — defaults to `~/Documents/Obsidian Vault`):

```bash
OBSIDIAN_VAULT_PATH=~/path/to/your/vault
```

---

## Usage

### Manual trigger

Tell your agent:

> "Scan my second brain and create skills from new notes"

The agent loads the `second-brain-evolution` skill and runs the scan.

### Cron job (recommended)

Create a daily scan job that runs at 8am:

```bash
hermes cron create \
  --name "second-brain-daily-scan" \
  --skill "second-brain-evolution" \
  --schedule "0 8 * * *" \
  --deliver "origin"
```

### Vault structure

The skill works best with a structured vault:

```
~/Documents/Obsidian Vault/
├── 00.Daily/           ← daily notes (YYYY-MM-DD format)
├── 01.Inbox/           ← capture zone
├── 02.Projects/        ← project notes
├── 03.Areas/           ← ongoing focus areas
├── 04.Resources/       ← reference material
├── 05.Templates/      ← note templates
├── 06.Archive/        ← completed/inactive
└── INDEX.md            ← vault index
```

### When a note becomes a skill

The skill creates a new Hermes skill when a note contains:

- A **repeatable process** or step-by-step workflow
- A **decision pattern** (context → choice → outcome)
- A **technique** worth reusing across sessions
- A **collection** of related resources on a topic

The skill does NOT promote notes that are:
- Raw captures with no conclusion
- Meeting notes without decisions
- One-off observations

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
├── README.md          ← you are here
├── SKILL.md           ← the Hermes skill file
├── AGENTS.md          ← AI agent conventions (how to extend)
├── LICENSE            ← public domain (Unlicense)
└── .github/
    └── ISSUE_TEMPLATE/
        └── feature-request.md
```

---

## Extending

See `AGENTS.md` for conventions on extending this skill. Key rules:

- Never edit existing notes — only read and create
- Scan recent files (last 7 days) to avoid performance degradation
- Skills belong in `~/.hermes/skills/`, not the vault
- Use wikilinks in the vault to connect notes to skills

---

## Contributing

Contributions welcome. Open an issue or PR.

---

## License

Released into the public domain under [The Unlicense](LICENSE). Do whatever you want with it.

---

## Acknowledgments

- [othneildrew / Best-README-Template](https://github.com/othneildrew/Best-README-Template) — this README structure
- [Hermes Agent](https://github.com/nousresearch/hermes-agent) — the agent framework this skill runs on
- [Obsidian](https://obsidian.md/) — the vault this skill maintains
