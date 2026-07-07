# Unstaged Workflow — Preparation

Run when nothing is staged but `git status --porcelain` shows changed/untracked files.
After these steps, return to [SKILL.md](../SKILL.md) step 2 (Resolve branch).

## 1. Discover all changed files

```bash
git status --porcelain
```

This returns lines like:
- ` M path/file` — modified, not staged
- `?? path/file` — untracked
- ` D path/file` — deleted, not staged
- `MM path/file` — modified, partially staged (treat unstaged part)

Collect all file paths and their statuses.

## 2. Security check

Scan for secret files (see patterns in [SKILL.md](../SKILL.md#secret-files)). **Exclude** any matches from the grouping plan. Warn the user which files are excluded. Do not stage or commit them.

## 3. Read diffs for context

```bash
git diff                         # modified tracked files
git diff --no-index /dev/null <file>   # untracked files (to see content)
```

Read enough of each file/diff to understand its purpose. For large files, read the first ~100 lines.

## 4. Group files into logical commits

Analyze the files and group them by **logical cohesion**. Use these heuristics (in priority order):

1. **Same feature/module**: files in the same directory or module that serve the same feature
2. **Same concern**: e.g., all config changes together, all test files together, all docs together
3. **Cross-cutting but related**: e.g., a utility + the files that use it
4. **Independent standalone changes**: e.g., a lone README fix, a single typo

**Grouping rules:**
- Each group should be a self-contained, reviewable unit
- A group should have 1–8 files; split larger groups further
- Prefer fewer groups over many tiny single-file commits (unless they are truly independent)
- Untracked files go with the group they logically belong to (e.g., a new test file with the feature it tests)
- Deleted files go with the group that explains the deletion (e.g., a refactor that removes old code)

## 5. Present the plan to the user

Before committing, show the user the proposed grouping:

```
Proposed commits (in order):

1. feat: add user auth middleware
   - src/middleware/auth.ts
   - src/middleware/auth.test.ts
   - src/types/auth.ts

2. docs: update API reference for auth endpoints
   - docs/api/auth.md
   - README.md

3. chore: update dependencies
   - package.json
   - package-lock.json
```

Ask for confirmation. The user may:
- **Approve** → proceed
- **Rearrange** → adjust groups and re-present
- **Exclude files** → remove files from the plan
