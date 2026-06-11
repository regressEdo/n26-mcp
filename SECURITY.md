# Security Policy

## Scope

This project uses reverse-engineered internal N26 APIs. It is a **read-only** local tool — no payment or write operations are exposed, and no credentials are transmitted to third parties.

## Credential handling

- Credentials are read from environment variables or `.env` only
- `.env` is in `.gitignore` — never commit it
- Session tokens are stored at `~/.config/n26-mcp/session.json` (chmod 600), valid ~14 minutes
- The MCP server runs locally; credentials and tokens never leave your machine

## Reporting a vulnerability

If you find a security issue (e.g. credential leak, path traversal, token exposure), open a **private** GitHub Security Advisory:

> **GitHub → Security → Report a vulnerability**

Please do not open a public issue for security bugs.

## Disclaimer

This tool uses unofficial, reverse-engineered APIs. It may break at any time following N26 API changes. Use at your own risk. The author is not affiliated with N26.
