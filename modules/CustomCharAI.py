import aiohttp, requests
from modules.config import getconfig

class Async():
    def __init__(self, token = getconfig('client', configfile='charaiconfig.json')):
        super().__init__()
        self.token = token

    async def request(self, endpoint, data = None, method = "get", neo = False):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {getconfig('client', configfile='charaiconfig.json')}"
        }

        if neo:
            url = f"https://neo.character.ai/{endpoint}"
        else:
            url = f"https://plus.character.ai/{endpoint}"

        async with aiohttp.ClientSession() as session:
            if method == "get":
                async with session.get(url, headers=headers, params=data) as response:
                    print("Async get request: ", url)
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status}")
            elif method == "post":
                async with session.post(url, headers=headers, json=data) as response:
                    print("Async post request:", url)
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status}")
            else:
                raise ValueError("Invalid method")

    async def get_character(self, character_id):
        data = {
            "external_id": character_id
        }
        response = await self.request("chat/character/info/", data, "post")
        return response.get("character", None)

    async def tts(self, candidateId, roomId, turnId, voiceId=None, voiceQuery=None):
        """voiceId or voiceQuery required"""
        if voiceId == "":
            data = {
                "candidateId": candidateId,
                "roomId": roomId,
                "turnId": turnId,
                "voiceId": voiceId,
                "voiceQuery":voiceQuery
            }
        else:
            data = {
                "candidateId": candidateId,
                "roomId": roomId,
                "turnId": turnId,
                "voiceId": voiceId
            }
        response = await self.request("multimodal/api/v1/memo/replay", data, "post", neo=True)
        return response

    async def get_recommend_chats(self):
        response = await self.request("recommendation/v1/user", neo=True)
        return response.get("characters", None)

    async def get_recent_chats(self):
        response = await self.request("chats/recent", neo=True)
        return response("chats", [])

    async def get_recent_chat(self, character_id):
        response = await self.request(f"chats/recent/{character_id}", neo=True)
        return response.get("chats", [])

    async def get_me(self):
        response = await self.request("chat/user/")
        return response.get("user", None).get("user", None)

    async def get_chat(self, character_id):
        response = await self.request(f"chats/{character_id}", neo=True)
        return response

    async def get_messages(self, chat_id, next_token=None):
        url = f"turns/{chat_id}"
        if next_token: url += f"?next_token={next_token}"

        response = await self.request(url, neo=True)

        next_token = response.get("meta", {}).get("next_token", "")
        turns = response.get("turns", [])

        return turns, next_token

    async def get_all_messages(self, chat_id):
        all_turns = []

        turns, next_token = await self.get_messages(chat_id)

        while True:
            if not turns: break
            all_turns += turns
            if not next_token: break

            turns, next_token = await self.get_messages(chat_id, next_token)

        return all_turns

class Sync():
    def __init__(self, token = getconfig('client', configfile='charaiconfig.json')):
        super().__init__()
        self.token = token

    def request(self, endpoint, data=None, method="get", neo=False):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}"
        }

        if neo:
            url = f"https://neo.character.ai/{endpoint}"
        else:
            url = f"https://plus.character.ai/{endpoint}"

        with requests.session() as session:
            if method == "get":
                with session.get(url, headers=headers, params=data) as response:
                    print("Sync get request:", url)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status_code}")
            elif method == "post":
                with session.post(url, headers=headers, json=data) as response:
                    print("Sync post request:", url)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status_code}")
            else:
                raise ValueError("Invalid method")

    def get_character(self, character_id):
        data = {
            "external_id": character_id
        }
        response = self.request("chat/character/info/", data, "post")
        return response.get("character", None)

    def tts(self, candidateId, roomId, turnId, voiceId=None, voiceQuery=None):
        """voiceId or voiceQuery required"""
        if voiceId == "":
            data = {
                "candidateId": candidateId,
                "roomId": roomId,
                "turnId": turnId,
                "voiceId": voiceId,
                "voiceQuery":voiceQuery
            }
        else:
            data = {
                "candidateId": candidateId,
                "roomId": roomId,
                "turnId": turnId,
                "voiceId": voiceId
            }
        response = self.request("multimodal/api/v1/memo/replay", data, "post", neo=True)
        return response

    def get_recommend_chats(self):
        response = self.request("recommendation/v1/user", neo=True)
        return response.get("characters", None)

    def get_recent_chats(self):
        response = self.request("chats/recent", neo=True)
        return response.get("chats", [])

    def get_recent_chat(self, character_id):
        response = self.request(f"chats/recent/{character_id}", neo=True)
        return response.get("chats", [])

    def get_me(self):
        response = self.request("chat/user/")
        return response.get("user", None).get("user", None)

    def get_messages(self, chat_id, next_token=None):
        url = f"turns/{chat_id}"
        if next_token: url += f"?next_token={next_token}"

        response = self.request(url, neo=True)

        next_token = response.get("meta", {}).get("next_token", "")
        turns = response.get("turns", [])

        return turns, next_token

    def get_all_messages(self, chat_id):
        all_turns = []

        turns, next_token = self.get_messages(chat_id)

        while True:
            if not turns: break
            all_turns += turns
            if not next_token: break

            turns, next_token = self.get_messages(chat_id, next_token)

        return all_turns
