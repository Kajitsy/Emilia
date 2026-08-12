class UsersAPI:
    def __init__(self, client):
        self.client = client

    async def get_me(self):
        response = await self.client.request("user/", domain="neo")
        return response.get("user", {})

    async def get_user_settings(self):
        return await self.client.request("chat/user/settings/", domain="plus")

    async def update_user_settings(self, data: dict):
        return await self.client.request(
            "chat/user/update_settings/", data, "post", domain="neo"
        )

    async def update_user_settings_2(self, data: dict):
        return await self.client.request(
            "chat/user/update/", data, "post", domain="neo"
        )

    async def get_user(self, username: str):
        response = await self.client.request(
            f"social.publicProfile?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22username%22%3A%22{username}%22%7D%7D%7D",
            domain="trpc",
        )
        return response[0].get("result", {}).get("data", {}).get("json", {})

    async def get_user_following(self, page_param: int = 1, username: str = ""):
        data = {"pageParam": page_param, "username": username}
        return await self.client.request(
            "chat/user/public/following/", data, "post", domain="plus"
        )

    async def get_user_followers(self, page_param: int = 1, username: str = ""):
        data = {"pageParam": page_param, "username": username}
        return await self.client.request(
            "chat/user/public/followers/", data, "post", domain="plus"
        )

    async def get_me_following(self):
        return await self.client.request(
            "chat/user/following/", method="get", domain="plus"
        )

    async def user_follow(self, username: str):
        data = {"target_username": username}
        return await self.client.request(
            "external/user/follow", data, "post", domain="user"
        )

    async def user_unfollow(self, username: str):
        data = {"target_username": username}
        return await self.client.request(
            "external/user/unfollow", data, "post", domain="user"
        )

    async def user_search(self, query: str):
        response = await self.client.request(
            f"search.searchCreators?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{query}%22%2C%22sortedBy%22%3A%22relevance%22%7D%7D%7D",
            domain="trpc",
        )
        return (
            response[0]
            .get("result", {})
            .get("data", {})
            .get("json", {})
            .get("creators", [])
        )

    async def upload_avatar(self, filetype: str, image_base64: str):
        data = {
            "0": {
                "json": {"imageDataUrl": f"data:image/{filetype};base64,{image_base64}"}
            }
        }
        response = await self.client.request(
            "user.uploadAvatar?batch=1", data, "post", domain="trpc"
        )
        return response[0].get("result", {}).get("data", {}).get("json", {})

    async def upload_image(self, multipart):
        headers = {
            "Content-Type": "multipart/form-data",
            "Authorization": f"Token {self.client.token}",
            "Cookie": f"web-next-auth={self.client.cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0",
        }
        response = await self.client.session.request(
            "POST",
            "https://neo.character.ai/image/upload_private_image",
            headers=headers,
            multipart=multipart,
            timeout=100,
            impersonate="chrome",
        )
        return response.json()
