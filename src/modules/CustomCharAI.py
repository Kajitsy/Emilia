import aiohttp, json, uuid, logging, inspect, curl_cffi

class Async:
    def __init__(self, token, auth_cookie=""):
        super().__init__()
        self.token = token
        self.auth_cookie = auth_cookie
        self.connect = ChatClient(self.token)
        self.session = aiohttp.ClientSession()

    async def request(self, endpoint, data = None, method = "get", neo = False, text = False):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.auth_cookie}"
        }

        if neo:
            url = f"https://neo.character.ai/{endpoint}"
        else:
            url = f"https://plus.character.ai/{endpoint}"

        while True:
            if method == "get":
                response = await self.session.get(url, headers=headers, params=data, timeout=100)
                logging.debug(f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async get request: {url}")
            elif method == "post":
                response = await self.session.post(url, headers=headers, json=data, timeout=100)
                logging.debug(f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async post request: {url}")
            elif method == "put":
                response = await self.session.put(url, headers=headers, json=data, timeout=100)
                logging.debug(f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async put request: {url}")
            else:
                raise ValueError("Invalid method")
            if response.status == 200:
                return await response.json() if not text else json.loads(await response.text())
            elif response.status == 400:
                pass
            else:
                raise Exception(f"Failed to get data, status code: {response.status}")

    async def trpc_request(self, endpoint, data = None, method = "get", text = False):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.auth_cookie}"
        }

        url = f"https://character.ai/api/trpc/{endpoint}"

        while True:
            if method == "get":
                response = await self.session.get(url, headers=headers, params=data, timeout=100)
                logging.debug(
                    f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async get request: {url}")
            elif method == "post":
                response = await self.session.post(url, headers=headers, json=data, timeout=100)
                logging.debug(
                    f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async post request: {url}")
            elif method == "put":
                response = await self.session.put(url, headers=headers, json=data, timeout=100)
                logging.debug(
                    f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async put request: {url}")
            else:
                raise ValueError("Invalid method")
            if response.status == 200 or response.status == 207:
                return await response.json() if not text else json.loads(await response.text())
            elif response.status == 400:
                pass
            else:
                raise Exception(f"Failed to get data, status code: {response.status}")

    async def custom_request(self, url, data = None, method = "get", text=False,headers={}):
        if method == "get":
            response = await self.session.get(url, headers=headers, params=data, timeout=100)
            logging.debug(
                f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async get request: {url}")
        elif method == "post":
            response = await self.session.post(url, headers=headers, json=data, timeout=100)
            logging.debug(
                f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async post request: {url}")
        elif method == "put":
            response = await self.session.put(url, headers=headers, json=data, timeout=100)
            logging.debug(
                f"CustomCharAI.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Async put request: {url}")
        else:
            raise ValueError("Invalid method")
        if response.status == 200:
            return await response.json() if not text else json.loads(await response.text())
        else:
            raise Exception(f"Failed to get data, status code: {response.status}")

    async def get_character(self, character_id):
        response = await self.trpc_request(f"character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22{character_id}%22%7D%7D%7D")
        return response[0].get("result", {}).get("data", {}).get("json", {}).get("character", {})

    async def tts(self, candidateId, roomId, turnId, voiceId="", voiceQuery=""):
        """voiceId or voiceQuery (Character Name) required"""
        if not voiceId:
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

    async def get_recent_chats(self, userCanUseRooms: bool = False):
        response = await self.trpc_request(f"discovery.recent?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22userCanUseRooms%22%3A{str(userCanUseRooms).lower()}%7D%7D%7D")
        return response[0].get("result", {}).get("data", {}).get("json", [])

    async def get_recommend_chats(self):
        response = await self.request("recommendation/v1/user", neo=True)
        return response.get("characters", None)

    async def get_featured_chats(self):
        response = await self.trpc_request("discovery.recommended?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22lang%22%3A%22none%22%7D%7D%7D")
        return response[0].get("result", {}).get("data", {}).get("json", {}).get("characters", [])

    async def get_main_page_chats(self):
        response = await self.trpc_request(f"character.infos,discovery.curatedLists,character.info,character.info,character.info,character.info,character.info,character.info,character.info,character.info,discovery.curatedCategories,discovery.charactersByCurated,character.info,character.info,character.info,character.info,character.info,character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalIds%22%3A%5B%22OtlDvgun8lLEEI3mXxVhl7_e8ArdmnuHa-hKeFKxjSI%22%2C%221his4cFt1rPawY6N01u5p5CM_4BbWJM3A-RVHwuSnRI%22%2C%22BQShAudovnnwL0rWwNzPzpn1cg_MQm3C3yPvUVuVvfU%22%2C%22Alp8ttiB1mOVF937d_b0hix2ToM3npDijaXRwA_7PY0%22%2C%22roqeHT1P5--gMOjrHEjE7z1PJ6sAXRYVcpLI6MYRemA%22%2C%22q0akobJPMxSgums8Z1GsVmsr498Zm7YtxRpKVS_iUl0%22%2C%22sv54nR1qDnJaS5Zf8Yxze-rrCGKSEMZUKg4Ui-azMk4%22%2C%22T-Vpx4MmCwvlb0PG_TkjBhGdpDWAhPVIRRk5E-eeEl4%22%2C%222gzUbuu3eznfsZMG6g6VxuyAoY_qGRUE22DNa399_I0%22%2C%22xAB0gj88bLy0lng4wcNPn1RAwQ51mHv03Uzqfus-Epk%22%2C%22m0kuZJY-9lFmEydDwmX1ea8pROEffyRjty4a_9xy2EI%22%2C%22uA2zSUxOzrsIKJKTzZZRA9AL6M5D1CShe8RAZns91As%22%2C%22LNb8DCj6vQ2Z1d3ok111bxoxpRVqqeP9drQd7IL3BGg%22%2C%22zWgJMRcp2Q_9fWfY4uBgLfQb9iDTPXyGGlSmSyOABe4%22%2C%22fvdCvTk3AAVeW-h3y4a9_ajfbIo1_1jdughy1VQJ0-8%22%2C%22ADisxXRP6TgrjJ-9M04m1ctHCeLTw-DPFUHJ1p-1Rqk%22%2C%22NayYpcaCSn8IkQBnES0UcFH-2unn48_i39iiVmAzAIc%22%2C%22wbcZlYilRx1ep5_L01aFB6-g0PPqbxHi_O4RsFNbOtw%22%2C%22FeXcfHZPzoStZCwqcqpf-wO-yCxsA-MGToRoipKfvzA%22%2C%22ZVHoWO767A7mR4DHHtum7J-l8tMFwY-NRbAy1S8ub4c%22%2C%22v-GVsCZOUNU5-Xovuji14m16qCjGW-96UIBZhyTP3do%22%2C%22dAPSIb3xavyQ-aO4Q0BxmUBXqHqaoktxr_l2rbRgccc%22%2C%22W3IC9o8l8Cbjep8pskXpbjwRn7huVkBM4GzzaxtLTaw%22%2C%22i-mYsXbuRSyYpsPivuFhjDCy9EcMBBi-uPLzER63E4c%22%2C%22DlqmValOtaDUVyYCbb-krx7PRdAQUiagFodPkpDtwTw%22%2C%22mXNjk1FpX06Nkjv4D0zyIKW2vJnxNnatiXr8chdN9Yc%22%5D%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22listIds%22%3A%5B%22cold_start_popular_characters_l30d_v1%22%2C%22cold_start_trending_characters_v1%22%5D%7D%7D%2C%222%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22A9zlEuzpvWiH8h0PNWEvZPK-PQifYxS-V24D3ncqIyU%22%7D%7D%2C%223%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22uD71krOYYFjVkYwspviH_8tYTybsf5eAGdwhNlFJAls%22%7D%7D%2C%224%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22f4hEGbw8ywUrjsrye03EJxiBdooy--HiOWgU2EiRJ0s%22%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229ZSDyg3OuPbFgDqGwy3RpsXqJblE4S1fKA_oU3yvfTM%22%7D%7D%2C%226%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22Hu84TYGgte3qVoQuy75x6Q1-ORjQbgoe2qaFoTkjaOM%22%7D%7D%2C%227%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22_FrgO6M-xCuTi72BYHbt-dQN2QsjNXnl-eKJGrjJttc%22%7D%7D%2C%228%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22WLcau8HDbkAPlnU9GPZvLVQ4QaWMhktCmgGFgG2nb5c%22%7D%7D%2C%229%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229wIR0NXzqD76sfJWRsHCGGb8IkPljhINj8WDy_2xjcg%22%7D%7D%2C%2210%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%2211%22%3A%7B%22json%22%3A%7B%22category%22%3A%22Helpers%22%7D%7D%2C%2212%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22W4MWmsvbFFnKF8b9e3Eg6ZUNzdhqvEZYy-tNRtxB_Og%22%7D%7D%2C%2213%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22GxP9L6QQ-qocxM9sYfvwywDw6wwfSmBJUjalAlD1ZCY%22%7D%7D%2C%2214%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%226HhWfeDjetnxESEcThlBQtEUo0O8YHcXyHqCgN7b2hY%22%7D%7D%2C%2215%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%227yDt2WH6Y_OpaAV4GsxKcY5xIQ8QT5M0kgpDQ6VAflI%22%7D%7D%2C%2216%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22YntB_ZeqRq2l_aVf2gWDCZl4oBttQzDvhj9cXafWcF8%22%7D%7D%2C%2217%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22YpuGnNPQiGvb0DIg77pDUruORvqEPQAxmabNuOIGylo%22%7D%7D%7D")
        return response

    async def get_featured_voices(self):
        response = await self.request("multimodal/api/v1/voices/featured", neo=True)
        return response.get("voices", [])

    async def get_trythis_chats(self):
        response = await self.trpc_request("character.info,character.info,character.info,character.info,character.info,character.info,character.info,character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22A9zlEuzpvWiH8h0PNWEvZPK-PQifYxS-V24D3ncqIyU%22%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22uD71krOYYFjVkYwspviH_8tYTybsf5eAGdwhNlFJAls%22%7D%7D%2C%222%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22f4hEGbw8ywUrjsrye03EJxiBdooy--HiOWgU2EiRJ0s%22%7D%7D%2C%223%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229ZSDyg3OuPbFgDqGwy3RpsXqJblE4S1fKA_oU3yvfTM%22%7D%7D%2C%224%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22Hu84TYGgte3qVoQuy75x6Q1-ORjQbgoe2qaFoTkjaOM%22%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22_FrgO6M-xCuTi72BYHbt-dQN2QsjNXnl-eKJGrjJttc%22%7D%7D%2C%226%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22WLcau8HDbkAPlnU9GPZvLVQ4QaWMhktCmgGFgG2nb5c%22%7D%7D%2C%227%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229wIR0NXzqD76sfJWRsHCGGb8IkPljhINj8WDy_2xjcg%22%7D%7D%2C%228%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%226HhWfeDjetnxESEcThlBQtEUo0O8YHcXyHqCgN7b2hY%22%7D%7D%7D")
        res_data = []
        for i in response:
            res_data.append(i.get('result', {}).get("data", {})['json']['character'])
        return res_data

    async def get_category_characters(self, category: str):
        response = await self.trpc_request(f"discovery.charactersByCurated?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22category%22%3A%22{category.replace(' ', '%20').replace('&', '%26')}%22%7D%7D%7D")
        return response[0].get("result", {}).get("data", {}).get("json", {}).get("characters", [])

    async def get_chats_with_character(self, character_id, num_preview_turns=1):
        response = await self.request(f"chats/?character_ids={character_id}&num_preview_turns={num_preview_turns}", neo=True)
        return response.get("chats", [])

    async def get_recent_chat(self, character_id):
        response = await self.request(f"chats/recent/{character_id}", neo=True)
        return response.get("chats", [])

    async def copy_chat(self, chat_id, end_turn_id):
        data = {
            "end_turn_id": end_turn_id
        }
        response = await self.request(f"chat/{chat_id}/copy", data, "post", neo=True)
        return response

    async def get_me(self):
        response = await self.request("chat/user/")
        return response.get("user", {}).get("user", {})

    async def get_user(self, username):
        response = await self.trpc_request(f"social.publicProfile?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22username%22%3A%22{username}%22%7D%7D%7D")
        return response[0].get("result", {}).get("data", {}).get("json", {})

    async def get_user_settings(self):
        response = await self.request("chat/user/settings/")
        return response

    async def update_user_settings(self, data):
        response = await self.request("chat/user/update_settings/", data, "post")
        return response

    async def get_chat(self, character_id):
        response = await self.request(f"chats/{character_id}", neo=True)
        return response

    async def get_chat_by_id(self, chat_id, load_metadata=False):
        response = await self.request(f"chat/{chat_id}/?load_metadata={load_metadata}", neo=True)
        return response

    async def get_available_models(self):
        response = await self.request(f"get-available-models", neo=True)
        return response.get('available_models', [])

    async def get_available_models_git(self):
        response = await self.custom_request("https://raw.githubusercontent.com/Kajitsy/Emilia/refs/heads/emilia/data/CAI_Available_Models.json", text=True)
        return response

    async def get_for_you_chats(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.auth_cookie}"
        }
        response = await self.custom_request("https://feed.api.character.ai/api/feed/recommended", method='post', headers=headers)
        return response.get('contents', [])

    async def hide_recent_chat(self, character_external_id):
        data = {
            "character_external_id": character_external_id
        }
        response_2 = await self.request(f"chats/recent/{character_external_id}/hide", "put", neo=True)
        response = await self.request(f"chat/history/hide/", data, "post")
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

    async def turn_remove(self, chat_id, turn_ids):
        data = {
            "turn_ids": turn_ids
        }
        response = await self.request(f"turns/{chat_id}/remove", data, "post", neo=True)
        return response

    async def follow(self, username):
        data = {
            "username": username
        }
        response = await self.request("chat/user/follow/", data, "post")
        return response

    async def get_following(self, pageParam=1, username=""):
        data = {
            "pageParam": pageParam,
            "username": username
        }
        response = await self.request("chat/user/public/following/", data, "post")
        return response

    async def get_followers(self, pageParam=1, username=""):
        data = {
            "pageParam": pageParam,
            "username": username
        }
        response = await self.request("chat/user/public/followers/", data, "post")
        return response

    async def get_me_following(self):
        response = await self.request("chat/user/following/", method="get")
        return response

    async def unfollow(self, username):
        data = {
            "username": username
        }
        response = await self.request("chat/user/unfollow/", data, "post")
        return response

    async def vote(self, character_id, vote):
        data = {
            "external_id": character_id,
            "vote": vote
        }
        response = await self.request("chat/character/vote/", data, "post", text=True)
        return response

    async def voted(self, character_id):
        response = await self.request(f"chat/character/{character_id}/voted/", "get", text=True)
        return response

    async def voices_search(self, query: str | None = "", character_name: str| None = ""):
        url = "multimodal/api/v1/voices/search"
        if character_name: url += f"?characterName={character_name}"
        if query: url += f"?query={query}"
        response = await self.request(url, "get", neo=True)
        return response.get('voices', [])

    async def voices_search_username(self, username: str | None = ""):
        url = f"multimodal/api/v1/voices/search?creatorInfo.username={username}"
        response = await self.request(url, "get", neo=True)
        return response.get('voices', [])

    async def character_search(self, query):
        url = f"search.search?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{query}%22%7D%7D%7D"
        response = await self.trpc_request(url)
        return response

    async def voice_override_update(self, character_id, voice_id):
        data = {
            "voice_id": voice_id
        }
        response = await self.request(f"chat/character/{character_id}/voice_override/update/", data, "post")
        return response

    async def voice_override_delete(self, character_id):
        response = await self.request(f"chat/character/{character_id}/voice_override/delete/", method= "post")
        return response

    async def voice_override(self, character_id):
        response = await self.request(f"chat/character/{character_id}/voice_override/", method= "get")
        return response

    async def get_voice(self, voice_id):
        response = await self.request(f"multimodal/api/v1/voices/{voice_id}", method= "get", neo=True)
        return response

    async def join_or_create_session(self, roomId:str, userAuthToken:str, username:str | None=None, voiceQueries:dict | None={}, voices:dict |None={}):
        data = {
            "enableASR": False,
            "platform": "web",
            "roomId": roomId,
            "userAuthToken": userAuthToken,
            "username": username,
            "voiceQueries": voiceQueries,
            "voices": voices
        }
        response = await self.request("multimodal/api/v1/sessions/joinOrCreateSession/", data, "post", True)
        return response

    async def discard_candidate(self, candidate_id, character_id, room_id):
        data = {
            'candidateId': candidate_id,
            'characterId': character_id,
            'roomId': room_id
        }
        response = await self.request("multimodal/api/v1/sessions/discardCandidate/", data, "post", True)
        return response

    async def resurrect(self, chat_id):
        response = await self.request(f"chat/{chat_id}/resurrect", method="get", neo=True)
        return response

    async def get_upvoted_characters(self):
        response = await self.request("character/v1/upvoted_characters", method="get", neo=True)
        return response.get('characters', [])

    async def create_persona(self, avatar_rel_path, base_img_prompt, definition, name):
        data = {
            'avatar_file_name': "",
            'avatar_rel_path': avatar_rel_path,
            'base_img_prompt': base_img_prompt,
            'categories': [],
            'copyable': False,
            'definition': definition,
            'description': "This is my persona.",
            'greeting': "Hello! This is my persona",
            'identifier': f"id:{uuid.uuid4()}",
            'img_gen_enabled': False,
            'name': name,
            'strip_img_prompt_from_msg': False,
            'title': name,
            'visibility': "PRIVATE",
            'voice_id': ""
        }
        response = await self.request("character/v1/create_persona", data, "post", True)
        return response.get('persona', {})

    async def remove_persona(self, data):
        data['archived'] = True
        response = await self.request("character/v1/update_persona", data, "post", True)
        return response

    async def update_persona(self, data):
        response = await self.request("character/v1/update_persona", data, "post", True)
        print(response)
        return response.get('persona', {})

    async def get_user_personas(self, force_refresh=0):
        response = await self.request(f"character/v1/get_user_personas?force_refresh={force_refresh}", method="get", neo=True)
        return response.get('personas', [])

    async def uploadAvatar(self, filetype, image):
        data = {
            "0": {
                "json": {
                    "imageDataUrl": f"data:image/{filetype};base64,{image}"
                }
            }
        }

        response = await self.trpc_request("user.uploadAvatar?batch=1", data, "post")
        return response[0]['result']['data']['json']

class ChatClient:
    def __init__(self, token: str = ""):
        self.token = token
        self.session: curl_cffi.AsyncSession | None = None
        self.ws = None

    async def __aenter__(self):
        self.session = curl_cffi.AsyncSession()
        self.ws = await self.session.ws_connect(
            'wss://neo.character.ai/ws/',
            cookies={'HTTP_AUTHORIZATION': f'Token {self.token}'}
        )

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

    async def __call__(self, token: str = None):
        if token:
            self.token = token
        return await self.__aenter__()

    async def new_chat(self, char: str, creator_id: str, greeting: bool = True,
                       chat_id: str = None, preferred_model_type: str = "MODEL_TYPE_BALANCED"):
        chat_id = str(uuid.uuid4()) if chat_id is None else chat_id

        payload = {
            'command': 'create_chat',
            'payload': {
                'chat': {
                    'character_id': char,
                    'chat_id': chat_id,
                    'creator_id': str(creator_id),
                    'preferred_model_type': preferred_model_type,
                    'type': 'TYPE_ONE_ON_ONE',
                    'visibility': 'VISIBILITY_PRIVATE'
                },
                'with_greeting': greeting
            }
        }

        await self.ws.send_str(json.dumps(payload))
        response = json.loads((await self.ws.recv_str()))

        if 'chat' not in response:
            raise Exception(response.get('comment', 'Unknown error'))

        answer = json.loads((await self.ws.recv_str()))['turn']
        return response['chat'], answer

    async def send_message(self, char: str, chat_id: str, text: str, author: dict = {}):
        message = {
            'command': 'create_and_generate_turn',
            'payload': {
                'character_id': char,
                'turn': {
                    'turn_key': {
                        'chat_id': chat_id
                    },
                    'author': author,
                    'candidates': [
                        {
                            'raw_content': text
                        }
                    ]
                }
            }
        }

        await self.ws.send_str(json.dumps(message))

        while True:
            msg = await self.ws.recv_str()
            response = json.loads(msg)
            if 'turn' not in response:
                raise Exception(response['comment'])
            yield response

    async def generate_turn_candidate(self, char: str, chat_id: str, turn_id: str, user_name: str = ""):
        message = {
            'command': 'generate_turn_candidate',
            'payload': {
                'character_id': char,
                'turn_key': {
                    'chat_id': chat_id,
                    'turn_id': turn_id
                },
                'user_name': user_name
            }
        }

        await self.ws.send_str(json.dumps(message))

        while True:
            msg = await self.ws.recv_str()
            response = json.loads(msg)
            if 'turn' not in response:
                raise Exception(response['comment'])
            yield response

    async def edit_message(self, chat_id: str, message_id: str, text: str):
        payload = {
            'command': 'edit_turn_candidate',
            'payload': {
                'turn_key': {
                    'chat_id': chat_id,
                    'turn_id': message_id
                },
                'new_candidate_raw_content': text
            }
        }
        await self.ws.send_str(json.dumps(payload))
        response = json.loads((await self.ws.recv_str()))
        if 'turn' not in response:
            raise Exception(response['comment'])
        return response['turn']