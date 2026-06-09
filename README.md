# n26-mcp

MCP server for N26 bank — read-only access via the unofficial N26 web API.

> **Warning:** Uses reverse-engineered internal API (`api.tech26.de` and `app.n26.com`). No official support. May break on N26 API changes.

---

## Quickstart

### 1. Install dependencies

```bash
cd /path/to/n26-mcp
uv sync
```

### 2. Configure credentials

Copy the example env file and choose your auth method:

```bash
cp .env.example .env
```

**Option A — Plain credentials** (simplest):

```ini
# .env
N26_USERNAME=your.email@example.com
N26_PASSWORD=your-n26-password
```

The server auto-loads `.env` on startup. Done.

**Option B — 1Password CLI** (recommended for security):

```ini
# .env  (or ~/.config/op/local-env.env)
N26_USERNAME=op://Vault/Item/N26_USERNAME
N26_PASSWORD=op://Vault/Item/N26_PASSWORD
```

Wrap the server command with `op run --env-file .env --` so 1Password resolves the references before the process starts (see step 3).

### 3. Register the MCP server with Claude Code

**Plain credentials** (`.env` in repo root, auto-loaded):

```bash
claude mcp add n26 --scope user -- uv --directory /path/to/n26-mcp run n26-mcp
```

**1Password**:

```bash
claude mcp add n26 --scope user -- op run --env-file /path/to/n26-mcp/.env -- uv --directory /path/to/n26-mcp run n26-mcp
```

Replace `/path/to/n26-mcp` with the actual repo path in both commands.

### 4. Authenticate via Claude Code

```
login()                    # triggers N26 MFA (push to N26 app)
submit_mfa()               # poll for push approval (approve in app first)

# or use SMS instead of push:
login()
request_sms_code()         # sends SMS to your phone
submit_mfa(otp="123456")   # enter the SMS code
```

Session tokens are cached at `~/.config/n26-mcp/session.json` (chmod 600) and are valid for ~14 minutes. Re-run `login()` + `submit_mfa()` when the session expires.

---

## Security notes

- Credentials are read from environment only — never stored, never sent to Claude
- `.env` is in `.gitignore` — never commit it
- Session file at `~/.config/n26-mcp/session.json` contains the access token (valid ~14 min)
- Read-only: no payment or write operations are exposed

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
| `get_transactions` | Transaction list (supports date filters) |
| `get_transaction` | Single transaction by ID |
| `get_spaces` | Savings Spaces with balances |
| `get_cards` | Card details |

---

## Make targets

| Target | Description |
|--------|-------------|
| `make setup` | Install deps + verify credentials are reachable |
| `make run` | Start MCP server over stdio |
| `make dev` | Start MCP server with interactive inspector UI |
| `make status` | Check whether a session is cached |
| `make logout` | Delete cached session |
| `make test` | Run test suite |
| `make clean` | Remove build artifacts and `__pycache__` |
