# n26-mcp

[![CI](https://github.com/regressEdo/n26-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/regressEdo/n26-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

MCP server for N26 bank — read-only access via the unofficial N26 web API.

> **Warning:** Uses reverse-engineered internal API (`api.tech26.de` and `app.n26.com`). No official support. May break on N26 API changes.

---

## Quickstart

### 1. Configure credentials

Copy the example env file and fill in your N26 credentials:

```bash
cp .env.example .env
```

**Option A — Plain credentials** (simplest):

```ini
# .env
N26_USERNAME=your.email@example.com
N26_PASSWORD=your-n26-password
```

**Option B — 1Password CLI** (recommended):

```ini
# .env  (or a dedicated env file, e.g. ~/.config/op/local-env.env)
N26_USERNAME=op://YourVault/YourItem/N26_USERNAME
N26_PASSWORD=op://YourVault/YourItem/N26_PASSWORD
```

Set `OP_ENV_FILE` to point at your 1Password env file (default: `~/.config/op/local-env.env`):

```bash
make register OP_ENV_FILE=~/.config/op/my-env.env
```

### 2. Install and verify

```bash
make setup
```

Installs dependencies (`uv sync`) and checks that your credentials are accessible.

### 3. Register with Claude Code

```bash
make register
```

Auto-detects whether you're using 1Password or plain credentials and runs the right `claude mcp add` command. Restart Claude Code afterwards.

### 4. Authenticate via Claude Code

```
login()                    # triggers N26 MFA (push notification to N26 app)
submit_mfa()               # poll for push approval (approve in app first)
```

Or use SMS instead of push:

```
login()
request_sms_code()         # sends SMS to your phone
submit_mfa(otp="123456")   # enter the SMS code
```

Session tokens are cached at `~/.config/n26-mcp/session.json` (chmod 600) and valid for ~14 minutes. Re-run `login()` + `submit_mfa()` when expired.

---

## Make targets

| Target | Description |
|--------|-------------|
| `make setup` | Install deps + verify credential access |
| `make register` | Register MCP server with Claude Code |
| `make run` | Start MCP server over stdio |
| `make dev` | Start with interactive inspector UI |
| `make status` | Check whether a session is cached |
| `make logout` | Delete cached session |
| `make test` | Run test suite |
| `make clean` | Remove build artifacts |
| `make help` | List all targets |

---

## Available tools

| Tool | Description |
|------|-------------|
| `login` | Start auth — triggers N26 MFA push notification |
| `request_sms_code` | Request SMS OTP instead of app push |
| `submit_mfa` | Complete MFA (`otp=` for SMS; no args polls push) |
| `logout` | Clear local session |
| `auth_status` | Check session state and time until expiry |
| `get_profile` | User profile info |
| `get_account` | Balance and IBAN |
| `get_transactions` | Transaction list (supports date range filters) |
| `get_transaction` | Single transaction by ID |
| `get_spaces` | Savings Spaces with balances |
| `get_cards` | Card details |

---

## Security notes

- Credentials read from environment only — never stored, never sent to Claude
- `.env` is in `.gitignore` — never commit it
- Session file at `~/.config/n26-mcp/session.json` contains the access token (valid ~14 min)
- Read-only: no payment or write operations are exposed
