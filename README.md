# n26-mcp

MCP server for N26 bank — read-only access via the unofficial N26 API.

> **Warning:** Uses reverse-engineered internal API (`api.tech26.de`). No official support. May break on N26 API changes.

## Quickstart

### Prerequisites

- [1Password CLI](https://developer.1password.com/docs/cli/) installed and vault unlocked
- `uv` installed
- `N26_USERNAME` and `N26_PASSWORD` fields present in your 1Password vault (see [Auth](#auth))

### 1. Install dependencies

```bash
make setup
```

This installs Python deps and verifies the 1Password fields are reachable.

### 2. Register the MCP server with Claude Code

```bash
claude mcp add n26 --scope user -- uv --directory /home/edo/OneDrive/Documenti/local/gitrepo/personal/n26-mcp run n26-mcp
```

### 3. Reload your shell, then authenticate via Claude

Open Claude Code and run:

```
login()         # reads credentials from 1Password, triggers N26 MFA
submit_mfa("123456")  # enter the OTP from your N26 app or SMS
```

Done — tokens are cached, future sessions auto-refresh for ~180 days.

---

## Auth

**Credentials are never typed into Claude or stored in files.** The server reads
`N26_USERNAME` and `N26_PASSWORD` exclusively from environment variables injected
by the 1Password CLI at shell startup via `op-env-load`.

The secret references live in `~/.config/op/local-env.env`:

```
N26_PASSWORD="op://Local Environment/ENV/N26_PASSWORD"
N26_USERNAME="op://Local Environment/ENV/N26_USERNAME"
```

To set them up, add `N26_USERNAME` and `N26_PASSWORD` fields to the
**`ENV`** item in your **`Local Environment`** 1Password vault, then run
`op-env-load` (or open a new shell).

---

## Make targets

| Target | Description |
|--------|-------------|
| `make setup` | Install deps + verify 1Password fields exist |
| `make run` | Start MCP server over stdio (production mode) |
| `make dev` | Start MCP server with interactive inspector UI |
| `make status` | Check whether OAuth tokens are present |
| `make logout` | Delete cached tokens (forces re-auth next session) |
| `make test` | Run test suite |
| `make clean` | Remove build artifacts and `__pycache__` |

---

## Available tools

| Tool | Description |
|------|-------------|
| `login` | Start auth — reads credentials from 1Password |
| `submit_mfa` | Complete MFA with OTP from N26 app or SMS |
| `auth_status` | Check if session is active |
| `get_profile` | User profile info |
| `get_account` | Balance and IBAN |
| `get_transactions` | Transaction list (supports date filters) |
| `get_transaction` | Single transaction by ID |
| `get_spaces` | Savings Spaces with balances |
| `get_cards` | Card details |

---

## Security notes

- Credentials injected by 1Password CLI — never stored in plaintext, never sent to Claude
- OAuth tokens stored at `~/.config/n26-mcp/tokens.json` (chmod 600)
- Device token persisted to avoid re-pairing on every run
- Read-only: no payment or write operations exposed
