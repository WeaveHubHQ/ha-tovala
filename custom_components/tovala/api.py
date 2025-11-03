from __future__ import annotations
import time
import httpx

# NOTE: These are derived from community work; adjust if Tovala changes them.
BASE = "https://my.tovala.com"
LOGIN_PATH = "/api/login"            # TODO: verify; some flows return JWT via /api/session or similar
ME_PATH = "/api/users/me"            # returns user id, ovens
STATUS_FMT = "/api/ovens/{oven_id}/status"  # TODO: verify field names
# Some gists show userId + token needed; homebridge uses JWT (jsonwebtoken); token likely short-lived.

class TovalaClient:
    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password
        self._token = None
        self._token_exp = 0
        self._client = httpx.AsyncClient(timeout=30)

    async def login(self):
        # 1) Exchange email/password for JWT
        r = await self._client.post(f"{BASE}{LOGIN_PATH}", json={
            "email": self._email, "password": self._password
        })
        r.raise_for_status()
        data = r.json()
        # Many apps return { token, expiresIn } or nested {accessToken}
        self._token = data.get("token") or data.get("accessToken")
        self._token_exp = int(time.time()) + int(data.get("expiresIn", 3600))

    async def _auth(self):
        if not self._token or time.time() > (self._token_exp - 60):
            await self.login()

    async def me(self):
        await self._auth()
        r = await self._client.get(f"{BASE}{ME_PATH}", headers={"Authorization": f"Bearer {self._token}"})
        r.raise_for_status()
        return r.json()

    async def oven_status(self, oven_id: str):
        await self._auth()
        r = await self._client.get(f"{BASE}{STATUS_FMT.format(oven_id=oven_id)}",
                                   headers={"Authorization": f"Bearer {self._token}"})
        r.raise_for_status()
        return r.json()

    async def aclose(self):
        await self._client.aclose()