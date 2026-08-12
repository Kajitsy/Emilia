import json
import re
import uuid


class CharacterAPI:
    def __init__(self, client):
        self.client = client  # BaseClient or WSClient

    async def get_character(self, character_id=None, path=None):
        if path and not character_id:
            headers = {"Cookie": f"web-next-auth={self.client.cookie}"}
            match = re.match(r"^/character/([^/]+)(?:/([^/]+))?$", path)
            if match:
                id_part = match.group(1)
                slug_part = match.group(2)
                url = (
                    f"character/{id_part}/{slug_part}.json?id={id_part}&slug={slug_part}"
                    if slug_part
                    else f"character/{id_part}.json?id={id_part}"
                )

                response = await self.client.session.request(
                    "GET",
                    f"https://character.ai/_next/data/bP2i_9D3c_KrZ-_24-fQR/{url}",
                    headers=headers,
                    timeout=100,
                )

                pattern = re.compile(
                    r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*(\{.+?\})\s*</script>',
                    re.DOTALL,
                )
                m = pattern.search(response.text)
                if m:
                    character_id = (
                        json.loads(m.group(1))
                        .get("props", {})
                        .get("pageProps", {})
                        .get("prefetchedCharacterInfo", {})
                        .get("external_id")
                    )

        if not character_id:
            return None

        response = await self.client.request(
            f"character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22{character_id}%22%7D%7D%7D",
            domain="trpc",
        )
        character = (
            response[0]
            .get("result", {})
            .get("data", {})
            .get("json", {})
            .get("character", {})
        )
        voted = await self.client.request(
            f"character/v1/character_voted/{character_id}/voted",
            method="get",
            domain="neo",
        )

        return {"character": character, "voted": voted, "character_id": character_id}

    async def get_similar_characters(self, character_id):
        response = await self.client.request(
            f"recommendation/v1/character/similar/{character_id}", domain="neo"
        )
        return response.get("characters", [])

    async def search_characters(self, query: str):
        response = await self.client.request(
            f"search.search?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{query}%22%7D%7D%7D",
            domain="trpc",
        )
        return (
            response[0]
            .get("result", {})
            .get("data", {})
            .get("json", {})
            .get("characters", [])
        )

    async def query_autocomplete(self, query_prefix: str):
        response = await self.client.request(
            f"search/v1/query/autocomplete?query_prefix={query_prefix}",
            method="get",
            domain="neo",
        )
        return response.get("search_autocomplete", [])

    async def vote_character(self, character_id: str, vote: bool | None):
        data = {"external_id": character_id, "vote": vote}
        return await self.client.request(
            "character/v1/vote_character", data, "post", domain="neo", text=True
        )

    async def get_upvoted_characters(self):
        response = await self.client.request(
            "character/v1/upvoted_characters", method="get", domain="neo"
        )
        return response.get("characters", [])

    async def create_character(self, data: dict):
        return await self.client.request(
            "character/v1/create_character", data, "post", domain="neo"
        )

    async def update_character(self, data: dict):
        return await self.client.request(
            "character/v1/update_character", data, "post", domain="neo"
        )

    async def get_user_personas(self, force_refresh=0):
        response = await self.client.request(
            f"character/v1/get_user_personas?force_refresh={force_refresh}",
            method="get",
            domain="neo",
        )
        return response.get("personas", [])

    async def create_persona(
        self, avatar_rel_path: str, base_img_prompt: str, definition: str, name: str
    ):
        data = {
            "avatar_file_name": "",
            "avatar_rel_path": avatar_rel_path,
            "base_img_prompt": base_img_prompt,
            "categories": [],
            "copyable": False,
            "definition": definition,
            "description": "This is my persona.",
            "greeting": "Hello! This is my persona",
            "identifier": f"id:{uuid.uuid4()}",
            "img_gen_enabled": False,
            "name": name,
            "strip_img_prompt_from_msg": False,
            "title": name,
            "visibility": "PRIVATE",
            "voice_id": "",
        }
        response = await self.client.request(
            "character/v1/create_persona", data, "post", domain="neo"
        )
        return response.get("persona", {})

    async def update_persona(self, data: dict):
        response = await self.client.request(
            "character/v1/update_persona", data, "post", text=True
        )
        return response.get("persona", {}) if isinstance(response, dict) else response

    async def remove_persona(self, data: dict):
        data["archived"] = True
        return await self.client.request(
            "character/v1/update_persona", data, "post", text=True
        )

    async def get_category_characters(self, category: str):
        category_url = category.replace(" ", "%20").replace("&", "%26")
        response = await self.client.request(
            f"recommendation/v1/characters_with_tag/{category_url}", domain="neo"
        )
        return response.get("characters", [])[:20]
