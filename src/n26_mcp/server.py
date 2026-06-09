from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .auth import complete_login, is_authenticated, start_login
from .client import N26Client

mcp = FastMCP("N26 Bank (read-only)")
_client = N26Client()


def _iso_to_ms(date_str: str) -> int:
    return int(datetime.fromisoformat(date_str).timestamp() * 1000)


@mcp.tool()
async def login() -> dict:
    """
    Start N26 login using credentials from the .env file.
    N26 requires MFA — you will receive an OTP via the N26 app or SMS.
    Call submit_mfa with that OTP to complete login.
    """
    return await start_login()


@mcp.tool()
async def submit_mfa(otp: str) -> dict:
    """
    Complete N26 MFA login with the OTP from the N26 app or SMS.
    Call this after login returns status='mfa_required'.
    """
    return await complete_login(otp)


@mcp.tool()
async def auth_status() -> dict:
    """Check whether the MCP server currently has a valid N26 session."""
    return {"authenticated": is_authenticated()}


@mcp.tool()
async def get_profile() -> dict:
    """Get N26 user profile (name, email, nationality, etc.)."""
    return await _client.get_me()


@mcp.tool()
async def get_account() -> dict:
    """Get N26 account details including available balance and IBAN."""
    return await _client.get_account()


@mcp.tool()
async def get_transactions(
    limit: int = 50,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list:
    """
    Get N26 transactions.

    Args:
        limit: Max number of transactions to return (1-200, default 50).
        from_date: Filter start date in ISO format (YYYY-MM-DD), optional.
        to_date: Filter end date in ISO format (YYYY-MM-DD), optional.
    """
    return await _client.get_transactions(
        from_ts=_iso_to_ms(from_date) if from_date else None,
        to_ts=_iso_to_ms(to_date) if to_date else None,
        limit=limit,
    )


@mcp.tool()
async def get_transaction(transaction_id: str) -> dict:
    """Get full details of a single N26 transaction by its ID."""
    return await _client.get_transaction(transaction_id)


@mcp.tool()
async def get_spaces() -> dict:
    """Get N26 Spaces (savings sub-accounts) with names and balances."""
    return await _client.get_spaces()


@mcp.tool()
async def get_cards() -> list:
    """Get N26 card details (type, status, masked PAN)."""
    return await _client.get_cards()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
