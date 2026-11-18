# Proposal

## Why

The club's article workflow ends in SharePoint: editors finish a `.docx` in the
finished-articles library and an approval flow signs it off. Publishing to the
Joomla site is still a manual local step (`docxwire <file>`). This change makes
that last step automatic: an Azure Function (Flex Consumption, Python) is
invoked by the approval automation, fetches the approved file itself from
SharePoint via Microsoft Graph (preserving its SharePoint filename so slug,
folder-date, and fallback-title behavior match local runs), and publishes it by
invoking the `docxwire` CLI. The function tracks project releases automatically:
Renovate bumps and automerges the `docxwire` tag pin on each release, deploying
the new version without manual work.

## What Changes

- New `azure/` function app in this repository (`POST /api/publish`): an
  authenticated HTTP trigger (`X-Api-Key`) that receives the SharePoint item
  reference (`site_id`, `list_id`, `item_id`) from the approval automation,
  resolves the item's `driveItem` metadata and downloads the `.docx` under its
  original filename via Microsoft Graph using the function app's Managed
  Identity, and publishes it by invoking the `docxwire` CLI (`--settings-env
  --json`, shipped in `v0.2.0`) in a subprocess via `sys.executable`
- New `.github/workflows/deploy-function-app.yml`: on every push to `main`
  touching `azure/**` or the workflow file itself (plus `workflow_dispatch`),
  it installs the pinned `docxwire` plus the function's dependencies from
  `azure/requirements.txt` into `azure/.python_packages/lib/site-packages`,
  uploads the `azure/` artifact with `include-hidden-files: true`, logs in with
  OIDC (`azure/login@v3`), and deploys with `Azure/functions-action@v1` using
  `${{ vars.AZURE_FUNCTIONAPP_NAME }}` (`remote-build` off; local packaging)
- `azure/requirements.txt` pins `docxwire` as a PEP 508 git install at the
  released tag (`v0.2.0` initially) — the GitHub Release remains the
  distribution surface, with no PyPI publishing (consistent with
  `automated-releases`). A targeted `packageRule` in `renovate.json` disables
  `minimumReleaseAge` (unsupported by `git-tags` under `timestamp-required`)
  and enables `automerge` + `platformAutomerge` on the `docxwire` self-pin so
  each new release opens a bump PR, passes CI, automerges, and deploys
- Dev/CI integration so `make ci` covers the function app at 100% coverage:
  `azure-functions` and `azure-identity` added to `[dependency-groups] dev` in
  `pyproject.toml` (core runtime dependencies unchanged), `--cov=azure` added
  to `Makefile`, and unit tests placed under `tests/function/` (with no
  `azure/__init__.py`, preserving Microsoft's `azure.*` PEP 420 namespace)
- A small `azure/README.md` next to the code (no standalone `docs/` file):
  Flex Consumption runtime prerequisites (Python matching `.python-version`),
  the app-settings table (`DOCXWIRE_JOOMLA_*` and `PUBLISH_API_KEY`), and the
  Power Automate flow contract (`POST /api/publish`, `X-Api-Key` header, JSON
  body, retry policy `none`), linking to official GitHub/Azure documentation
  for identity, consent, and OIDC mechanics; plus a brief note in `README.md`
  for the `renovate.json` self-pin rule

Non-goals: provisioning Azure resources (no IaC in this change), the Power
Automate flow itself, PyPI publishing, duplicate suppression (a re-triggered
file always creates a new draft article, matching current CLI behavior), and
update/delete flows (create-only, as today).

## Capabilities

### New Capabilities

(None — tooling/deployment change; `skip_specs: true` in `.openspec.yaml`)

### Modified Capabilities

(None)

## Impact

- `azure/` — new function app (`function_app.py`, `requirements.txt`,
  `host.json`, `.funcignore`, `README.md`; no `__init__.py`)
- `tests/function/` — unit tests for the handler, keeping `make ci` green at
  100% coverage across both `docxwire` and `azure`
- `pyproject.toml`, `uv.lock`, `Makefile` — `azure-functions` and
  `azure-identity` in `[dependency-groups] dev` (no runtime dependency changes
  to the core library) and `--cov=azure` in `make test`
- `.github/workflows/deploy-function-app.yml` — new OIDC deployment workflow
- `renovate.json`, `README.md` — `packageRule` for the `docxwire` `git-tags`
  self-pin (`minimumReleaseAge: null`, `automerge: true`,
  `platformAutomerge: true`) and matching policy note in `README.md`
- External: Azure subscription (Flex Consumption function app on the repo's
  pinned Python, storage account), Microsoft Entra / SharePoint (Function App
  Managed Identity granted Graph `Sites.Selected` application permission +
  admin consent + `read` permission on the target SharePoint site), GitHub
  repository secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
  `AZURE_SUBSCRIPTION_ID`) and repository variable (`AZURE_FUNCTIONAPP_NAME`),
  and a Power Automate flow (club tenant, outside this repo)
