import json
import os
import re
import uuid
from pathlib import Path
from typing import Optional

import httpx

LOGIN_URL = "https://app.n26.com/login"
GRAPHQL_URL = "https://app.n26.com/graphql"
CONFIG_DIR = Path.home() / ".config" / "n26-mcp"
SESSION_FILE = CONFIG_DIR / "session.json"

_BIOMETRIC_MUTATION = (
    "mutation requestBiometricChallengeMutation("
    "$username:String! $password:String! $fp:String $fpc:String $requestId:String"
    "){requestBiometricChallenge("
    "username:$username password:$password fp:$fp fpc:$fpc requestId:$requestId"
    "){status shouldDelay challengeId challengeType challengeStep "
    "challengeData{obfuscatedPhoneNumber remainingResendCodeCount waitingTimeInSeconds}"
    "errors{translationKey message field userMessage{title detail}}redirectUrl}}"
)

_SMS_MUTATION = (
    "mutation requestSMSChallengeMutation{requestSMSChallenge{"
    "status errors{translationKey message field}shouldAbortLoginAttempt "
    "challengeType challengeData{obfuscatedPhoneNumber remainingResendCodeCount "
    "waitingTimeInSeconds}}}"
)

_VERIFY_SMS_MUTATION = (
    "mutation verifyLoginWithSMSMutation($verificationCode:String!)"
    "{verifyLoginWithSMS(verificationCode:$verificationCode){"
    "status errors{translationKey message field}"
    "attemptLimitExceeded shouldAbortLoginAttempt challengeType}}"
)

_VERIFY_PUSH_MUTATION = (
    "mutation verifyLoginWithPushMutation{verifyLoginWithPush{"
    "status errors{translationKey message field}"
    "isAuthorizationPending shouldAbortLoginAttempt "
    "challengeType rateLimit{limit current}}}"
)


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


def _extract_csrf_token(html: str) -> str:
    m = re.search(r'name="_csrf" value="([^"]+)"', html)
    if not m:
        raise RuntimeError("Could not extract CSRF token from login page")
    return m.group(1)


def _cookie_header(cookies: dict) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def _parse_set_cookies(response_headers: httpx.Headers) -> dict:
    result = {}
    for header in response_headers.get_list("set-cookie"):
        part = header.split(";")[0].strip()
        if "=" in part:
            name, _, value = part.partition("=")
            result[name.strip()] = value.strip()
    return result


def _extract_uuid_from_signed_cookie(value: str) -> Optional[str]:
    """Extract UUID from Express.js signed cookie: s:UUID.HMAC or s:UUID"""
    if not value:
        return None
    raw = value
    if raw.startswith("s%3A"):
        raw = raw[4:]  # URL-decode s:
    elif raw.startswith("s:"):
        raw = raw[2:]
    uuid_part = raw.split(".")[0]
    try:
        return str(uuid.UUID(uuid_part))
    except ValueError:
        return None


def _extract_timestamp_from_signed_cookie(value: str) -> Optional[int]:
    """Extract integer timestamp from Express.js signed cookie."""
    if not value:
        return None
    raw = value
    if raw.startswith("s%3A"):
        raw = raw[4:]
    elif raw.startswith("s:"):
        raw = raw[2:]
    ts_part = raw.split(".")[0]
    try:
        return int(ts_part)
    except (ValueError, TypeError):
        return None


def is_authenticated() -> bool:
    return SESSION_FILE.exists()


def load_session() -> Optional[dict]:
    if SESSION_FILE.exists():
        return json.loads(SESSION_FILE.read_text())
    return None


def save_session(state: dict) -> None:
    _ensure_config_dir()
    SESSION_FILE.write_text(json.dumps(state))
    SESSION_FILE.chmod(0o600)


def clear_session() -> None:
    SESSION_FILE.unlink(missing_ok=True)


def get_access_token() -> Optional[str]:
    state = load_session()
    if not state or not state.get("authenticated"):
        return None
    return state.get("access_token")


def get_token_expiry_ms() -> Optional[int]:
    state = load_session()
    if not state:
        return None
    return state.get("expires_at_ms")


async def start_login() -> dict:
    username, password = _get_credentials()

    async with httpx.AsyncClient(follow_redirects=False) as client:
        resp = await client.get(LOGIN_URL)
        cookies: dict = _parse_set_cookies(resp.headers)
        csrf_token = _extract_csrf_token(resp.text)

        resp2 = await client.post(
            GRAPHQL_URL,
            data={
                "_csrf": csrf_token,
                "__mutation": _BIOMETRIC_MUTATION,
                "__successRedirect": "/login?verifyLogin=1",
                "__failureRedirect": "/login?verifyLogin=1",
                "username": username,
                "password": password,
            },
            headers={"Cookie": _cookie_header(cookies)},
        )
        cookies.update(_parse_set_cookies(resp2.headers))

    if "n26.mfa_token" not in cookies:
        return {"status": "error", "detail": "Login failed — bad credentials or account locked"}

    save_session({"cookies": cookies, "authenticated": False})
    return {
        "status": "mfa_required",
        "message": (
            "Push notification sent to N26 app. Approve it then call submit_mfa(), "
            "or call request_sms() to receive an SMS code instead."
        ),
    }


async def request_sms() -> dict:
    state = load_session()
    if not state:
        return {"status": "error", "message": "No active login session. Call login first."}

    cookies = state["cookies"]

    async with httpx.AsyncClient(follow_redirects=False) as client:
        resp = await client.get(
            f"{LOGIN_URL}?verifyLogin=1",
            headers={"Cookie": _cookie_header(cookies)},
        )
        cookies.update(_parse_set_cookies(resp.headers))
        csrf_token = _extract_csrf_token(resp.text)

        resp2 = await client.post(
            GRAPHQL_URL,
            data={
                "_csrf": csrf_token,
                "__mutation": _SMS_MUTATION,
                "__successRedirect": "/login?verifyLogin=1",
                "__failureRedirect": "/login?verifyLogin=1",
            },
            headers={"Cookie": _cookie_header(cookies)},
        )
        cookies.update(_parse_set_cookies(resp2.headers))

    state["cookies"] = cookies
    save_session(state)

    redirect = resp2.headers.get("location", "")
    if "error" in redirect.lower() or "failure" in redirect.lower():
        return {"status": "error", "detail": "SMS request failed"}

    return {"status": "sms_sent", "message": "SMS code sent to your phone. Call submit_mfa(otp=<code>)."}


async def complete_login(otp: Optional[str] = None) -> dict:
    state = load_session()
    if not state:
        return {"status": "error", "message": "No active login session. Call login first."}

    cookies = state["cookies"]

    async with httpx.AsyncClient(follow_redirects=False) as client:
        resp = await client.get(
            f"{LOGIN_URL}?verifyLogin=1",
            headers={"Cookie": _cookie_header(cookies)},
        )
        cookies.update(_parse_set_cookies(resp.headers))
        csrf_token = _extract_csrf_token(resp.text)

        if otp:
            mutation = _VERIFY_SMS_MUTATION
            extra = {"verificationCode": otp}
        else:
            mutation = _VERIFY_PUSH_MUTATION
            extra = {}

        resp2 = await client.post(
            GRAPHQL_URL,
            data={
                "_csrf": csrf_token,
                "__mutation": mutation,
                "__successRedirect": "/login?verifyLogin=1",
                "__failureRedirect": "/login?verifyLogin=1",
                **extra,
            },
            headers={"Cookie": _cookie_header(cookies)},
        )
        cookies.update(_parse_set_cookies(resp2.headers))

    redirect = resp2.headers.get("location", "")
    if "error" in redirect.lower() or "failure" in redirect.lower():
        return {"status": "error", "detail": "MFA verification failed"}

    if otp is None:
        # Push: check if still pending (need to poll)
        state["cookies"] = cookies
        save_session(state)
        return {
            "status": "pending",
            "message": "Waiting for push approval. Approve in N26 app then call submit_mfa() again.",
        }

    access_token = _extract_uuid_from_signed_cookie(cookies.get("n26.token", ""))
    expires_at = _extract_timestamp_from_signed_cookie(cookies.get("num26expires_at", ""))

    if not access_token:
        return {"status": "error", "detail": "Login succeeded but could not extract access token"}

    state["cookies"] = cookies
    state["access_token"] = access_token
    state["expires_at_ms"] = expires_at
    state["authenticated"] = True
    save_session(state)
    return {"status": "authenticated"}
