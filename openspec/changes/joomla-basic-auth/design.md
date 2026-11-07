# Design

## Context

The Joomla client already handles one transport-level credential: in `JoomlaClient.__init__`
it sets `X-Joomla-Token` and `Accept` once on a shared `requests.Session`, and every request
inherits them. The settings arrive as a frozen `JoomlaSettings` dataclass loaded from the
`[joomla]` TOML section. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Let a target sit behind an HTTP Basic Auth gate, configured per-target and off by default.
- Keep the change minimal and backward compatible: no existing `settings.toml` changes behavior.
- Compose cleanly with the existing `X-Joomla-Token` (independent header, no conflict).

**Non-Goals:**
- No client-side credential handling beyond a single opaque value (no username/password
  fields, no keyring/env-var secret management).
- No change to how a 401 from the gate is surfaced beyond what the client already does.

## Decisions

- **Single opaque `basic_auth` value, sent verbatim.** The config takes one string and the
  client emits `Authorization: Basic <value>` with the value unchanged.
  - *Why:* the observed real-world case (a staging/reverse-proxy gate) uses an opaque shared
    secret, not a `user:pass` pair. A verbatim value is strictly more general — it covers the
    opaque case exactly, and a classical `user:pass` gate can be served by putting the
    pre-encoded base64 string in the same field.
  - *Alternatives:* (a) `basic_auth_user` + `basic_auth_password` with client-side base64 —
    rejected, it cannot represent an opaque token and is less general; (b) support both —
    rejected, more settings surface, validation, and test area for no observed need.

- **Set the `Authorization` header directly, not via `requests`' `auth=` parameter.**
  - *Why:* `requests`' built-in Basic auth base64-encodes a `user:pass` tuple and re-negotiates
    on a `401`/`WWW-Authenticate` challenge. Neither is wanted for a pre-known opaque token.
    Writing the header onto the session is deterministic and reuses the exact mechanism the
    client already uses for `X-Joomla-Token`, so all CRUD methods pick it up with no other
    changes.

- **The value lives in the `[joomla]` section and is optional.** It protects the Joomla target
  (the `base_url`), so it is per-target like the other keys. `JoomlaSettings.basic_auth`
  defaults to `None` (unset); the loader reads it with `joomla_data.get("basic_auth")` and
  type-checks it as a string only when present. When unset, no `Authorization` header is sent.

- **The example file explains how to obtain the value.** `settings.toml.example` documents
  `basic_auth` with a placeholder and a short note: for a classical gate, base64-encode
  `username:password` and put the result in `basic_auth`. This keeps the client minimal while
  making the self-serve path obvious.

## Risks / Trade-offs

- [A classical `user:pass` gate user must pre-encode the pair] → the example-file note shows
  the exact base64 step; accepted to keep the config a single field and the client simple.
- [A bad/missing Basic token surfaces as a generic 401] → the gate's 401 (typically an HTML
  challenge page, not the Joomla JSON envelope) already becomes `JoomlaApiError(401, [],
  raw=…)`. Acceptable; a friendlier "check `basic_auth`" hint is a possible follow-up, out of
  scope here.
- [`basic_auth` is another secret in `settings.toml`] → that file is already gitignored, so the
  new key adds no new exposure path.

## Migration Plan

None required — the key is optional and additive. Deploy by merging; existing targets are
unaffected. To use it, add `basic_auth = "…"` to a target's `settings.toml`. Rollback is
removing the key (reverts to no `Authorization` header).
