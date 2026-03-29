# Claude Code Skills

A curated collection of [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills) for hobby projects, research, and everyday dev workflows — ready to drop into your own environment.

## Available Skills

| Skill | Description |
|---|---|
| [project-pitch](./project-pitch/) | Generate a timed narration script + PowerPoint slide deck for any project pitch |
| [insight-extractor](./insight-extractor/) | Extract actionable insights from YouTube videos, articles, and research papers |

---

## Installation

Skills live in:
- **Global** (available in every project): `~/.claude/skills/`
- **Project-local** (only for one repo): `.claude/skills/` inside your repo

### Install a single skill

```bash
# Example: install project-pitch globally
cp -r skills/project-pitch ~/.claude/skills/
```

Or, without cloning this repo at all:

```bash
# Download and install directly from GitHub (replace SKILL_NAME as needed)
SKILL=project-pitch
mkdir -p ~/.claude/skills/$SKILL
curl -L "https://github.com/tezansahu/ai-garage/archive/refs/heads/master.tar.gz" \
  | tar -xz --strip-components=2 -C ~/.claude/skills/$SKILL \
    "ai-garage-master/skills/$SKILL"
```

### Install all skills at once

```bash
# Clone and copy everything
git clone https://github.com/tezansahu/ai-garage.git /tmp/ai-garage
cp -r /tmp/ai-garage/skills/* ~/.claude/skills/
rm -rf /tmp/ai-garage
```

After copying, restart Claude Code (or reload the window in your IDE extension) and the skill will appear as a slash command — e.g., `/project-pitch`.

---

## Anatomy of a Skill

```
skills/
└── my-skill/
    ├── SKILL.md          ← Entry point: frontmatter + full skill prompt
    └── references/       ← Supporting reference docs the skill reads at runtime
        └── *.md
    └── scripts/          ← Optional helper scripts the skill invokes
        └── *.py / *.js
```

The `SKILL.md` frontmatter sets the name, description, and argument hint shown in the `/` command menu:

```markdown
---
name: my-skill
description: "One-line description shown in the skill picker"
argument-hint: "[optional-arg] or leave blank"
---
```

---

## Contributing

Found a bug, want to improve a skill, or have one to add? PRs and issues are welcome.
