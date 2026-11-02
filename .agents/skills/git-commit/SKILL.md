---
name: git-commit
description: Defines the conventional commit rules to follow. MUST be used on any git commit.
license: MIT
compatibility: Requires git.
---

# Git Commit

## Rules

1. Every commit must be atomic and self-contained.
2. The body, when present, MUST explain the motivation (the *why*) behind the change, not the diff (the *how*).
   It MAY be omitted for trivial changes or if the motivation is conveyed in the title.
   Body lines MUST NOT be wrapped to a fixed width: line-length limits are intentionally disabled.
3. The title and body MUST use the imperative, present tense: "change" not "changed" nor "changes".
4. Commits MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) specification, including its semantic rules (e.g., `feat` = new feature, `fix` = bug fix).
5. The message MUST pass commitlint, which enforces the specification's format rules (configuration: `.commitlintrc.json`).  
   Before committing, pipe the drafted message into below command run from the repository root to validate it.

   ```sh
   npx -y -p @commitlint/cli@21.2.4 -p @commitlint/config-conventional@21.2.4 commitlint
   ```

   After committing, append `-l` and fix via `git commit --amend` until it exits 0.
