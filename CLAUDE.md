# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make setup       # install deps (uv sync) + verify credential access
make register    # register MCP server with Claude Code (auto-detects op vs plain .env)
make dev         # run server with interactive inspector UI
make test        # run test suite (uv run pytest)
make status      # check for cached session
make logout      # delete session file (~/.config/n26-mcp/session.json)
make help        # list all targets
```

Underlying commands if needed directly:

```bash
uv sync
uv run pytest
uv run mcp dev src/n26_mcp/server.py
uv run n26-mcp
```

## Running with Headroom

This repo is used alongside the [Headroom](https://github.com/chopratejas/headroom) Claude Code plugin, which adds cross-agent memory and a code graph to every Claude session.

**With Headroom installed**, the `claude` shell function wraps all invocations:

```bash
HEADROOM_REQUIRE_RUST_CORE=false headroom wrap claude --memory --code-graph --learn
```

**Important:** `op run` cannot wrap interactive TUI apps (breaks stdin/TTY). The `mcp add` registration command must bypass the `claude` alias and call the real binary directly:

```bash
/usr/bin/claude mcp add n26 --scope user -- op run --env-file ~/.config/op/local-env.env -- uv --directory /path/to/n26-mcp run n26-mcp
```

**Without Headroom**, use `claude` normally:

```bash
claude mcp add n26 --scope user -- op run --env-file ~/.config/op/local-env.env -- uv --directory /path/to/n26-mcp run n26-mcp
```

Or if using plain `.env` credentials (no 1Password):

```bash
claude mcp add n26 --scope user -- uv --directory /path/to/n26-mcp run n26-mcp
```

## Architecture

Three modules in `src/n26_mcp/`:

**`server.py`** — MCP entry point. Registers all tools via `FastMCP`. Calls `load_dotenv()` at import time so a `.env` file in the repo root is picked up automatically. The single `N26Client` instance is module-level.

**`auth.py`** — Web session auth against `app.n26.com`. N26 deprecated the OAuth2 password grant; the current flow uses form-encoded GraphQL mutations on the web login page:

1. `start_login()` — GET `app.n26.com/login` → extract CSRF token → POST `requestBiometricChallenge` mutation → N26 sets `n26.mfa_token` cookie and sends a push to the N26 app.
2. `request_sms()` — optional; POST `requestSMSChallenge` mutation to trigger SMS instead.
3. `complete_login(otp)` — POST `verifyLoginWithSMS` (with OTP) or `verifyLoginWithPush` (polls push). On success N26 sets `n26.token=s:UUID.HMAC` and `num26expires_at`.

The UUID extracted from `n26.token` is the actual Bearer token used against `api.tech26.de`. Session state (all cookies, extracted token, expiry) is persisted to `~/.config/n26-mcp/session.json` (chmod 600). Token TTL is ~14 minutes; no working refresh endpoint exists — re-auth required when expired.

**`client.py`** — Async REST client for `api.tech26.de`. All methods call `_get()` which reads the token from `session.json` via `get_access_token()` (sync) and sends `Authorization: Bearer <uuid>`.

## Key constraints

- `follow_redirects=False` is intentional in auth flows — N26 encodes success/failure in redirect destinations and cookies, not response bodies.
- CSRF tokens expire per-request. Each POST is preceded by a GET to fetch a fresh token from the HTML form on `app.n26.com/login`.
- `is_authenticated()` only checks file existence, not expiry. Use `auth_status()` (checks `expires_at_ms`) for real session state.
