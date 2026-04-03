---
name: ship
description: >
  End-to-end git workflow: commit changes, push to branch, and open a PR.
  Handles both staged and unstaged changes. When files are staged, commits them directly.
  When nothing is staged, discovers all changed files, groups them logically, and creates
  progressive commits before pushing and opening a PR.
  Triggers on: "/ship", "ship these changes", "commit push and PR",
  "commit the staged stuff and open a PR", "push and PR",
  "create commits from staged changes and raise a PR", "ship it".
  Do NOT trigger for plain commit-only requests (/commit) or general git questions.
---

## Overview

Ship all pending work: commit, push, and open a crisp PR. Works in two modes:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Staged** | Files are staged (`git diff --staged` is non-empty) | Single commit of staged files |
| **Auto-group** | Nothing staged, but unstaged/untracked changes exist | Discover → group → progressive commits |

## Workflow

### 1. Detect mode & prepare

```bash
git diff --staged --name-status
```

- **Non-empty** → **Staged mode**: follow [references/staged-workflow.md](references/staged-workflow.md)
- **Empty** → check for unstaged/untracked changes:
  ```bash
  git status --porcelain
  ```
  - **Non-empty** → **Auto-group mode**: follow [references/unstaged-workflow.md](references/unstaged-workflow.md)
  - **Empty** → nothing to ship. Stop and tell the user.

### 2. Resolve branch

```bash
git rev-parse --abbrev-ref HEAD
```

- **On `main` (or `master`)**: create a new feature branch:
  ```bash
  git checkout -b u/tezansahu/<camelCaseDescriptor>
  ```
  Derive `<camelCaseDescriptor>` from the changes (e.g., `addShipSkill`, `fixLatencyMetrics`, `authAndDocs`). Always camelCase, always `u/tezansahu/` prefix.
- **On a feature branch**: stay on it.

### 3. Commit

Use Conventional Commits prefixes (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `perf:`). Focus on **why**, not just what.

```bash
git commit -m "$(cat <<'EOF'
<type>: <concise 1-line summary>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Use the exact model name matching the current session (default: `Claude Sonnet 4.6`).

- **Staged mode**: single commit of all validated staged files.
- **Auto-group mode**: progressive commits — stage and commit one group at a time per the approved plan. Verify each with `git log -1 --oneline` before moving to the next.

**Hard rules:**
- Never `--amend` — always create a new commit
- Never `--no-verify` — if a hook fails: diagnose, explain to user, propose fix, wait for confirmation, then create a new commit
- Verify after commit: `git log -1 --oneline`

### 4. Push

```bash
# Check if upstream is set:
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null

# No upstream (new branch):
git push -u origin <branch>

# Upstream already set:
git push
```

Never force-push.

### 5. Open PR

Analyze all commits on the branch:

```bash
git log main..<branch> --oneline
```

```bash
gh pr create --title "<concise title under 70 chars>" --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2 if needed>

## Test plan
- [ ] <what to verify>

---
Co-authored with [GitHub Copilot](https://github.com/features/copilot)
EOF
)"
```

**PR rules:**
- Title: short, factual, under 70 chars
- Summary: 1–3 bullets — what changed and why. For multi-commit PRs, summarize the overall change
- Test plan: concrete checkboxes, not boilerplate
- Footer: `Co-authored with [GitHub Copilot](https://github.com/features/copilot)` when running as Copilot; `Co-authored with [Claude Code](https://claude.com/claude-code)` for Claude Code sessions

Return the PR URL to the user.

## Secret files

In both modes, warn and exclude these from staging/committing:
- `.env`, `.env.*`
- `credentials.json`, `**/credentials.json`
- `*.pem`, `*.key`, `*.p12`, `*.pfx`
- Any file matching common secret patterns
