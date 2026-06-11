from typing import Any, Optional

import httpx

from .auth import get_access_token

BASE_URL = "https://api.tech26.de"


class N26Client:
    def __init__(self) -> None:
        self._http = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

    async def _get(self, path: str, params: Optional[dict] = None) -> Any:
        token = get_access_token()
        if not token:
            raise RuntimeError("Not authenticated. Call login first.")

        resp = await self._http.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )

        if resp.status_code == 401:
            raise RuntimeError("Session expired (token valid ~14 min). Call login again.")

        resp.raise_for_status()
        return resp.json()

    async def get_me(self) -> dict:
        return await self._get("/api/me")

    async def get_account(self) -> dict:
        return await self._get("/api/accounts")

    async def get_transactions(
        self,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        limit: int = 50,
        last_id: Optional[str] = None,
    ) -> list:
        params: dict = {"limit": min(limit, 200)}
        if from_ts is not None:
            params["from"] = from_ts
        if to_ts is not None:
            params["to"] = to_ts
        if last_id is not None:
            params["lastId"] = last_id
        return await self._get("/api/smrt/transactions", params=params)

    async def get_transaction(self, transaction_id: str) -> dict:
        return await self._get(f"/api/transactions/{transaction_id}")

    async def get_spaces(self) -> dict:
        return await self._get("/api/v2/spaces")

    async def get_cards(self) -> list:
        return await self._get("/api/v1/cards")

    async def close(self) -> None:
        await self._http.aclose()
