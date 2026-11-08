# Tasks

## 1. Validation

- [x] 1.1 Verify the split delta validates strict — `openspec validate split-settings-example-requirement --strict` exits 0 with no length warnings
- [x] 1.2 Verify `make ci` stays green (spec-only change, no code) — lint, type check, tests at 100% coverage

## Workflow follow-up

- Archive this change (move to `changes/archive/` + spec sync) once the user has reviewed — its own commit, per repo convention. Verify the synced `settings` main spec passes `openspec validate --specs --strict` (the length warning is gone).
