import asyncio, zipfile, io, os

class EmiliaAPI:
    def __init__(self, client):
        self.url = "https://api.emilia.ateez.ru/"
        self.client = client

    async def get_themes(self, query: str = "", author: str = "", count: int = 0, offset: int = 0):
        response = await self.client.custom_request(f"{self.url}themes/?author={author}&q={query}&offset={offset}")
        return response

    async def get_theme(self, theme_id: str):
        response = await self.client.custom_request(f"{self.url}themes/{theme_id}")
        return response

    async def get_user_themes(self, creator_id: int):
        response = await self.client.custom_request(f"{self.url}user/{creator_id}/themes")
        return response

    async def download_theme(self, theme_name: str, theme_id: str):
        response_data = await self.client.custom_request(
            url=f"{self.url}themes/{theme_id}/download",
            method="get",
            is_bytes=True
        )

        extract_path = os.path.join("themes", theme_name)
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        def extract():
            with zipfile.ZipFile(io.BytesIO(response_data)) as archive:
                archive.extractall(extract_path)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, extract)

        return extract_path