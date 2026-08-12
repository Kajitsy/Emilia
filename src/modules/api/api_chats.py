class ChatsAPI:
    def __init__(self, client):
        self.client = client

    async def get_recent_chats(self):
        response = await self.client.request("chats/recent", domain="neo")
        return response.get("chats", [])

    async def get_chat(self, character_id: str):
        response = await self.client.request(
            f"chats/recent/{character_id}", domain="neo"
        )
        return response.get("chats", [])

    async def get_chat_by_id(self, chat_id: str, load_metadata: bool = False):
        return await self.client.request(
            f"chat/{chat_id}/?load_metadata={load_metadata}", domain="neo"
        )

    async def get_character_chats(self, character_id: str, num_preview_turns: int = 1):
        response = await self.client.request(
            f"chats/?character_ids={character_id}&num_preview_turns={num_preview_turns}",
            domain="neo",
        )
        return response.get("chats", [])

    async def get_history(self, chat_id: str, next_token: str | None = None):
        url = f"turns/{chat_id}"
        if next_token:
            url += f"?next_token={next_token}"

        response = await self.client.request(url, domain="neo")
        turns = response.get("turns", [])
        meta_token = response.get("meta", {}).get("next_token", "")

        turns.reverse()

        return {"turns": turns, "next_token": meta_token}

    async def remove_turns(self, chat_id: str, turn_ids: list):
        data = {"turn_ids": turn_ids}
        return await self.client.request(
            f"turns/{chat_id}/remove", data, "post", domain="neo"
        )

    async def copy_chat(self, chat_id: str, end_turn_id: str):
        data = {"end_turn_id": end_turn_id}
        return await self.client.request(
            f"chat/{chat_id}/copy", data, "post", domain="neo"
        )

    async def hide_chat(self, character_id: str):
        return await self.client.request(
            f"chats/recent/{character_id}/hide", method="put", domain="neo"
        )

    async def get_recommended_chars(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.client.token}",
            "Cookie": f"web-next-auth={self.client.cookie}",
        }
        response = await self.client.custom_request(
            "https://feed.api.character.ai/api/feed/recommended",
            method="post",
            headers=headers,
        )
        return response.get("contents", [])

    async def get_trythis_chats(self):
        query = "%7B%220%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22A9zlEuzpvWiH8h0PNWEvZPK-PQifYxS-V24D3ncqIyU%22%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22uD71krOYYFjVkYwspviH_8tYTybsf5eAGdwhNlFJAls%22%7D%7D%2C%222%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22f4hEGbw8ywUrjsrye03EJxiBdooy--HiOWgU2EiRJ0s%22%7D%7D%2C%223%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229ZSDyg3OuPbFgDqGwy3RpsXqJblE4S1fKA_oU3yvfTM%22%7D%7D%2C%224%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22Hu84TYGgte3qVoQuy75x6Q1-ORjQbgoe2qaFoTkjaOM%22%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22_FrgO6M-xCuTi72BYHbt-dQN2QsjNXnl-eKJGrjJttc%22%7D%7D%2C%226%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22WLcau8HDbkAPlnU9GPZvLVQ4QaWMhktCmgGFgG2nb5c%22%7D%7D%2C%227%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229wIR0NXzqD76sfJWRsHCGGb8IkPljhINj8WDy_2xjcg%22%7D%7D%2C%228%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%226HhWfeDjetnxESEcThlBQtEUo0O8YHcXyHqCgN7b2hY%22%7D%7D%7D"
        response = await self.client.request(
            f"character.info,character.info,character.info,character.info,character.info,character.info,character.info,character.info?batch=1&input={query}",
            domain="trpc",
        )

        res_data = []
        for i in response:
            res_data.append(
                i.get("result", {}).get("data", {}).get("json", {}).get("character")
            )
        return res_data

    async def get_main_page_chats(self):
        query = "%7B%220%22%3A%7B%22json%22%3A%7B%22externalIds%22%3A%5B%22OtlDvgun8lLEEI3mXxVhl7_e8ArdmnuHa-hKeFKxjSI%22%2C%221his4cFt1rPawY6N01u5p5CM_4BbWJM3A-RVHwuSnRI%22%2C%22BQShAudovnnwL0rWwNzPzpn1cg_MQm3C3yPvUVuVvfU%22%2C%22Alp8ttiB1mOVF937d_b0hix2ToM3npDijaXRwA_7PY0%22%2C%22roqeHT1P5--gMOjrHEjE7z1PJ6sAXRYVcpLI6MYRemA%22%2C%22q0akobJPMxSgums8Z1GsVmsr498Zm7YtxRpKVS_iUl0%22%2C%22sv54nR1qDnJaS5Zf8Yxze-rrCGKSEMZUKg4Ui-azMk4%22%2C%22T-Vpx4MmCwvlb0PG_TkjBhGdpDWAhPVIRRk5E-eeEl4%22%2C%222gzUbuu3eznfsZMG6g6VxuyAoY_qGRUE22DNa399_I0%22%2C%22xAB0gj88bLy0lng4wcNPn1RAwQ51mHv03Uzqfus-Epk%22%2C%22m0kuZJY-9lFmEydDwmX1ea8pROEffyRjty4a_9xy2EI%22%2C%22uA2zSUxOzrsIKJKTzZZRA9AL6M5D1CShe8RAZns91As%22%2C%22LNb8DCj6vQ2Z1d3ok111bxoxpRVqqeP9drQd7IL3BGg%22%2C%22zWgJMRcp2Q_9fWfY4uBgLfQb9iDTPXyGGlSmSyOABe4%22%2C%22fvdCvTk3AAVeW-h3y4a9_ajfbIo1_1jdughy1VQJ0-8%22%2C%22ADisxXRP6TgrjJ-9M04m1ctHCeLTw-DPFUHJ1p-1Rqk%22%2C%22NayYpcaCSn8IkQBnES0UcFH-2unn48_i39iiVmAzAIc%22%2C%22wbcZlYilRx1ep5_L01aFB6-g0PPqbxHi_O4RsFNbOtw%22%2C%22FeXcfHZPzoStZCwqcqpf-wO-yCxsA-MGToRoipKfvzA%22%2C%22ZVHoWO767A7mR4DHHtum7J-l8tMFwY-NRbAy1S8ub4c%22%2C%22v-GVsCZOUNU5-Xovuji14m16qCjGW-96UIBZhyTP3do%22%2C%22dAPSIb3xavyQ-aO4Q0BxmUBXqHqaoktxr_l2rbRgccc%22%2C%22W3IC9o8l8Cbjep8pskXpbjwRn7huVkBM4GzzaxtLTaw%22%2C%22i-mYsXbuRSyYpsPivuFhjDCy9EcMBBi-uPLzER63E4c%22%2C%22DlqmValOtaDUVyYCbb-krx7PRdAQUiagFodPkpDtwTw%22%2C%22mXNjk1FpX06Nkjv4D0zyIKW2vJnxNnatiXr8chdN9Yc%22%5D%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22listIds%22%3A%5B%22cold_start_popular_characters_l30d_v1%22%2C%22cold_start_trending_characters_v1%22%5D%7D%7D%2C%222%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22A9zlEuzpvWiH8h0PNWEvZPK-PQifYxS-V24D3ncqIyU%22%7D%7D%2C%223%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22uD71krOYYFjVkYwspviH_8tYTybsf5eAGdwhNlFJAls%22%7D%7D%2C%224%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22f4hEGbw8ywUrjsrye03EJxiBdooy--HiOWgU2EiRJ0s%22%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229ZSDyg3OuPbFgDqGwy3RpsXqJblE4S1fKA_oU3yvfTM%22%7D%7D%2C%226%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22Hu84TYGgte3qVoQuy75x6Q1-ORjQbgoe2qaFoTkjaOM%22%7D%7D%2C%227%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22_FrgO6M-xCuTi72BYHbt-dQN2QsjNXnl-eKJGrjJttc%22%7D%7D%2C%228%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22WLcau8HDbkAPlnU9GPZvLVQ4QaWMhktCmgGFgG2nb5c%22%7D%7D%2C%229%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229wIR0NXzqD76sfJWRsHCGGb8IkPljhINj8WDy_2xjcg%22%7D%7D%2C%2210%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%2211%22%3A%7B%22json%22%3A%7B%22category%22%3A%22Helpers%22%7D%7D%2C%2212%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22W4MWmsvbFFnKF8b9e3Eg6ZUNzdhqvEZYy-tNRtxB_Og%22%7D%7D%2C%2213%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22GxP9L6QQ-qocxM9sYfvwywDw6wwfSmBJUjalAlD1ZCY%22%7D%7D%2C%2214%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%226HhWfeDjetnxESEcThlBQtEUo0O8YHcXyHqCgN7b2hY%22%7D%7D%2C%2215%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%227yDt2WH6Y_OpaAV4GsxKcY5xIQ8QT5M0kgpDQ6VAflI%22%7D%7D%2C%2216%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22YntB_ZeqRq2l_aVf2gWDCZl4oBttQzDvhj9cXafWcF8%22%7D%7D%2C%2217%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22YpuGnNPQiGvb0DIg77pDUruORvqEPQAxmabNuOIGylo%22%7D%7D%7D"
        return await self.client.request(
            f"character.infos,discovery.curatedLists,character.info,character.info,character.info,character.info,character.info,character.info,character.info,character.info,discovery.curatedCategories,discovery.charactersByCurated,character.info,character.info,character.info,character.info,character.info,character.info?batch=1&input={query}",
            domain="trpc",
        )
