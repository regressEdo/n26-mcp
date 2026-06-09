# n26-mcp

MCP server for N26 bank — read-only access via the unofficial N26 API.

> **Warning:** Uses reverse-engineered internal API (`api.tech26.de`). No official support. May break on N26 API changes.

## Setup

```bash
uv sync
```

## Claude Code config

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "n26": {
      "command": "uv",
      "args": ["--directory", "/path/to/n26-mcp", "run", "n26-mcp"]
    }
  }
}
```

## Usage

1. Call `login(username, password)` — N26 sends OTP to your phone/SMS
2. Call `submit_mfa(otp)` — completes auth, tokens stored at `~/.config/n26-mcp/`
3. Use any read-only tool: `get_account`, `get_transactions`, `get_spaces`, etc.

Tokens refresh automatically. Refresh token valid ~180 days.

## Available tools

| Tool | Description |
|------|-------------|
| `login` | Start auth with email + password |
| `submit_mfa` | Complete MFA with OTP |
| `auth_status` | Check if session is active |
| `get_profile` | User profile info |
| `get_account` | Balance and IBAN |
| `get_transactions` | Transaction list (supports date filters) |
| `get_transaction` | Single transaction by ID |
| `get_spaces` | Savings Spaces with balances |
| `get_cards` | Card details |

## Security notes

- Credentials are never stored — only OAuth tokens in `~/.config/n26-mcp/`
- Device token is persisted to avoid re-pairing on every run
- This is read-only: no payment or write operations
