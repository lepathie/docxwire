# Tasks

## 1. Verify sync precondition

- [ ] 1.1 Verify the committed generated files are in sync with the pinned CLI: `./node_modules/.bin/openspec update --dry-run --json` reports `"changes": []`, so the gate is green on merge

## 2. CI gate

- [ ] 2.1 Add the `Check generated OpenSpec files are in sync` step (exact text in design.md) after `Validate OpenSpec artifacts` in the `openspec` job of `.github/workflows/ci.yaml`, and verify the workflow YAML still parses and the step asserts `jq '.changes | length'` equals 0
- [ ] 2.2 Verify the gate fires: in a scratch copy of the repo (never the real one), modify a generated `.agents/skills/openspec-*/SKILL.md` file and confirm the new step's command fails there, and passes in the unmodified copy

## 3. Integration

- [ ] 3.1 Run `make ci` and `openspec validate --all`, and verify both exit 0

## Workflow follow-up

- Archive the change once the project's review requirements are satisfied (per repo rules, the archive is the owner's own commit).
