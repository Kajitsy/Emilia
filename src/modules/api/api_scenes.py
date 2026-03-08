class ScenesAPI:
    def __init__(self, client):
        self.client = client

    async def get_curated_scenes(self):
        response = await self.client.request("scene/v1/scenes/curated", domain="neo")
        return response.get("scenes", [])

    async def get_scene(self, scene_id: str):
        response = await self.client.request(f"scene/v1/scenes/{scene_id}", method="get", domain="neo")
        return response.get("scene", {})

    async def get_user_scenes(self, username: str):
        response = await self.client.request(f"scene/v1/scenes?creator_username={username}", domain="neo")
        return response.get("scenes", [])

    async def search_scenes(self, query: str):
        response = await self.client.request(
            f"search.searchScenes?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{query}%22%7D%7D%7D",
            domain="trpc"
        )
        return response[0].get('result', {}).get('data', {}).get('json', {}).get('creators', [])

    async def create_scene(self, data: dict):
        response = await self.client.request("scene/v1/scenes", data, "post", domain="neo")
        return response.get('scene', {})

    async def update_scene(self, scene_id: str, data: dict):
        response = await self.client.request(f"scene/v1/scenes/{scene_id}", data, "put", domain="neo")
        return response.get('scene', {})

    async def remove_scene(self, scene_id: str):
        return await self.client.request(f"scene/v1/scenes/{scene_id}", method="delete", domain="neo")