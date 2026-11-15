# Design

## Context

v0.1.0 already provides the complete publishing pipeline: the `docxwire` CLI
converts the `.docx` (pandoc via `pypandoc-binary`), uploads images, and
creates a draft article via `JoomlaClient`. The CLI is the project's
automation entry point, but today it reads `settings.toml` from the working
directory and prints a human-oriented report. The function app must therefore
(a) be callable over HTTP, (b) obtain the file itself from SharePoint, and
(c) drive the CLI in a hosted environment: its invocation inherits the
function's environment, which the CLI's env-based settings and
machine-readable output (prerequisite change `cli-automation-interface`)
make usable. The repo already releases via
python-semantic-release on `main`; the GitHub Release (tag) is the declared
distribution surface (see `automated-releases`), so the function must consume
the package by tag, not from PyPI.

## Goals / Non-Goals

**Goals:**

- An HTTP endpoint the approval automation can call with the approved item's
  SharePoint reference
- The function fetching the `.docx` itself (Microsoft Graph, function app
  identity) and publishing it with the existing pipeline
- A GitHub Actions deployment that tracks `azure/` on `main` (Renovate
  bumps the `docxwire` pin per release), so the deployed function always
  matches the pinned release
- `make ci` stays green (lint, types, 100% coverage) including the new code

**Non-Goals:**

- Azure provisioning (the function app, storage account, and identities are
  created in the portal / Azure CLI by the operator — documented, not scripted)
- The Power Automate approval flow (lives in the club tenant)
- Update/delete of previously published articles; duplicate suppression

## Decisions

1. **The function invokes the CLI as a subprocess.** The `docxwire` command is
   the project's automation entry point — the function runs it on the
   downloaded file (`docxwire <file> --settings-env --json`; the flags come
   from the prerequisite change `cli-automation-interface`) and relays the
   resulting JSON. One tested
   entry point for all automations, a thin function (fetch file → run CLI →
   relay result), and no second in-process integration to keep in sync.
   Alternative considered: importing `publish_article` in-process — rejected
   because it would be a second entry point with its own settings handling,
   drifting from the CLI.
2. **HTTP trigger with API-key header.** `POST /` requires an
   `X-Api-Key` header equal to the `PUBLISH_API_KEY` app setting (constant
   -time compare; 401 on mismatch). Alternatives: IP allow-list (Power
   Automate egress IPs are not stable) and Entra-authenticated endpoint
   (Power Automate's HTTP action does not cleanly do client-credentials
   flows). A shared secret in app settings + header is the standard pattern
   for automation-to-function calls.
3. **Graph fetch with the function app's identity.** The request body carries
   `site_id`, `list_id`, `item_id`; the function calls
   `GET https://graph.microsoft.com/v1.0/sites/{site}/lists/{list}/items/{item}/content`
   with `azure-identity`'s `DefaultAzureCredential` (managed identity, no
   client secret in settings). The endpoint answers a 302 to a
   preauthenticated download URL, which the HTTP client follows to get the
   file bytes. This keeps the function self-contained and the file
   re-fetchable on failure. Requires (tenant-side) an Entra app
   registration with the application permission `Files.Read.All` (the least
   privileged *application* permission for this call; `Files.Read` is
   delegated-only) and admin consent, plus the function app's identity
   granted access to the SharePoint site.
4. **Tag-pinned git install, tracked by Renovate.** The function's
   `requirements.txt` pins `docxwire @ git+https://github.com/<org>/docxwire.git@vX.Y.Z`
   at the current release tag. The pin is set to the then-current release —
   the first one carrying `--settings-env` and `--json` — when this change
   is implemented, and Renovate's pip manager maintains it from there
   (`git-tags` datasource): it opens a bump PR per new release, and merging
   the bump PR is the deployment, so the pin on `main` is always the
   version that is live. This realizes "the function tracks releases"
   without PyPI, per the `automated-releases` non-goal, and without the
   workflow rewriting the pin at build time. The self-pin is subject to the
   repo's own Renovate policy (7-day `minimumReleaseAge`, 0.x bumps as
   manual PRs) — the most conservative dependency in the repo; a one-line
   `packageRule` can relax that if the club wants faster deploys.
5. **OIDC deployment, local packaging.** `azure/login` authenticates with a
   user-assigned managed identity via a federated credential, then
   `Azure/functions-action@v1` deploys the locally built package
   (`pip install -r requirements.txt --target azure/.python_packages/lib/site-packages`).
   No `remote-build`/Oryx: dependencies are resolved in the runner, which also
   lets CI verify the exact tag installs. No Azure-specific values are written
   into the repository or the public docs: the workflow and docs reference
   only the three GitHub Actions secret *names* (`AZURE_CLIENT_ID`,
   `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) with `<placeholder>` values,
   and the setup mechanics are covered by the official GitHub/Azure
   documentation, which the project docs link to rather than reproducing.
   Flex Consumption specifics: it uses package deployment, supports no
   deployment slots, and has no Deployment Center source-control
   integration — the repo-side workflow is the only deployment path, and
   rollback is a `git revert` of the pin-bump commit, which re-deploys the
   previous version.
6. **Trigger on `azure/` changes.** The workflow runs on `push` to `main`
   touching `azure/**` (and `workflow_dispatch`) — a plain
   deploy-what-is-on-`main` pipeline. The Renovate bump PR touches
   `azure/requirements.txt`, so merging it deploys; the concurrency guard
   serializes rapid consecutive deploys. The `release: published` trigger
   was rejected: it couples the deploy to the release event and forces the
   workflow to resolve the tag and rewrite the pin — exactly the moving
   part Renovate replaces. The workflow carries no deployment gate of its
   own — the merge is the gate: the Azure-side setup (function app,
   identity, consent, repository secrets) is independent of the repository,
   so it is done while the change's PR is open, and the first merge — an
   `azure/**` change — is the first deployment. A merge before the setup is
   done fails the deploy job visibly (missing secrets); `workflow_dispatch`
   re-runs it once the setup is complete.
7. **Timeouts.** `host.json` sets `functionTimeout` to 10 minutes (Flex
   Consumption maximum) — conversion of image-heavy documents plus image
   uploads can exceed the 5-minute default.
8. **The function runs on the project's pinned Python.** The app targets the
   same Python as the repository (`.python-version`, 3.14 today) — the
   `requires-python >= 3.11.5` floor is a library minimum, not the deployment
   target; Flex Consumption supports 3.11–3.14, and `pypandoc-binary` ships
   `py3-none` wheels, so the bundled pandoc is Python-version independent.
   The workflow's `actions/setup-python` uses `python-version-file:
   .python-version`, keeping one Renovate-managed source of truth; the Azure
   app setting `PYTHON_VERSION` must match it (noted in `azure/README.md`).
9. **`azure/README.md` instead of a `docs/` file.** The only
   project-specific setup knowledge is the app-settings names
   (`DOXXWIRE_JOOMLA_*`, `PUBLISH_API_KEY`, `PYTHON_VERSION`) and the Power
   Automate flow contract (endpoint, `X-Api-Key` header, JSON body) — that
   lives in a small README next to the code, linking to the official
   GitHub/Azure docs for the mechanics.
10. **Renovate manages all of `azure/requirements.txt` — no
    `renovate.json` changes.** The pip manager picks the file up with its
    default match, so `azure-functions` and `azure-identity` get normal
    updates, and the `docxwire` `git+…@tag` pin is tracked via the
    `git-tags` datasource — no exclusion, no special-casing.

## Risks / Trade-offs

- **Bundled pandoc binary bloats the deployment package** (~40 MB wheel)
  → verify the zipped package size in CI; if it approaches the plan's zip
  limit, switch the action to `remote-build: true` (Oryx) — a one-line
  workflow change.
- **Tenant consent is a human gate** (admin consent for `Files.Read.All`,
  site permission grant) → covered by the Azure-side setup guide; the
  function fails with a clear Graph error until it is done.
- **Re-triggered file creates a duplicate draft** (accepted decision) → the
  response includes the created article id/title so the automation (and logs)
  show what was created; duplicates are visible drafts the club can trash.
- **CLI output contract drift** (the function parses the CLI's `--json`
  output) → the JSON shape is a spec-level requirement of the `cli`
  capability (prerequisite change `cli-automation-interface`), and the
  function's tests pin the shape.
- **Secrets in logs** → the handler never logs the request body beyond the
  item reference, and error responses strip credentials; the API key is
  compared in constant time and never echoed.
- **Cold starts** (pandoc + dependency load) → acceptable for occasional
  article approvals; Flex Consumption's dynamic scale-out suits the load
  profile.

## Migration Plan

1. Operator performs the Azure-side setup per `azure/README.md`
   (placeholders only; the mechanics of identities, consent, and GitHub
   secrets are in the official GitHub/Azure documentation, which the guide
   links to). The setup is independent of the repository, so it happens
   while the change's PR is open.
2. Merge the repo-side change (code, tests, workflow, docs; the pin carries
   the then-current release) — the merge is an `azure/**` change, so it
   triggers the first deployment.
3. End-to-end test: approve a throwaway article in SharePoint; verify the
   draft appears in Joomla.
4. Point the Power Automate flow at the endpoint.

Rollback: disable the Power Automate flow (stops all traffic); the function
and pipeline are inert. Reverting the repo change only removes the
`azure/` directory and workflow; the deployed app keeps its last code.

## References

External documentation the project docs link to (setup mechanics are not
reproduced in the repo):

- Deploy to Azure Functions with GitHub Actions (OIDC +
  `Azure/functions-action`):
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-github-actions>
- Using OpenID Connect in GitHub Actions:
  <https://docs.github.com/en/actions/security-guides/using-openid-connect-in-actions>
- `Azure/functions-action` (parameters incl. `remote-build`):
  <https://github.com/Azure/functions-action>
- Python function apps (local `pip install --target` packaging):
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python>
- Supported Python runtimes (3.11–3.14 on Flex Consumption; 3.12 is the
  maximum for classic Consumption):
  <https://learn.microsoft.com/en-us/azure/azure-functions/supported-languages>
- Continuous deployment for Functions (Flex Consumption: package
  deployment, no slots, GitHub Actions with OIDC):
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-continuous-deployment>
- Graph: download driveItem content (302 to preauthenticated URL):
  <https://learn.microsoft.com/en-us/graph/api/driveitem-get-content>
- Graph application permissions (`Files.Read.All`):
  <https://learn.microsoft.com/en-us/graph/permissions-reference>
- Function app configuration (application settings as environment
  variables):
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-config>
- GitHub Actions secrets (encryption):
  <https://docs.github.com/en/actions/security-guides/encryption>
- Renovate pip manager (tracks `git+…@tag` pins via the `git-tags`
  datasource):
  <https://docs.renovatebot.com/modules/manager/pip_requirements>

## Open Questions

- Exact tenant values (function app name, resource group, SharePoint
  site/list ids, `PUBLISH_API_KEY` value) — supplied by the operator at
  setup time; the docs carry placeholders.
- Whether the club reuses an existing Entra app registration for SharePoint
  access or creates a dedicated one — operator choice, documented either way.
