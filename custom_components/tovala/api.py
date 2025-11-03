# custom_components/tovala/api.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence
from aiohttp import ClientSession, ClientError
import time

# Prefer beta, fall back to prod if needed
DEFAULT_BASES: Sequence[str] = (
    "https://api.beta.tovala.com",
    "https://api.tovala.com",
)

LOGIN_PATH = "/v0/getToken"

class TovalaAuthError(Exception):
    """Authentication failed (bad credentials or denied)."""

class TovalaApiError(Exception):
    """Other API/HTTP failures."""

class TovalaClient:
    def __init__(
        self,
        session: ClientSession,
        email: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        api_bases: Optional[Sequence[str]] = None,
    ):
        self._session = session
        self._email = email
        self._password = password
        self._token = token
        self._token_exp = 0
        self._bases: Sequence[str] = api_bases or DEFAULT_BASES
        self._base: Optional[str] = None  # set on successful login

    @property
    def base_url(self) -> Optional[str]:
        return self._base

    async def login(self) -> None:
        """Ensure we have a valid bearer token. Tries beta then prod."""
        if self._token and self._token_exp > time.time() + 60:
            return
        if not (self._token or (self._email and self._password)):
            raise TovalaAuthError("Missing credentials")

        # If we already have a token but exp unknown, assume 1 hour left
        if self._token and not self._token_exp:
            self._token_exp = int(time.time()) + 3600
            return

        if self._token:
            # Token supplied by options: we don't yet know the right base.
            # Pick the first base so subsequent GETs have a host; callers can override via api_bases.
            self._base = self._bases[0]
            return

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-Tovala/0.1",
        }

        last_err: Optional[Exception] = None
        for base in self._bases:
            url = f"{base}{LOGIN_PATH}"
            try:
                async with self._session.post(
                    url,
                    headers=headers,
                    json={"email": self._email, "password": self._password, "type": "user"},
                ) as r:
                    txt = await r.text()
                    if r.status in (401, 403):
                        # Stop immediately on explicit auth failure
                        raise TovalaAuthError(f"Invalid auth (HTTP {r.status}): {txt}")
                    if r.status >= 400:
                        last_err = TovalaApiError(f"Login failed (HTTP {r.status}): {txt}")
                        continue
                    data = await r.json()

                token = data.get("token") or data.get("accessToken") or data.get("jwt")
                if not token:
                    last_err = TovalaAuthError("No token returned from getToken")
                    continue

                self._token = token
                self._token_exp = int(time.time()) + int(data.get("expiresIn", 3600))
                self._base = base
                return
            except TovalaAuthError:
                # Do not try other bases if credentials are wrong
                raise
            except (ClientError, Exception) as e:
                last_err = e
                # Try next base

        # If we reach here, all bases failed
        if isinstance(last_err, Exception):
            raise TovalaApiError(str(last_err))
        raise TovalaApiError("Login failed")

    async def _auth_headers(self) -> Dict[str, str]:
        await self.login()
        return {"Authorization": f"Bearer {self._token}"}

    async def _get_json(self, path: str, **fmt) -> Any:
        if not self._base:
            # Ensure login determined the base URL
            await self.login()
        assert self._base, "Base URL not set after login"
        headers = await self._auth_headers()
        url = f"{self._base}{path.format(**fmt)}"
        async with self._session.get(url, headers=headers) as r:
            txt = await r.text()
            if r.status == 404:
                raise TovalaApiError("not_found")
            if r.status >= 400:
                raise TovalaApiError(f"HTTP {r.status}: {txt}")
            try:
                return await r.json()
            except Exception:
                # Some endpoints may return empty body
                return {}

    # ---- Stubs until we confirm the read endpoints from the app traffic ----
    # Candidates observed/typical in v0 APIs; we probe until one works.
    OVENS_LIST_CANDIDATES: Sequence[str] = (
        "/v0/ovens",           # returns [{id,name,...}]
        "/v0/devices/ovens",   # alt naming
        "/v0/user/ovens",      # user-scoped
    )
    OVEN_STATUS_CANDIDATES: Sequence[str] = (
        "/v0/ovens/{oven_id}/status",
        "/v0/ovens/{oven_id}",           # sometimes status is in the base object
        "/v0/devices/ovens/{oven_id}/status",
    )

    async def list_ovens(self) -> List[Dict[str, Any]]:
        """Try a few candidate endpoints to find user's ovens."""
        for path in self.OVENS_LIST_CANDIDATES:
            try:
                data = await self._get_json(path)
                if isinstance(data, dict) and "ovens" in data:
                    data = data["ovens"]
                if isinstance(data, list):
                    return data
            except TovalaApiError as e:
                if str(e) == "not_found":
                    continue
                # try next candidate on other errors too
                continue
            except Exception:
                continue
        raise TovalaApiError("Could not find an ovens endpoint in v0 API")

    async def oven_status(self, oven_id: str) -> Dict[str, Any]:
        """Try a few candidate endpoints to fetch oven status."""
        for path in self.OVEN_STATUS_CANDIDATES:
            try:
                data = await self._get_json(path, oven_id=oven_id)
                return data
            except TovalaApiError as e:
                if str(e) == "not_found":
                    continue
                continue
            except Exception:
                continue
        raise TovalaApiError("Could not read oven status from any known endpoint")