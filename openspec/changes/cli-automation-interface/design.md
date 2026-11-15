# Design

## Context

The CLI today prints two human-oriented lines on success
(`Created draft article <id>: <title>` plus the note line or
`Nothing to review.`), sends `error: …` to stderr on failure, and reads
settings only from `settings.toml` in the CWD. The Azure Function
(`azure-functions-deployment`) will invoke it on downloaded files from a
hosted environment: no CWD settings file, and it needs a result it can parse
without fragile text matching. This change is deliberately self-contained:
the env loader and the CLI flags land together, so the first release that
contains the loader also contains its only entry point.

## Goals / Non-Goals

**Goals:**

- An env-based settings source with validation parity to the TOML source
- A stable, spec-level machine-readable result contract (`--json`)
- A way to select the env source from the CLI (`--settings-env`)
- Zero change to the default behavior for existing users

**Non-Goals:**

- Changing the human-oriented default output
- Other output formats (e.g. NDJSON, YAML)
- Merging/overriding the two settings sources
- A separate automation subcommand or alias

## Decisions

1. **Namespaced `DOXXWIRE_JOOMLA_*` variable names.** The prefix mirrors the
   `[joomla]` section and keeps the variables unambiguous in a function app
   environment that carries many unrelated variables (Azure injects dozens of
   `AWS_*`/`Azure*`/`FUNCTIONS_*` variables). Alternatives: unprefixed
   `JOOMLA_*` (collision-prone) and a single JSON blob variable (an encoding
   layer for no benefit).
2. **Shared validation core; the env source behaves like the TOML file.**
   The per-key checks (required keys present, string/integer types,
   defaults) are factored so both loaders apply the same rules: a missing
   required variable is an error naming the variable, exactly as a missing
   required TOML key is an error; an empty-string value passes the same type
   checks as the corresponding TOML value; optional variables keep the
   TOML loader's defaults. No new validation rules are introduced — the env
   source is the TOML source with the file replaced by the environment, so
   the two cannot drift.
3. **Two flags, not a subcommand.** `--json` and `--settings-env` keep the
   "exactly one positional argument" shape and a single code path; a
   `docxwire auto …` subcommand would duplicate the run logic and the help
   surface.
4. **JSON contract: one object on stdout, exit code as discriminator.**
   In `--json` mode every operational run writes exactly one JSON object to
   stdout: success `{"id": …, "title": …, "note": …}`, failure
   `{"error": "…"}`. The note is `""` when nothing needs review (no
   `Nothing to review.` sentence in JSON). Usage errors (argparse) keep their
   text output and exit code 2. JSON goes to stdout — the one stream an
   automation captures — never to stderr. `json.dumps` uses
   `ensure_ascii=False` so German titles stay readable in logs; the output
   is UTF-8.
5. **`--settings-env` selects exactly one source.** With the flag the CLI
   calls `load_settings_from_env()` and does not look for `settings.toml`
   at all; without it, behavior is exactly as today. No env-over-TOML
   merging — one source per run keeps failures actionable.
6. **The flags compose independently.** `--json` and `--settings-env` can be
   combined (the function's invocation is `docxwire <file> --settings-env
   --json`); each flag changes one axis (output format, settings source).

## Risks / Trade-offs

- **The JSON shape becomes a contract** → it is a spec-level requirement of
  the `cli` capability, so any future change goes through a spec delta; the
  function's tests pin the shape.
- **`--json` on failure still prints to stdout** (unusual for CLI
  convention) → deliberate: an automation capturing stdout gets the error in
  the same place as the success object; the non-zero exit code separates the
  cases.
- **Env pollution** (a stray `DOXXWIRE_JOOMLA_*` variable in the host
  environment) → the namespaced prefix makes accidental collision
  implausible; the function app's settings are explicitly managed.

## Migration Plan

Purely additive: a new loader function and two optional flags. No existing
invocation changes. No migration needed.

## Open Questions

(None)
