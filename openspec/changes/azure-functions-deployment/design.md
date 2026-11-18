# Design

## Context

`v0.2.0` already provides the complete automation-ready publishing pipeline:
the `docxwire` CLI converts a `.docx` (pandoc via `pypandoc-binary`), uploads
images, and creates a draft article via `JoomlaClient`, accepting
`--settings-env` (`DOCXWIRE_JOOMLA_*` environment variables) and `--json`
(a single JSON object on stdout: `{"id", "title", "note"}` on exit 0,
`{"error"}` on operational exit 1). Notably, `DocxConverter` always derives
`Article.slug` (Joomla `alias` and image folder date via `slug_date`) from the
source file's stem (`src.stem`), and falls back `Article.title` to `src.stem`
when the document has no heading.

The function app must therefore (a) expose an authenticated HTTP endpoint,
(b) resolve and download the approved `.docx` from SharePoint under its
original SharePoint filename, and (c) invoke the CLI in a hosted environment
inheriting the function's app settings. Because the repository releases via
python-semantic-release on `main` with GitHub Releases (tags) as the declared
distribution surface (see `automated-releases`), the function consumes
`docxwire` by git release tag rather than from PyPI.

## Goals / Non-Goals

**Goals:**

- An authenticated HTTP endpoint (`POST /api/publish`) the approval automation
  can call with the approved item's SharePoint reference
- Fetching the `.docx` via Microsoft Graph using the function app's Managed
  Identity (`Sites.Selected` least-privilege scope), preserving its SharePoint
  filename so `slug`, folder date, and fallback title match local CLI runs
- A GitHub Actions deployment tracking `azure/` on `main`, paired with a
  Renovate self-pin rule that bumps and automerges new `docxwire` tags so
  releases deploy automatically once CI passes
- `make ci` stays green (lint, types, 100% coverage across `docxwire` and
  `azure/`)

**Non-Goals:**

- Azure provisioning (the function app, storage account, identities, and
  permissions are configured in Azure / Graph by the operator — documented,
  not scripted)
- The Power Automate approval flow (lives in the club tenant)
- Update/delete of previously published articles; duplicate suppression

## Decisions

1. **The function invokes the CLI in a subprocess via `sys.executable`.** The
   `docxwire` CLI is the project's single automation entry point, and running
   it in a child process isolates stdout/stderr/exit codes cleanly under
   concurrent worker threads. Because dependencies are packaged with
   `pip install --target azure/.python_packages/lib/site-packages`, console
   scripts land in `.../site-packages/bin/docxwire` (not on `PATH` in Azure
   Functions, and stamped with the GitHub Actions runner's Python shebang),
   and `v0.2.0` ships no `docxwire.__main__`. The handler therefore runs
   `[sys.executable, "-c", "from docxwire.cli import main; raise SystemExit(main())", str(docx_path), "--settings-env", "--json"]`
   with an explicit timeout and `PYTHONPATH` prepending
   `.python_packages/lib/site-packages` (when present) alongside `sys.path`.
   Alternative considered: importing `publish_article` or calling `cli.main()`
   in-process — rejected because `publish_article` bypasses CLI settings/JSON
   handling, and in-process `sys.stdout` redirection is not thread-safe across
   concurrent HTTP invocations.
2. **HTTP trigger at `POST /api/publish` with fail-closed `X-Api-Key`.** The
   v2 Python trigger registers `@app.route(route="publish", methods=["POST"],
   auth_level=func.AuthLevel.ANONYMOUS)`, keeping Azure Functions' standard
   `/api` route prefix while disabling host function-key enforcement so
   `X-Api-Key` is the single authentication mechanism. If `PUBLISH_API_KEY` is
   unset or empty in app settings, the handler fails closed (`500` JSON) so an
   unconfigured deployment can never match an empty header; otherwise it
   compares `X-Api-Key` to `PUBLISH_API_KEY` with `hmac.compare_digest` (`401`
   JSON on missing or mismatched key). Alternatives: IP allow-list (Power
   Automate egress IPs are broad/shared), Entra-authenticated endpoint (Power
   Automate's HTTP action is awkward with client-credentials), or overriding
   `host.json` `routePrefix` to `""` for `POST /` (unnecessary deviation from
   standard `/api/...` routing).
3. **Two-step Graph `driveItem` fetch preserving filename, under
   `Sites.Selected`.** The JSON request body carries non-empty strings
   `site_id`, `list_id`, `item_id`. Using `DefaultAzureCredential` (the
   function app's Managed Identity — system-assigned, or user-assigned with
   `AZURE_CLIENT_ID` in app settings; no client secret and no separate Entra
   app registration), the handler acquires a token for
   `https://graph.microsoft.com/.default` and calls:
   `GET https://graph.microsoft.com/v1.0/sites/{site}/lists/{list}/items/{item}/driveItem`
   (with URL-encoded path segments: `quote(site_id, safe=",")` for composite
   SharePoint site IDs and `quote(..., safe="")` for `list_id` / `item_id`).
   Note that `listItem` itself has no `/content` segment in Graph v1.0, and a
   direct `/driveItem/content` stream omits the SharePoint filename that
   `DocxConverter` relies on for `Article.slug`, `slug_date`, and fallback
   `Article.title`. Fetching `driveItem` returns both `"name"` and the
   pre-authenticated `"@microsoft.graph.downloadUrl"` in one metadata call (and
   cleanly distinguishes files from folders, which lack `downloadUrl`). The
   handler sanitizes `Path(name).name` (rejecting empty/dot names), downloads
   `@microsoft.graph.downloadUrl` via `requests.get` without an `Authorization`
   header, and writes the bytes to `<temp_dir>/<safe_name>` inside a
   `TemporaryDirectory`. Tenant-side, the Managed Identity's service principal
   is granted the Microsoft Graph application permission `Sites.Selected`
   (admin consent) plus a `read` permission grant on the single target
   SharePoint site (`/v1.0/sites/{siteId}/permissions`) — strictly narrower
   than tenant-wide `Files.Read.All`.
4. **Tag-pinned git install, automerged by Renovate.** `azure/requirements.txt`
   lists `azure-functions`, `azure-identity`, `requests`, and
   `docxwire @ git+https://github.com/lepathie/docxwire.git@v0.2.0`. Renovate's
   `pip_requirements` manager tracks the PEP 508 git URL via the `git-tags`
   datasource. Because `git-tags` exposes no release timestamps, Renovate's
   default `minimumReleaseAgeBehaviour: "timestamp-required"` combined with
   this repo's global `minimumReleaseAge: "7 days"` would hold `docxwire`
   updates indefinitely — and a supply-chain cooldown on this repository's own
   tags serves no purpose. `renovate.json` therefore adds a `packageRule`
   matching `pip_requirements` + `git-tags` + `depName: "docxwire"` with
   `minimumReleaseAge: null`, `automerge: true`, and `platformAutomerge: true`
   (overriding the `0.x` manual-PR default for self-pins). Each new `docxwire`
   release gets a Renovate bump PR that runs CI and automerges under the
   `renovate[bot]` GitHub App identity; because a GitHub App merge triggers
   `push` workflows (and `chore(deps):` commits are ignored by
   python-semantic-release), merging deploys the new tag without triggering a
   release loop.
5. **OIDC deployment, local packaging, hidden-files artifact preservation.**
   `azure/login@v3` authenticates with a user-assigned managed identity via a
   federated credential (`Website Contributor` RBAC scoped to the function
   app), and `Azure/functions-action@v1` deploys the locally packaged `azure/`
   directory (`pip install -r azure/requirements.txt --target
   azure/.python_packages/lib/site-packages`; no `remote-build`/Oryx, and no
   `sku` override needed under OIDC). Because `actions/upload-artifact` (v4+)
   excludes dot-prefixed paths by default, uploading `azure/` between build and
   deploy jobs MUST set `include-hidden-files: true` so
   `azure/.python_packages/` and `azure/.funcignore` are not stripped. No
   Azure-specific resource names or IDs are committed: the workflow reads
   `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` from GitHub
   secrets and `app-name` from `${{ vars.AZURE_FUNCTIONAPP_NAME }}` (a GitHub
   repository variable). Rollback on Flex Consumption (which has no deployment
   slots) is a `git revert` of the offending `azure/` commit on `main`.
6. **Trigger on `azure/**` and workflow changes.** The workflow runs on `push`
   to `main` touching `azure/**` or `.github/workflows/deploy-function-app.yml`
   (plus `workflow_dispatch`), serialized with a concurrency group
   (`cancel-in-progress: false`). Merging a Renovate bump of
   `azure/requirements.txt` triggers deployment automatically; if Azure-side
   setup is not yet complete on the initial merge, the deploy job fails visibly
   on missing secrets/variables and is re-run via `workflow_dispatch` once
   configured.
7. **Timeouts and HTTP load-balancer ceiling.** `azure/host.json` sets
   `"functionTimeout": "00:10:00"` (`hh:mm:ss` TimeSpan string — an explicit
   10-minute worker cap below Flex Consumption's 30-minute default). Outbound
   Graph/download HTTP calls and the CLI subprocess also carry explicit
   timeouts. Note that synchronous Azure Functions HTTP triggers are still
   bounded by Azure Load Balancer's non-configurable 230-second (~3.8 minute)
   idle timeout.
8. **Flex Consumption Python runtime matches `.python-version`.** The function
   app targets the repository's pinned Python (`.python-version`, `3.14` today;
   GA on Flex Consumption, and `pypandoc-binary` ships `py3-none` wheels). The
   workflow's `actions/setup-python` uses `python-version-file:
   .python-version`. On Flex Consumption, the language and Python version are
   resource-level runtime properties (`functionAppConfig.runtime`), NOT
   application settings — legacy `FUNCTIONS_EXTENSION_VERSION`,
   `FUNCTIONS_WORKER_RUNTIME`, and `PYTHON_VERSION` app settings are deprecated
   or rejected on Flex Consumption and must not be set.
9. **Repo test/typecheck layout (`azure/` without `__init__.py`).** Because
   `azure` is Microsoft's PEP 420 namespace package (`azure.functions`,
   `azure.identity`), `azure/` MUST NOT contain `__init__.py` (which would
   shadow the SDK). `azure-functions` and `azure-identity` are added to
   `[dependency-groups] dev` in `pyproject.toml` so `uv sync --frozen` lets
   `ty check .` and `pytest` run against real SDK types without changing core
   library runtime dependencies. Handler tests live in `tests/function/`
   (picked up by `testpaths = ["tests"]`), and `Makefile` passes
   `--cov=docxwire --cov=azure` to enforce 100% coverage across both.
10. **`azure/README.md` instead of a `docs/` file.** Documents the Flex
    Consumption runtime prerequisites, the app-settings table
    (`DOCXWIRE_JOOMLA_*` and `PUBLISH_API_KEY`), GitHub secrets/variable names,
    and the Power Automate HTTP contract (`POST /api/publish`, `X-Api-Key`,
    JSON body, disabling HTTP retries), linking to official GitHub/Azure/Graph
    docs for setup mechanics.

## Risks / Trade-offs

- **230-second HTTP load-balancer timeout & Power Automate retries** → club
  articles convert and upload within seconds, well under 230s; `azure/README.md`
  instructs setting Power Automate's HTTP action retry policy to `none` so a
  transient timeout or 5xx does not automatically re-POST and create duplicate
  drafts.
- **Bundled pandoc binary bloats the deployment package** (~40 MB wheel) →
  well within Flex Consumption deployment limits; if package size ever grows
  problematic, switching `Azure/functions-action` to `remote-build: true`
  (Oryx) is a small workflow change.
- **Tenant consent & site grant are human gates** (admin consent for
  `Sites.Selected` + SharePoint site `read` permission grant on the Managed
  Identity) → covered by `azure/README.md`; until completed, Graph returns 403
  and the function responds `502` with a credential-safe message.
- **Re-triggered file creates a duplicate draft** (accepted decision) → `200`
  responses include `article_id` and `title` so automation history and logs
  identify created drafts clearly.
- **CLI unhandled exceptions on `stderr`** (`cli.py` catches operational
  errors as JSON on `stdout`, whereas an uncaught `requests.RequestException`
  writes a traceback to `stderr` with empty `stdout`) → on non-zero CLI exit,
  the handler relays `"error"` only when `stdout` parses as a JSON error
  object, falling back to a generic credential-safe `500` message rather than
  echoing raw `stderr`.
- **Secrets and pre-authenticated URLs in logs/responses** → the handler logs
  only item IDs/status, never echoes `PUBLISH_API_KEY`, bearer tokens, or
  `@microsoft.graph.downloadUrl` query strings, and compares `X-Api-Key` in
  constant time.
- **`.python-version` bumps require matching Azure runtime updates** →
  `azure/README.md` notes that upgrading the minor Python version in
  `.python-version` requires updating the Flex Consumption function app's
  runtime version in lockstep so compiled wheels in `.python_packages` match
  the host interpreter.

## Migration Plan

1. Operator performs the Azure, Entra/SharePoint, and GitHub secrets/variable
   setup per `azure/README.md` while the PR is open.
2. Merge the repo-side change to `main` (code, tests, dev deps, `renovate.json`,
   workflow, READMEs; `azure/requirements.txt` pinned to `v0.2.0`) — the push
   touches `azure/**` and triggers the initial deployment (meanwhile
   `release.yml` cuts the next repo release, which Renovate then bumps and
   automerges into `azure/requirements.txt`).
3. End-to-end test: invoke `POST /api/publish` (or approve a throwaway
   SharePoint `.docx`) and verify the draft, slug, images, and note in Joomla.
4. Point the Power Automate approval flow at `POST /api/publish` (with retry
   policy `none`).

Rollback: disable the Power Automate flow (stops traffic immediately); revert
the `azure/` commit on `main` to redeploy a previous package version.

## References

External documentation linked from `azure/README.md`:

- Deploy to Azure Functions with GitHub Actions (OIDC +
  `Azure/functions-action`):
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-github-actions>
- Using OpenID Connect in GitHub Actions:
  <https://docs.github.com/en/actions/security-guides/using-openid-connect-in-actions>
- `Azure/functions-action`:
  <https://github.com/Azure/functions-action>
- Python function apps (v2 model & local `pip install --target` packaging):
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python>
- Supported Python runtimes (`3.14` GA on Flex Consumption):
  <https://learn.microsoft.com/en-us/azure/azure-functions/supported-languages>
- Flex Consumption plan (runtime configuration, deprecated app settings,
  package deployment):
  <https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan>
- `host.json` reference (`functionTimeout` TimeSpan & HTTP 230s limit):
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-host-json>
- Graph: get `driveItem` for a SharePoint `listItem` (`name` &
  `@microsoft.graph.downloadUrl`):
  <https://learn.microsoft.com/en-us/graph/api/driveitem-get>
- Graph permissions (`Sites.Selected`) & SharePoint site permission grants:
  <https://learn.microsoft.com/en-us/graph/permissions-reference>
- Renovate `pip_requirements` manager & `minimumReleaseAge`:
  <https://docs.renovatebot.com/modules/manager/pip_requirements/>

## Open Questions

- Exact tenant/environment values (function app name for
  `AZURE_FUNCTIONAPP_NAME`, resource group, SharePoint `site_id`/`list_id`,
  `PUBLISH_API_KEY` value, and whether the function app uses a system-assigned
  or user-assigned Managed Identity for Graph) — operator choices supplied at
  setup time; repository docs use placeholders and document both Managed
  Identity variants.
