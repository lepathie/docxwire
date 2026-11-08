# Tasks

## 1. Gate

- [ ] 1.1 Add `--strict` to the `openspec validate --all` invocation in the Makefile's `check-specs` target — `make check` runs strict validation
- [ ] 1.2 Verify the gate is green on the clean tree — `make ci` (lint, type check, strict spec validation, tests at 100% coverage) passes

## Prerequisite

- `split-settings-example-requirement` must be archived before this change is applied, or `check-specs --strict` fails on the existing 558-character `settings` requirement.
