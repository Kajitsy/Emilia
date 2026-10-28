import asyncio
import logging

import curl_cffi

from modules.api.base_client import SERVICE_UNAVAILABLE_STATUS

SERVICE_CHECK_URLS = (
    ("GET", "https://neo.character.ai/user/"),
    ("GET", "https://neo.character.ai/chats/recent"),
    ("GET", "https://plus.character.ai/chat/user/settings/"),
)
SERVICE_CHECK_TIMEOUT = 5


async def is_service_unavailable(token: str = "", cookie: str = "") -> bool:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
        "Cookie": f"web-next-auth={cookie}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0",
    }

    try:
        async with curl_cffi.AsyncSession() as session:
            responses = await asyncio.gather(
                *(
                    session.request(
                        method, url, headers=headers, timeout=SERVICE_CHECK_TIMEOUT
                    )
                    for method, url in SERVICE_CHECK_URLS
                ),
                return_exceptions=True,
            )
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).error(f"Service status check failed: {e}")
        return False

    if any(isinstance(response, Exception) for response in responses):
        return False

    return all(
        response.status_code == SERVICE_UNAVAILABLE_STATUS for response in responses
    )
