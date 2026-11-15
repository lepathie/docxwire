# Tasks

Prerequisite: `cli-automation-interface` must be merged first (the function
invokes the CLI with `--settings-env --json`).

## 1. Function app (`azure/`)

- [ ] 1.1 Create the `azure/` scaffold: `host.json` with `functionTimeout: 10`, `requirements.txt` with `azure-functions`, `azure-identity`, and `docxwire` pinned to the then-current release tag `docxwire @ git+https://github.com/<org>/docxwire.git@vX.Y.Z` (the first release carrying `--settings-env`/`--json` — by chain order that is the `cli-automation-interface` release, not an older placeholder), and `.funcignore` excluding VCS/dev files; verify the files exist and `requirements.txt` parses (`pip install --dry-run` in a clean venv)
- [ ] 1.2 Implement the HTTP trigger handler module in `azure/`: `POST /` requiring an `X-Api-Key` header equal to the `PUBLISH_API_KEY` app setting (constant-time compare → 401 JSON on mismatch), then parsing the JSON body fields `site_id`, `list_id`, `item_id` (→ 400 JSON when missing/not strings); verify with unit tests mocking the app registration
- [ ] 1.3 Implement the Graph fetch: `GET /v1.0/sites/{site}/lists/{list}/items/{item}/content` with `DefaultAzureCredential`, saving the bytes to a temp file; Graph/network failure → 502 JSON with a credential-safe message; verify with unit tests mocking the credential and HTTP layer
- [ ] 1.4 Wire the publish step: run the `docxwire` CLI as a subprocess (`docxwire <file> --settings-env --json`), inheriting the function's environment; parse the JSON result (article id, title, note) → 200 with `{"ok": true, "article_id", "title", "note"}`; non-zero exit or unparseable output → 500 JSON with the CLI's error message (no credentials); verify with unit tests covering success and each failure branch
- [ ] 1.5 Verify the whole handler module is exercised: `uv run pytest` green, and the new `azure/` modules are covered by the tests added in 1.2–1.4 (spot-check with `--cov` on the module)

## 2. Deployment workflow

- [ ] 2.1 Create `.github/workflows/deploy-function-app.yml`: triggers `push` to `main` with `paths: ['azure/**']` + `workflow_dispatch`; concurrency guard keyed on the workflow; `actions/setup-python` with `python-version-file: .python-version` (the project's pinned Python, already Renovate-managed); installs the pinned `azure/requirements.txt` as-is into `azure/.python_packages/lib/site-packages` (no tag resolution, no pin rewriting — the pin on `main` is the source of truth); uploads the `azure/` directory as an artifact; verify the YAML parses (`python3 -c 'import yaml,sys; yaml.safe_load(open(...))'`)
- [ ] 2.2 Add the deploy job: download artifact, `azure/login@v3` with the `AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_SUBSCRIPTION_ID` secrets (job `permissions: id-token: write, contents: read`), then `Azure/functions-action@v1` with `app-name` from an env var; pin every action by SHA with the version comment, matching the repo's existing convention; verify the pinned SHAs resolve
- [ ] 2.3 Verify Renovate tracks the `docxwire` git pin: a local `renovate` dry run lists the `docxwire` dependency in `azure/requirements.txt` via the `git-tags` datasource, and no `renovate.json` change is needed
- [ ] 2.4 Verify the workflow file passes the repo's CI (`make lint` is Python/markdown-scoped, so additionally run the YAML parse check and a `yaml`-level review that the job graph matches design.md decision 5)

## 3. Function app README

- [ ] 3.1 Write `azure/README.md`: the app-settings table (`DOCXWIRE_JOOMLA_*`, `PUBLISH_API_KEY`, `PYTHON_VERSION` — noting it must match the repo's `.python-version` — and `FUNCTIONS_VERSION`), the Power Automate flow contract (endpoint URL, `X-Api-Key` header, JSON body `{"site_id", "list_id", "item_id"}`), a note that the setup must be complete before the change is merged (the first merge is the first deployment), and links to the official GitHub/Azure docs for the identity/consent/secret mechanics; verify every setting name and the request contract match the implementation in `azure/`, and that the README contains no real tenant values
- [ ] 3.2 Verify `make ci` is green with the new README (pymarkdown scans it)

## 4. Integration verification

- [ ] 4.1 Run `make ci` on the full change (lint, type check, 100%-coverage tests, specs, deps) and verify it is green
- [ ] 4.2 Verify the release-tracking loop: in a scratch fork, bump the `docxwire` pin in `azure/requirements.txt` and confirm the push to `main` deploys a package containing `docxwire` at the new version (inspect the uploaded artifact); if no scratch app is available, verify the trigger and install steps in a local dry run of the workflow

## Workflow follow-up

- Operator completes the Azure-side setup per `azure/README.md` (function app on Flex Consumption with the repo's pinned Python, identities, consent, secrets) before the change is merged — the merge is the first deployment.
- End-to-end test with a throwaway approved article in SharePoint; verify the draft appears in Joomla.
- Point the Power Automate approval flow at the endpoint and disable the manual publishing step.
- Archive the change after the project's review requirements are satisfied.
