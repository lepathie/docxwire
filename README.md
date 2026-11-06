# DOCxWIRE

[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

> Built for the [Heilbronner Rudergesellschaft Schwaben](https://www.ruderschwaben.de/) — but designed
> for reuse. See [`MOTIVATION.md`](MOTIVATION.md).

Converts `.docx` files to clean HTML and publishes them as draft articles to a Joomla 5 website.

```mermaid
flowchart LR
    C[("Contributor")] -->|"Submit .docx"| S1
    subgraph DOCxWIRE
        S1[Convert] --> S2[Metadata] --> S3[Publish]
    end
    S3 -->|"Create draft"| J["Joomla"]
    R[("Reviewer")] -->|"Review &amp; Publish"| J
```

## Getting started

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management and
[Node.js 22](https://nodejs.org/) (with npm) for the JavaScript tooling (OpenSpec CLI, commitlint).

To set up your environment, run:

```bash
make setup   # Setup environment
```

[Make](https://www.gnu.org/software/make/) serves as the task runner for code quality and testing. Available targets:

```bash
make test              # Run test suite with coverage
make check             # Run all checks
make ci                # Full CI (lint + tests)
make fix               # Auto-fix findings
make lint-commit       # Validate a commit message (piped via stdin)
make openspec-validate # Validate OpenSpec artifacts
```

## Spec-driven development

Features are specified with [OpenSpec](https://openspec.dev) before they are built: proposals, designs, and task lists live in [`openspec/`](openspec/), and agent workflow rules in [`AGENTS.md`](AGENTS.md). The OpenSpec workflow skills are committed to the repo (`.agents/skills/openspec-*/`), and the artifacts are validated in CI with the OpenSpec CLI. The CLI version is declared in [`package.json`](package.json) and installed by `make setup`; validate locally with `make openspec-validate`. If you want the bare `openspec` command on your `PATH` (e.g. to (re)generate the workflow skills with `openspec update`), optionally install the pinned version globally with `npm install -g @fission-ai/openspec@<version from package.json>`.

## Conventional Commits

This project adheres to [Conventional Commits](https://www.conventionalcommits.org/). The `Commit Lint` CI workflow validates commit messages with [commitlint](https://commitlint.js.org/) using the `@commitlint/config-conventional` preset (see [`.commitlintrc.json`](.commitlintrc.json)): it checks the commit landing on `main` and, before a merge, the pull request title. Pull requests are squash-merged, with the title serving as the commit message.
