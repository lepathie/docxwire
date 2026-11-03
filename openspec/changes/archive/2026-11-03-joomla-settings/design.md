# Design

## Context

The package currently contains a single domain subpackage, `docxwire/converter/`, and the root `docxwire` package is an empty namespace — all public API lives in subpackages. There is no configuration facility at all: nothing in the repo can hold a Joomla base URL, API endpoint path, API token, or default category, and the forthcoming Joomla client has nothing to read its configuration from. Constraints: CI enforces 100% test coverage; OpenSpec artifacts are public (no secrets or club internals); the project already requires Python ≥ 3.11.5; no new runtime dependencies were wanted.

## Goals / Non-Goals

**Goals:**

- One validated entry point for per-environment settings, shared by all future consumers.
- Zero new runtime dependencies.
- The converter keeps working with no settings file present.

**Non-Goals:**

- The Joomla client / publishing itself (a later change consumes `load_settings()`).
- Environment-variable overrides, multiple environments per file, config watching.
- Semantic validation of values (e.g. URL format) — that belongs to the consumer.

## Decisions

1. **TOML with stdlib `tomllib`, not YAML with `pyyaml`.** Python's stdlib has no YAML parser, so YAML would add a third-party dependency for a four-key file. `tomllib` (stdlib since 3.11) parses TOML to plain nested dicts, which is exactly the shape needed, and the repo already sets a TOML tone via `pyproject.toml`. Alternatives considered: `pyyaml` (new dependency, rejected on that alone), JSON (no sections/comments, rejected), hand-rolled mini-parser (parser code means coverage and security surface for no gain, rejected).
2. **Top-level module `src/docxwire/settings.py`, not a subpackage.** Settings is a cross-cutting concern with no interface/implementation split, so a `settings/` subpackage would be structure without substance. The root `__init__.py` stays empty; consumers import `docxwire.settings` directly, mirroring how `docxwire.converter` is imported today. The precedent set — subpackage for domains, top-level module for small cross-cutting concerns — is the right one; the future `joomla/` client is a real domain and gets its own subpackage.
3. **Strict at load, lazy at call site.** `load_settings()` validates everything and raises a `SettingsError` with actionable messages (missing file → "create it from `settings.toml.example`"; missing key → names the key; malformed TOML → wrapped, not raw). Only the future publishing step calls it; the converter never imports the module, so a dev without a settings file can still convert. Alternatives: eager validation at import (breaks converter-only use), returning defaults on a missing file (silently misrouted publishing — rejected).
4. **Frozen dataclasses as the settings model.** `Settings` carries a `joomla` section of type `JoomlaSettings` (`base_url`, `base_path`, `token`, `default_catid=0`). Frozen value objects: immutable after load, no hidden state, room to grow with further top-level sections.
5. **`default_catid = 0` aligns with the existing `Article.catid` "unset" sentinel.** The module stores the value; the mapping `0 → default_catid` happens at publish time in the future Joomla client, keeping this module free of publishing semantics.
6. **Validation is presence + type only.** Required keys must be present and of the right type; `default_catid` is the sole optional key. Anything semantic (URL shape, path conventions) is the consumer's job.

## Risks / Trade-offs

- **Token accidentally committed** → `.gitignore` entry plus the example-file workflow make the intended flow obvious; the missing-file error message always points back at `settings.toml.example`.
- **TOML is read-only in the stdlib** (no writer) → irrelevant: the tool never writes the file, developers edit it by hand.
- **Error-path coverage under the 100% bar** → every branch (missing file, malformed TOML, missing section/key, wrong type) gets its own test with a `tmp_path` fixture; the module is small enough that this is exhaustive by construction.
- **Config growth** → a new section later means a new field on `Settings` plus one validation block; the loader's per-section structure is already set up for that.

## Migration Plan

None — new facility, nothing to migrate. Each developer copies `settings.toml.example` to `settings.toml` and fills in real values the first time they need to publish.
