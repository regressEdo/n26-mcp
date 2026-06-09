import json
import os
import uuid
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel

AUTH_URL = "https://api.tech26.de/oauth2/token"
BASIC_AUTH = ("android", "secret")
CONFIG_DIR = Path.home() / ".config" / "n26-mcp"
TOKEN_FILE = CONFIG_DIR / "tokens.json"
DEVICE_FILE = CONFIG_DIR / "device.json"
MFA_FILE = CONFIG_DIR / "mfa_state.json"


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 0


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _get_credentials() -> tuple[str, str]:
    username = os.getenv("N26_USERNAME")
    password = os.getenv("N26_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "N26_USERNAME and N26_PASSWORD must be set in 1Password "
            "(op://Local Environment/ENV/N26_USERNAME)"
        )
    return username, password


def load_device_token() -> str:
    if DEVICE_FILE.exists():
        return json.loads(DEVICE_FILE.read_text())["device_token"]
    _ensure_config_dir()
    token = str(uuid.uuid4())
    DEVICE_FILE.write_text(json.dumps({"device_token": token}))
    return token


def load_tokens() -> Optional[TokenData]:
    if TOKEN_FILE.exists():
        return TokenData(**json.loads(TOKEN_FILE.read_text()))
    return None


def save_tokens(tokens: TokenData) -> None:
    _ensure_config_dir()
    TOKEN_FILE.write_text(tokens.model_dump_json())
    TOKEN_FILE.chmod(0o600)


def is_authenticated() -> bool:
    return TOKEN_FILE.exists()


async def start_login() -> dict:
    """Read credentials from .env and start OAuth2 password grant flow."""
    username, password = _get_credentials()
    device_token = load_device_token()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            AUTH_URL,
            data={
                "username": username,
                "password": password,
                "grant_type": "password",
            },
            auth=BASIC_AUTH,
            headers={"device-token": device_token},
        )

    if resp.status_code == 200:
        save_tokens(TokenData(**resp.json()))
        return {"status": "authenticated"}

    if resp.status_code == 403:
        body = resp.json()
        if body.get("error") == "mfa_required":
            _ensure_config_dir()
            MFA_FILE.write_text(json.dumps({
                "mfa_token": body["mfaToken"],
                "device_token": device_token,
            }))
            MFA_FILE.chmod(0o600)
            return {
                "status": "mfa_required",
                "message": "Check your N26 app or SMS for OTP, then call submit_mfa.",
            }

    return {"status": "error", "detail": resp.text}


async def complete_login(otp: str) -> dict:
    """Submit OTP received from N26 app or SMS to complete authentication."""
    if not MFA_FILE.exists():
        return {"status": "error", "message": "No pending MFA. Call login first."}

    state = json.loads(MFA_FILE.read_text())

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            AUTH_URL,
            data={
                "mfaToken": state["mfa_token"],
                "otp": otp,
                "grant_type": "mfa_otp",
            },
            auth=BASIC_AUTH,
            headers={"device-token": state["device_token"]},
        )

    if resp.status_code != 200:
        return {"status": "error", "detail": resp.text}

    save_tokens(TokenData(**resp.json()))
    MFA_FILE.unlink(missing_ok=True)
    return {"status": "authenticated"}


async def refresh_access_token() -> Optional[str]:
    tokens = load_tokens()
    if not tokens:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            AUTH_URL,
            data={
                "refresh_token": tokens.refresh_token,
                "grant_type": "refresh_token",
            },
            auth=BASIC_AUTH,
            headers={"device-token": load_device_token()},
        )

    if resp.status_code != 200:
        return None

    new_tokens = TokenData(**resp.json())
    save_tokens(new_tokens)
    return new_tokens.access_token


async def get_access_token() -> Optional[str]:
    tokens = load_tokens()
    if not tokens:
        return None
    return tokens.access_token
