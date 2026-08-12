class VoicesAPI:
    def __init__(self, client):
        self.client = client

    async def search_voices(self, query: str | None = None, character_name: str | None = None):
        url = "multimodal/api/v1/voices/search"
        params = []
        if character_name:
            params.append(f"characterName={character_name}")
        if query:
            params.append(f"query={query}")

        if params:
            url += "?" + "&".join(params)

        response = await self.client.request(url, method="get", domain="neo")
        return response.get("voices", [])

    async def search_voices_by_username(self, username: str):
        url = f"multimodal/api/v1/voices/search?creatorInfo.username={username}"
        response = await self.client.request(url, method="get", domain="neo")
        return response.get("voices", [])

    async def get_featured_voices(self):
        response = await self.client.request(
            "multimodal/api/v1/voices/featured", method="get", domain="neo"
        )
        return response.get("voices", [])

    async def get_voice(self, voice_id: str):
        return await self.client.request(
            f"multimodal/api/v1/voices/{voice_id}", method="get", domain="neo"
        )

    async def replay(
        self,
        candidate_id: str,
        room_id: str,
        turn_id: str,
        voice_id: str = "",
        voice_query: str = "",
    ):
        data = {
            "candidateId": candidate_id,
            "roomId": room_id,
            "turnId": turn_id,
            "voiceId": voice_id,
        }
        if not voice_id:
            data["voiceQuery"] = voice_query

        return await self.client.request(
            "multimodal/api/v1/memo/replay", data, "post", domain="neo"
        )

    async def get_voice_override(self, character_id: str):
        return await self.client.request(
            f"chat/character/{character_id}/voice_override/",
            method="get",
            domain="plus",
        )

    async def update_voice_override(self, character_id: str, voice_id: str):
        data = {"voice_id": voice_id}
        return await self.client.request(
            f"chat/character/{character_id}/voice_override/update/",
            data,
            "post",
            domain="plus",
        )

    async def delete_voice_override(self, character_id: str):
        return await self.client.request(
            f"chat/character/{character_id}/voice_override/delete/",
            method="post",
            domain="plus",
        )

    async def join_or_create_session(
        self,
        room_id: str,
        user_auth_token: str,
        username: str | None = None,
        voice_queries: dict | None = None,
        voices: dict | None = None,
    ):
        if voice_queries is None:
            voice_queries = {}
        if voices is None:
            voices = {}

        data = {
            "enableASR": False,
            "platform": "web",
            "roomId": room_id,
            "userAuthToken": user_auth_token,
            "username": username,
            "voiceQueries": voice_queries,
            "voices": voices,
        }
        return await self.client.request(
            "multimodal/api/v1/sessions/joinOrCreateSession/",
            data,
            "post",
            domain="neo",
            text=True,
        )
