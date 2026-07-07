# Staged Workflow — Preparation

Run when `git diff --staged --name-status` is non-empty.
After these steps, return to [SKILL.md](../SKILL.md) step 2 (Resolve branch).

## 1. Review staged files

```bash
git diff --staged --name-status
git diff --staged
```

- Never use `git status -uall`, `git diff HEAD`, or include unstaged files.
- Only operate on what is staged — do not touch the working tree.

## 2. Security check

Scan the staged file list for secret files (see patterns in [SKILL.md](../SKILL.md#secret-files)). **Unstage** any matches:

```bash
git reset HEAD <secret-file>
```

Inform the user which files were excluded and why.
