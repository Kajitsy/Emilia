import logging, json, curl_cffi

class BaseClient:
    def __init__(self):
        self.token = None
        self.cookie = None
        self.session = curl_cffi.AsyncSession()

    def set_token(self, token: str):
        self.token = token

    def set_cookie(self, cookie: str):
        self.cookie = cookie

    def _get_headers(self, additional: dict = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0"
        }
        if additional:
            headers.update(additional)
        return headers

    async def _make_request(self, method: str, url: str, headers: dict, data=None, json_data=None, return_text=False, is_bytes=False):
        try:
            response = await self.session.request(method, url, headers=headers, data=data, json=json_data, timeout=100)
            logging.debug(f"Req: {url} [{response.status_code}]")

            if response.status_code in [200, 207, 400]:
                if is_bytes:
                    return response.content
                return response.json() if not return_text else json.loads(response.text)
            else:
                logging.error(f"Request failed: {url} - {response.status_code}")
                return {"error": True, "status": response.status_code}
        except Exception as e:
            logging.error(f"Async request error ({url}): {e}")
            raise

    async def request(self, endpoint: str, data=None, method: str = "GET", domain: str = "neo", text: bool = False):
        if data is None:
            data = {}

        headers = self._get_headers()
        base_urls = {
            "neo": "https://neo.character.ai/",
            "trpc": "https://character.ai/api/trpc/",
            "plus": "https://plus.character.ai/",
            "user": "https://user.api.character.ai/"
        }
        base_url = base_urls.get(domain, "https://plus.character.ai/")
        url = f"{base_url}{endpoint}"

        kwargs = {}
        if method.lower() in ("post", "put", "patch"):
            kwargs["json_data"] = data
        else:
            kwargs["data"] = data

        return await self._make_request(method, url, headers, return_text=text, **kwargs)

    async def custom_request(self, url: str, data=None, method: str = "get", text: bool = False, headers: dict = None, is_bytes: bool = False, **kwargs):
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        kwargs = {"json_data": data} if method.lower() in ["post", "delete"] else {"data": data}
        return await self._make_request(method, url, headers, return_text=text, is_bytes=is_bytes, **kwargs)