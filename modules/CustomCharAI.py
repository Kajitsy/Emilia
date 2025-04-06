from modulefinder import replacePackageMap

import aiohttp, websockets, json, uuid, logging
from websockets import exceptions

class Async():
    def __init__(self, token, auth_cookie=""):
        super().__init__()
        self.token = token
        self.auth_cookie = auth_cookie
        self.connect = ChatClient(self.token)

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

        async with aiohttp.ClientSession() as session:
            while True:
                if method == "get":
                    async with session.get(url, headers=headers, params=data, timeout=100) as response:
                        logging.debug(f"CustomCharAI.py: Async get request: {url}")
                        if response.status == 200:
                            return await response.json() if not text else json.loads(await response.text())
                        elif response.status == 400:
                            pass
                        else:
                            raise Exception(f"Failed to get data, status code: {response.status}")
                elif method == "post":
                    async with session.post(url, headers=headers, json=data, timeout=100) as response:
                        logging.debug(f"CustomCharAI.py: Async post request: {url}")
                        if response.status == 200:
                            return await response.json() if not text else json.loads(await response.text())
                        elif response.status == 400:
                            pass
                        else:
                            raise Exception(f"Failed to get data, status code: {response.status}")
                elif method == "put":
                    async with session.put(url, headers=headers, json=data, timeout=100) as response:
                        logging.debug(f"CustomCharAI.py: Async put request: {url}")
                        if response.status == 200:
                            return await response.json() if not text else json.loads(await response.text())
                        elif response.status == 400:
                            pass
                        else:
                            raise Exception(f"Failed to get data, status code: {response.status}")
                else:
                    raise ValueError("Invalid method")

    async def trpc_request(self, endpoint, data = None, method = "get"):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.auth_cookie}"
        }

        url = f"https://character.ai/api/trpc/{endpoint}"

        async with aiohttp.ClientSession() as session:
            while True:
                if method == "get":
                    async with session.get(url, headers=headers, params=data, timeout=100) as response:
                        logging.debug(f"CustomCharAI.py: Async get request: {url}")
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 400:
                            pass
                        else:
                            raise Exception(f"Failed to get data, status code: {response.status}")
                elif method == "post":
                    async with session.post(url, headers=headers, json=data, timeout=100) as response:
                        logging.debug(f"CustomCharAI.py: Async post request: {url}")
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 400:
                            pass
                        else:
                            raise Exception(f"Failed to get data, status code: {response.status}")
                elif method == "put":
                    async with session.put(url, headers=headers, json=data, timeout=100) as response:
                        logging.debug(f"CustomCharAI.py: Async put request: {url}")
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 400:
                            pass
                        else:
                            raise Exception(f"Failed to get data, status code: {response.status}")
                else:
                    raise ValueError("Invalid method")

    async def custom_request(self, url, data = None, method = "get"):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.auth_cookie}"
        }

        async with aiohttp.ClientSession() as session:
            if method == "get":
                async with session.get(url, headers=headers, params=data, timeout=10) as response:
                    logging.debug(f"CustomCharAI.py: Async get request: {url}")
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status}")
            elif method == "post":
                async with session.post(url, headers=headers, json=data, timeout=10) as response:
                    logging.debug(f"CustomCharAI.py: Async post request: {url}")
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get data, status code: {response.status}")
            else:
                raise ValueError("Invalid method")

    async def get_character(self, character_id):
        response = await self.trpc_request(
            f"character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22{character_id}%22%7D%7D%7D")
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

    async def get_main_page_chats(self, short_lang):
        response = await self.trpc_request(
            f"discovery.recommended,discovery.curatedLists,discovery.recommended,character.infos?batch=1&input={{%220%22:{{%22json%22:{{%22lang%22:%22{short_lang}%22}}}},%221%22:{{%22json%22:{{%22listIds%22:[%22cold_start_popular_characters_l30d_v1%22,%22cold_start_trending_characters_v1%22]}}}},%222%22:{{%22json%22:{{%22lang%22:%22{short_lang}%22}}}},%223%22:{{%22json%22:{{%22externalIds%22:[%22q0KukI6MnGQm_vDr9tG8YIyBJr8pNs8Wf6eKGh_yldw%22,%22edOuK6q8jN1kbv_QXnx25gfqpL0k0v2ByTbET5HCsgs%22,%22o6GGF93x8zFmPL1f2lT7d0iRhRZquc1x6h4KJ00g9Ck%22,%22U0UEmkGE3HBSuZAXchwcwO4HDWwPV8qhlsmO38YkO3k%22,%22DI1yer-gTAG_SvdxR-bu23eCCz4BMgsLTKp-NJ0vV3s%22,%22H4Y7Db2ALtZCm2yI8Ai9TT_hjyskGASBgKy6VSxhtak%22,%225MNwesgXRtUm0is6KXZ7ii2U0aaopVDyGa1N5-DwHrc%22,%228wk86EGdQ7LLbu8I1nadKL1giiYGLfE4DaryTdSyv9w%22,%22VAe__mrIOgaos1AgKQqTLe2lbe3E1JU8WXmTWxm45gw%22,%22EeNI0LbMJXSNUrlFaaAmEq5OfVXMY73A_GplJtGZ-pU%22,%22QD9um3txuc-oDVMmMB3rg9KFzmYR_JBMo8wEVwPDlRE%22,%22gFWL2jo3N1FHiLihknz1f_nwFBq6xBiAdGyuSmw_cTc%22,%22JzdwtXZNEqHoSsVf8sQ2P26WZRv7f_IQGSWZQAcT3pY%22,%22n3xkV_EptnZ0euflSos8Ylq_corcjZfaYEcfSOmu9to%22,%22f3vvWne0fuUL20eHVNRjAxk1a0CzbtjA6sFlgIU6p2g%22,%22VAxMSGSUghPurx28geTtgXWZYbm07vX7kGKJlaKw4Vg%22]}}}}}}")
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
        return response.get("user", None).get("user", None)

    async def get_user(self, username):
        response = await self.trpc_request(f"social.publicProfile?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22username%22%3A%22{username}%22%7D%7D%7D")
        return response[0].get("result", {}).get("data", {}).get("json", {})

    async def get_user_settings(self):
        response = await self.request("chat/user/settings", text=True)
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

    async def get_following(self, pageParam="", username=""):
        data = {}
        if pageParam and username:
            data = {
                "pageParam": pageParam,
                "username": username
            }
        response = await self.request("chat/user/public/following/", data, "post")
        return response

    async def get_followers(self, pageParam="", username=""):
        data = {}
        if pageParam and username:
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

class ChatClient:
    def __init__(self, token: str = ""):
        self.token = token
        self.ws = None

    async def __aenter__(self):
        cookie = f'HTTP_AUTHORIZATION="Token {self.token}"'
        try:
            self.ws = await websockets.connect(
                'wss://neo.character.ai/ws/',
                extra_headers={'Cookie': cookie}
            )
        except exceptions.InvalidStatusCode as e:
            if e.status_code == 403:
                raise Exception('Invalid token')
            else:
                raise e
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        if self.ws:
            await self.ws.close()

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

        await self.ws.send(json.dumps(payload))
        response = json.loads(await self.ws.recv())

        if 'chat' not in response:
            raise Exception(response['comment'])

        answer = json.loads(await self.ws.recv())['turn']
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

        await self.ws.send(json.dumps(message))

        async def response_stream():
            while True:
                response = json.loads(await self.ws.recv())

                if 'turn' not in response:
                    raise Exception(response['comment'])

                yield response

        async for result in response_stream():
            yield result

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

        await self.ws.send(json.dumps(message))

        async def response_stream():
            while True:
                response = json.loads(await self.ws.recv())

                if 'turn' not in response:
                    raise Exception(response['comment'])

                yield response

        async for result in response_stream():
            yield result

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
        await self.ws.send(json.dumps(payload))
        response = json.loads(await self.ws.recv())
        if 'turn' not in response:
            raise Exception(response['comment'])
        return response['turn']
