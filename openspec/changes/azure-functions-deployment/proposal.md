# Proposal

## Why

The club's article workflow ends in SharePoint: editors finish a `.docx` in the
finished-articles library and an approval flow signs it off. Publishing to the
Joomla site is still a manual local step (`docxwire <file>`). This change makes
that last step automatic: an Azure Function (Flex Consumption, Python) is
invoked by the approval automation, fetches the approved file itself from
SharePoint via Microsoft Graph, and publishes it by invoking the `docxwire`
CLI. The function tracks project releases, so every new `docxwire` release is
deployed to it without further work.

## What Changes

- New `azure/` function app in this repository: an authenticated HTTP trigger
  that receives the SharePoint item reference (site, list, item) from the
  approval automation, downloads the `.docx` via Microsoft Graph using the
  function app's identity, and publishes it by invoking the `docxwire` CLI —
  the project's automation entry point — as a subprocess
- This change depends on `cli-automation-interface`, which makes the CLI
  automation-ready: env-based settings selected by `--settings-env` (so the
  CLI is configured through Azure Application Settings instead of a
  `settings.toml` file) and a `--json` machine-readable output mode
- New `.github/workflows/deploy-function-app.yml`: on every push to `main`
  touching `azure/` (plus manual dispatch) it installs the pinned `docxwire`
  plus the function's dependencies from `azure/requirements.txt`, logs in
  with OIDC, and deploys with `Azure/functions-action` (`remote-build` off;
  local packaging) — a plain "deploy what is on `main`" pipeline
- The function's `requirements.txt` pins `docxwire` as a git install at the
  released tag — the GitHub Release remains the distribution surface, no PyPI
  publishing (consistent with the `automated-releases` non-goal); Renovate
  tracks that pin natively (pip manager, `git-tags` datasource) and opens a
  bump PR per new release, which deploys the function when merged
- A small `azure/README.md` next to the code (no standalone `docs/` file):
  the app-settings table (`DOXXWIRE_JOOMLA_*`, `PUBLISH_API_KEY`, and
  `PYTHON_VERSION` matching the repo's `.python-version`) and the Power
  Automate flow contract (endpoint, `X-Api-Key` header, JSON body), with
  the setup mechanics linked to the official GitHub/Azure documentation

Non-goals: provisioning Azure resources (no IaC in this change), the Power
Automate flow itself, PyPI publishing, duplicate suppression (a re-triggered
file always creates a new draft article, matching v0.1.0 behavior), and
update/delete flows (create-only, as today).

## Capabilities

### New Capabilities

(None — tooling/deployment change; `skip_specs: true` in `.openspec.yaml`)

### Modified Capabilities

(None)

## Impact

- `azure/` — new function app (handler, `requirements.txt`, `host.json`,
  `.funcignore`, small `README.md` with app settings and the flow contract)
- `azure/tests/` (or `tests/function/`) — tests for the handler, keeping
  `make ci` green at 100% coverage
- `.github/workflows/deploy-function-app.yml` — new workflow
- `renovate.json` — no changes: the pip manager already picks up
  `azure/requirements.txt` (including the `git+…@tag` pin) with its default
  configuration
- `pyproject.toml` — no runtime dependency changes to the core library
- External: Azure subscription (function app on Flex Consumption, storage
  account), Microsoft Entra (app registration / consent for SharePoint
  `Files.Read`), GitHub repository secrets (`AZURE_CLIENT_ID`,
  `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`), a Power Automate flow
  (club tenant, outside this repo)
