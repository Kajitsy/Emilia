import asyncio, zipfile, io, os, requests

class EmiliaAPI:
    def __init__(self, client):
        self.url = "https://api.emilia.ateez.ru/"
        self.client = client

    async def get_update_servers(self):
        response = await self.client.custom_request(f"{self.url}servers/update")
        return response

    async def get_themes(self, query: str = "", author: str = "", count: int = 0, offset: int = 0):
        response = await self.client.custom_request(f"{self.url}themes/?author={author}&q={query}&offset={offset}")
        return response

    async def get_theme(self, theme_id: str):
        response = await self.client.custom_request(f"{self.url}themes/{theme_id}")
        return response

    async def delete_theme(self, theme_id: str, token: str, user_id: int, username: str, avatar_file_name: str):
        data = {
            "token": token,
            "id": user_id,
            "username": username,
            "avatar_file_name": avatar_file_name,
        }
        response = await self.client.custom_request(f"{self.url}themes/{theme_id}/delete", data, method="DELETE")
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
    
    async def upload_theme(self, theme_name: str, user_id: int, username: str, avatar_file_name: str, token: str):
        theme_path = os.path.join("themes", theme_name)
        if not os.path.exists(theme_path):
            return {"error": "Theme path not found"}

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(theme_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, theme_path)
                    zip_file.write(file_path, arcname)
        zip_buffer.seek(0)

        data = {
            "token": token,
            "id": user_id,
            "username": username,
            "avatar_file_name": avatar_file_name,
        }

        multipart = {
            "file": (f"{username}_{theme_name}.zip", zip_buffer.getvalue(), "application/zip")
        }
        response = requests.post(f"{self.url}themes/upload",data=data, files=multipart)
        return response.json()

    async def update_theme(self, theme_name: str, theme_id: str, user_id: int, username: str, avatar_file_name: str, token: str):
        theme_path = os.path.join("themes", theme_name)
        if not os.path.exists(theme_path):
            return {"error": "Theme path not found"}

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(theme_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, theme_path)
                    zip_file.write(file_path, arcname)
        zip_buffer.seek(0)

        data = {
            "token": token,
            "id": user_id,
            "username": username,
            "avatar_file_name": avatar_file_name,
        }

        multipart = {
            "file": (f"{username}_{theme_name}.zip", zip_buffer.getvalue(), "application/zip")
        }
        response = requests.post(f"{self.url}themes/{theme_id}/update",data=data, files=multipart)
        return response.json()