import json
import logging
import platform
from collections import defaultdict
from urllib.parse import urlparse

import curl_cffi

SERVICE_UNAVAILABLE_STATUS = 503
SERVICE_UNAVAILABLE_THRESHOLD = 3

if platform.system() == "Linux":
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
elif platform.system() == "Darwin":
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
else:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"

IMPERSONATE_TARGET = "chrome150"


class BaseClient:
    def __init__(self):
        self.token = None
        self.cookie = None
        self.session = curl_cffi.AsyncSession(impersonate=IMPERSONATE_TARGET)
        self.on_service_unavailable = None
        self._unavailable_streaks = defaultdict(int)
        self._notified_services = set()

    def _track_service_status(self, url: str, status_code: int) -> None:
        host = urlparse(url).netloc or url

        if status_code == SERVICE_UNAVAILABLE_STATUS:
            self._unavailable_streaks[host] += 1
            if (
                self._unavailable_streaks[host] >= SERVICE_UNAVAILABLE_THRESHOLD
                and host not in self._notified_services
            ):
                self._notified_services.add(host)
                logging.getLogger(__name__).error(
                    f"Service is unavailable: {host} returned "
                    f"{SERVICE_UNAVAILABLE_STATUS} for "
                    f"{self._unavailable_streaks[host]} consecutive requests"
                )
                if self.on_service_unavailable is not None:
                    self.on_service_unavailable()
        else:
            self._unavailable_streaks[host] = 0
            self._notified_services.discard(host)

    def set_token(self, token: str):
        self.token = token

    def set_cookie(self, cookie: str):
        self.cookie = cookie

    def _get_headers(self, additional: dict | None = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.cookie}",
            "User-Agent": USER_AGENT,
        }
        if additional:
            headers.update(additional)
        return headers

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: dict,
        data=None,
        json_data=None,
        return_text=False,
        is_bytes=False,
    ):
        try:
            response = await self.session.request(
                method, url, headers=headers, data=data, json=json_data, timeout=100
            )
            logging.getLogger(__name__).debug(f"Req: {url} [{response.status_code}]")
            self._track_service_status(url, response.status_code)

            if response.status_code in [200, 207, 400]:
                if is_bytes:
                    return response.content
                return response.json() if not return_text else json.loads(response.text)
            else:
                logging.getLogger(__name__).error(f"Request failed: {url} - {response.status_code}")
                return {"error": True, "status": response.status_code}
        except Exception as e:
            logging.getLogger(__name__).error(f"Async request error ({url}): {e}")
            raise

    async def request(
        self,
        endpoint: str,
        data=None,
        method: str = "GET",
        domain: str = "neo",
        text: bool = False,
    ):
        if data is None:
            data = {}

        headers = self._get_headers()
        base_urls = {
            "neo": "https://neo.character.ai/",
            "trpc": "https://character.ai/api/trpc/",
            "plus": "https://plus.character.ai/",
            "user": "https://user.api.character.ai/",
        }
        base_url = base_urls.get(domain, "https://plus.character.ai/")
        url = f"{base_url}{endpoint}"

        kwargs = {}
        if method.lower() in ("post", "put", "patch"):
            kwargs["json_data"] = data
        else:
            kwargs["data"] = data

        return await self._make_request(
            method, url, headers, return_text=text, **kwargs
        )

    async def custom_request(
        self,
        url: str,
        data=None,
        method: str = "get",
        text: bool = False,
        headers: dict | None = None,
        is_bytes: bool = False,
        **kwargs,
    ):
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        kwargs = (
            {"json_data": data}
            if method.lower() in ["post", "delete"]
            else {"data": data}
        )
        return await self._make_request(
            method, url, headers, return_text=text, is_bytes=is_bytes, **kwargs
        )
