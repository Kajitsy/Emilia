import logging, asyncio, inspect, json, re, uuid

import curl_cffi.curl
from PyQt6.QtCore import QThread, pyqtSignal, QLocale
from gpytranslate import Translator
from functools import wraps

from modules.logic.VTubeCore import EEC

def asyncSlot(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.ensure_future(func(*args, **kwargs))
    return wrapper

class ChatThread(QThread):
    finished = pyqtSignal(object)
    connected_signal = pyqtSignal(bool)
    user_message_signal = pyqtSignal(object)
    message_signal = pyqtSignal(object)
    turn_remove_signal = pyqtSignal(object)
    turn_regenerate_signal = pyqtSignal(object, object, object)
    new_chat_created_signal = pyqtSignal(object)
    chat_signal = pyqtSignal(object)
    get_history_signal = pyqtSignal(object, str)
    get_char_signal = pyqtSignal(object)
    get_recommend_chars_by_id_signal = pyqtSignal(object)
    get_chat_by_id_signal = pyqtSignal(object)
    get_me_signal = pyqtSignal(object)
    get_user_settings_signal = pyqtSignal(object)
    update_user_settings_signal = pyqtSignal(object)
    update_user_settings_2_signal = pyqtSignal(object)
    get_available_models_signal = pyqtSignal(object)
    get_available_models_git_signal = pyqtSignal(object)
    get_user_signal = pyqtSignal(object)
    hide_chat_signal = pyqtSignal(object)

    query_autocomplete_signal = pyqtSignal(object)
    character_search_signal = pyqtSignal(object)
    scene_search_signal = pyqtSignal(object)
    user_search_signal = pyqtSignal(object)

    recent_chats_signal = pyqtSignal(object)
    get_main_page_chats_signal = pyqtSignal(object)
    featured_chats_signal = pyqtSignal(object)
    trythis_chats_signal = pyqtSignal(object)
    category_characters_signal = pyqtSignal(object)
    character_chats_signal = pyqtSignal(object)
    copy_chat_signal = pyqtSignal(object)

    character_vote_signal = pyqtSignal(object)
    user_follow_signal = pyqtSignal(object)
    user_unfollow_signal = pyqtSignal(object)
    user_following_signal = pyqtSignal(object)
    user_followers_signal = pyqtSignal(object)
    me_following_signal = pyqtSignal(object)
    upload_avatar_signal = pyqtSignal(object)
    upload_image_signal = pyqtSignal(object)
    get_upvoted_characters_signal = pyqtSignal(list)
    create_character_signal = pyqtSignal(object)
    update_character_signal = pyqtSignal(object)
    get_user_personas_signal = pyqtSignal(list)
    create_persona_signal = pyqtSignal(object)
    update_persona_signal = pyqtSignal(object)
    remove_persona_signal = pyqtSignal(object)

    get_scene_signal = pyqtSignal(object)
    create_scene_signal = pyqtSignal(object)
    update_scene_signal = pyqtSignal(object)
    remove_scene_signal = pyqtSignal(object)

    join_or_create_session_signal = pyqtSignal(object)

    get_scenes_curated_signal = pyqtSignal(object)
    get_scene_by_id_signal = pyqtSignal(object)
    get_scenes_by_user_signal = pyqtSignal(object)

    voices_search_signal = pyqtSignal(object)
    voices_search_username_signal = pyqtSignal(object)
    featured_voices_signal = pyqtSignal(object)
    replay_signal = pyqtSignal(object)
    edit_message_signal = pyqtSignal(object)
    get_voice_signal = pyqtSignal(object)
    voice_override_signal = pyqtSignal(object)
    voice_override_update_signal = pyqtSignal(object)
    voice_override_delete_signal = pyqtSignal(object)
    recognize_speech_signal = pyqtSignal(object)

    vtube_connect_signal = pyqtSignal(object)
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.token: str | None = None
        self.cookie: str | None = None
        self.session = curl_cffi.AsyncSession()
        self.connect = None
        self.ws = None
        self.me = {}
        self.eec = EEC(self.mw, self.mw.settings.value("vtube/address", "127.0.0.1"), self.mw.settings.value("vtube/port", 8001))

        self.microphone_muted = True
        self.voiced = False
        self.lang = QLocale.system().name().split('_')[0]
        self.translator = Translator()

        self.chat_histories = {}
        self.chat_next_tokens = {}
        self.category_characters = {}
        self.characters = {}
        self.users = {}
        self.similar_characters = {}

    def _get_headers(self, additional=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0"
        }
        if additional:
            headers.update(additional)
        return headers

    async def _make_request(self, method, url, headers, data=None, json_data=None, return_text=False):
        """Централизованный метод запросов с обработкой ошибок"""
        try:
            response = await self.session.request(method, url, headers=headers, data=data, json=json_data, timeout=100)
            logging.debug(f"Req: {url} [{response.status_code}]")

            if response.status_code in [200, 207, 400]:
                return response.json() if not return_text else json.loads(response.text)
            else:
                logging.error(f"Request failed: {url} - {response.status_code}")
                return {"error": True, "status": response.status_code}
        except Exception as e:
            logging.error(f"Async request error ({url}): {e}")
            raise

    async def request(self, endpoint, data={}, method="GET", domain="neo", text=False):
        headers = self._get_headers()
        base_urls = {
            "neo": "https://neo.character.ai/",
            "trpc": "https://character.ai/api/trpc/",
            "plus": "https://plus.character.ai/",
        }
        base_url = base_urls.get(domain, "https://plus.character.ai/")
        url = f"{base_url}{endpoint}"

        if method.lower() in ("post", "put", "patch"):
            kwargs = {"json_data": data}
        else:
            kwargs = {"data": data}

        return await self._make_request(method, url, headers, return_text=text, **kwargs)

    async def custom_request(self, url, data={}, method="get", text=False, headers={}):
        kwargs = {"json_data": data} if method.lower() == "post" else {"data": data}
        return await self._make_request(method, url, headers, return_text=text, **kwargs)

    @asyncSlot
    async def create_connect(self):
        if self.ws and not self.ws.closed:
            return self.ws
        try:
            self.ws = await self.session.ws_connect(
                'wss://neo.character.ai/ws/',
                cookies={'HTTP_AUTHORIZATION': f'Token {self.token}'},
                autoclose=False
            )
            return self.ws
        except Exception as e:
            logging.error(f"WebSocket connection failed: {e}")
            return None

    @asyncSlot
    async def check_vtube_connect(self):
        try:
            await self.eec.connect()
            self.vtube_connect_signal.emit(self.tr("Successful connection!"))
            await self.eec.close()
        except Exception as e:
            self.vtube_connect_signal.emit(self.tr("Connection error: ") + str(e))
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): VTube Check Error: {e}")

    def set_token(self, token):
        self.token = token

    def set_cookie(self, cookie):
        self.cookie = cookie

    async def _send_message(self, char: str, chat_id: str, text: str, author: dict = {}, attachments: list = []):
        message = {
            'command': 'create_and_generate_turn',
            'payload': {
                'attachments': attachments,
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

    @asyncSlot
    async def send_message(self, char, chat_id, text, tts_enabled=False, voice_id="", attachments=[]):
        used_emotes = []
        vtube_studio = self.mw.settings.value("vtube/use", False, type=bool)
        if vtube_studio:
            await self.eec.connect()
            await self.eec.UseEmote("Thinks")
            used_emotes.append("Thinks")
        if self.mw.settings.value("tr_user_msg", False, type=bool):
            translation = await self.translator.translate(text, targetlang=self.mw.settings_page.languages.get(self.mw.settings.value("tr_user_msg_to", "en_US"))['google_code'])
            text = translation.text
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The translator is used on user message")
        while True:
            if self.ws:
                try:
                    async for response in self._send_message(char, chat_id, text, attachments=attachments):
                        if response['turn']['author']['author_id'].isdigit() and response['turn']['author']['is_human']:
                            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The message has been sent")
                            self.chat_histories.get(chat_id, []).append({
                                'author': {
                                    'is_human': True
                                },
                                'candidates': [{
                                    'raw_content': text,
                                    'is_final': True
                                }],
                                'turn_key': {
                                    'chat_id': chat_id,
                                    'turn_id': response['turn']['turn_key']['turn_id']
                                }
                            })
                            self.user_message_signal.emit(response)
                        if vtube_studio and "Says" not in used_emotes:
                            await self.eec.UseEmote("Says")
                            used_emotes.append("Says")
                        if not response['turn']['author']['author_id'].isdigit():
                            if response.get('turn', {}).get('candidates', [])[0].get('is_final'):
                                if tts_enabled:
                                    char_name = ""
                                    if self.characters.get(char, {}):
                                        char_name = self.characters[char]['character']['name']
                                    await self.replay(response['turn']['primary_candidate_id'], chat_id, response['turn']['turn_key']['turn_id'], voice_id, char_name)
                                self.chat_histories.get(chat_id, []).append({
                                    'author': {
                                        'is_human': False
                                    },
                                    'candidates': [{
                                        'raw_content': response['turn']['candidates'][0]['raw_content'],
                                        'is_final': True
                                    }],
                                    'turn_key': {
                                        'chat_id': chat_id,
                                        'turn_id': response['turn']['turn_key']['turn_id']
                                    }
                                })
                                if self.mw.settings.value("tr_char_msg", False, type=bool):
                                    translation = await self.translator.translate(response['turn']['candidates'][0]['raw_content'], targetlang=self.mw.settings_page.languages.get(self.mw.settings.value("tr_char_msg_to", self.mw.current_language))['google_code'])
                                    response['turn']['candidates'][0]['raw_content'] = translation.text
                                    logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The translator is used on character message")

                                self.message_signal.emit(response)
                                logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The message has been received in full")
                                await self.request(f"chat/{chat_id}/resurrect", method="get", domain="neo")
                                return
                            self.message_signal.emit(response)
                            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The message has been updated")
                except curl_cffi.curl.CurlError:
                    self.ws = self.create_connect()
                    logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Reconnecting to websockets...")

    @asyncSlot
    async def edit_message(self, chat_id: str, turn_id: str, text: str):
        payload = {
            'command': 'edit_turn_candidate',
            'payload': {
                'turn_key': {
                    'chat_id': chat_id,
                    'turn_id': turn_id
                },
                'new_candidate_raw_content': text
            }
        }
        await self.ws.send_str(json.dumps(payload))

        while True:
            response = json.loads((await self.ws.recv_str()))
            if 'turn' not in response:
                raise Exception(response['comment'])
            if response['command'] == 'update_turn':
                turn = response.get("turn", {})
                pci = turn.get('primary_candidate_id')

                current = ""
                current_id = ""
                for candidate in turn.get('candidates', []):
                    if candidate.get('candidate_id') == pci:
                        current = candidate.get('raw_content', '')
                        current_id = candidate.get('candidate_id')
                        break

                history = self.chat_histories.get(chat_id, [])
                for message in history:
                    if message.get('turn_key', {}).get('turn_id') == turn_id:
                        message['candidates'][0]['raw_content'] = current
                        message['candidates'][0]['candidate_id'] = current_id
                        message['primary_candidate_id'] = pci
                        break

                self.edit_message_signal.emit(response)
            else:
                pass

    @asyncSlot
    async def turn_remove(self, chat_id, turn_ids):
        data = {"turn_ids": turn_ids}
        response = await self.request(f"turns/{chat_id}/remove", data, "post", "neo")
        self.turn_remove_signal.emit(response)
        for i, turn in enumerate(self.chat_histories.get(chat_id, [])):
            if turn.get('turn_key', {}).get('turn_id') in turn_ids:
                del self.chat_histories[chat_id][i]

    async def _generate_turn_candidate(self, char: str, chat_id: str, turn_id: str, user_name: str = ""):
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


    @asyncSlot
    async def turn_regenerate(self, char, chat_id, turn_id, user_name="", tts_enabled=False, voice_id=""):
        used_emotes = []
        message_bubble_added = False
        vtube_studio = self.mw.settings.value("vtube/use", False, type=bool)
        logging.debug(f'QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Message Regeneration')
        if vtube_studio:
            await self.eec.connect()
            await self.eec.UseEmote("Thinks")
            used_emotes.append("Thinks")
        if self.ws:
             while True:
                try:
                    async for response in self._generate_turn_candidate(char, chat_id, turn_id, user_name):
                        if vtube_studio and "Says" not in used_emotes:
                            logging.debug(f'QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The emotion "Says" is used')
                            await self.eec.UseEmote("Says")
                            used_emotes.append("Says")
                        if not response['turn']['author']['author_id'].isdigit():
                            if response.get('turn', {}).get('candidates', [])[0].get('is_final'):
                                if tts_enabled:
                                    char_name = ""
                                    if self.characters.get(char, {}):
                                        char_name = self.characters[char]['character']['name']
                                    await self.replay(response['turn']['primary_candidate_id'], chat_id,
                                                      response['turn']['turn_key']['turn_id'], voice_id, char_name)
                                self.chat_histories.get(chat_id, []).append({
                                    'author': {
                                        'is_human': False
                                    },
                                    'candidates': [{
                                        'raw_content': response['turn']['candidates'][0]['raw_content'],
                                        'is_final': True
                                    }],
                                    'turn_key': {
                                        'chat_id': chat_id,
                                        'turn_id': response['turn']['turn_key']['turn_id']
                                    }
                                })
                                if self.mw.settings.value("tr_char_msg", False, type=bool):
                                    translation = await self.translator.translate(
                                        response['turn']['candidates'][0]['raw_content'], targetlang=
                                        self.mw.settings_page.languages.get(
                                            self.mw.settings.value("tr_char_msg_to", self.mw.current_language))[
                                            'google_code'])
                                    response['turn']['candidates'][0]['raw_content'] = translation.text
                                    logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The translator is used on character message")

                                self.turn_regenerate_signal.emit(response, turn_id, message_bubble_added)
                                logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The message has been received in full")
                                await self.request(f"chat/{chat_id}/resurrect", method="get", domain="neo")
                                return
                            self.turn_regenerate_signal.emit(response, turn_id, message_bubble_added)
                            message_bubble_added = True
                            turn_id = response['turn']['turn_key']['turn_id']
                            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The message has been updated")
                except curl_cffi.curl.CurlError:
                    self.ws = self.create_connect()
                    logging.warning(f"QThreads.py: ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}) Reconnecting to websockets...")

    @asyncSlot
    async def replay(self, candidateId, roomId, turnId, voiceId="", voiceQuery=""):
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
        response = await self.request("multimodal/api/v1/memo/replay", data, "post", domain="neo")
        self.replay_signal.emit(response)

    @asyncSlot
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
        self.join_or_create_session_signal(response)

    @asyncSlot
    async def get_me(self):
        response = await self.request("user/", domain="neo")
        self.me = response.get("user", {})
        self.get_me_signal.emit(self.me)
        return self.me

    @asyncSlot
    async def get_user_settings(self):
        response = await self.request("chat/user/settings/", domain="plus")
        self.get_user_settings_signal.emit(response)

    @asyncSlot
    async def update_user_settings(self, data):
        response = await self.request("chat/user/update_settings/", data, "post")
        self.update_user_settings_signal.emit(response)

    @asyncSlot
    async def update_user_settings_2(self, data):
        response = await self.request("chat/user/update/", data, "post")
        self.update_user_settings_2_signal.emit(response)

    @asyncSlot
    async def get_user(self, username):
        if not username in self.users:
            response = await self.request(f"social.publicProfile?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22username%22%3A%22{username}%22%7D%7D%7D",
                                          domain="trpc")
            self.users[username] = response[0].get("result", {}).get("data", {}).get("json", {})
        self.get_user_signal.emit(self.users[username])

    @asyncSlot
    async def new_chat(self, char, chat_id = None, preferred_model_type = "MODEL_TYPE_BALANCED", scene_id = ""):
        if not self.me:
            self.me = self.get_me()
        if self.ws:
            while True:
                try:
                    chat_id = str(uuid.uuid4())

                    payload = {
                        'command': 'create_chat',
                        'payload': {
                            'chat': {
                                'character_id': char,
                                'chat_id': chat_id,
                                'creator_id': str(self.me['user']['id']),
                                'preferred_model_type': preferred_model_type,
                                'type': 'TYPE_ONE_ON_ONE',
                                'visibility': 'VISIBILITY_PRIVATE'
                            },
                            'with_greeting': True
                        }
                    }

                    if scene_id:
                        payload['payload']['chat']['scene_id'] = scene_id

                    await self.ws.send_str(json.dumps(payload))

                    while True:
                        response = json.loads((await self.ws.recv_str()))
                        if response['command'] == 'create_chat_response':
                            if chat_id and chat_id in self.chat_histories: del self.chat_histories[chat_id]
                            self.new_chat_created_signal.emit(response)
                        elif response['command'] == 'add_turn':
                            break
                        else:
                            raise Exception(response.get('comment', 'Unknown error'))
                        logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): New chat started")
                    break
                except curl_cffi.curl.CurlError:
                    self.ws = self.create_connect()
                    logging.warning(f"QThreads.py: ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}) Reconnecting to websockets...")

    @asyncSlot
    async def get_chat(self, character_id):
        response = await self.request(f"chats/recent/{character_id}", domain="neo")
        self.chat_signal.emit(response.get("chats", []))

    @asyncSlot
    async def get_chat_by_id(self, chat_id, load_metadata=False):
        response = await self.request(f"chat/{chat_id}/?load_metadata={load_metadata}", domain="neo")
        self.get_chat_by_id_signal.emit(response)

    @asyncSlot
    async def get_available_models(self):
        response = await self.request(f"get-available-models", domain="neo")
        self.get_available_models_signal.emit(response.get('available_models', []))

    @asyncSlot
    async def get_available_models_git(self):
        response = await self.custom_request("https://raw.githubusercontent.com/Kajitsy/Emilia/refs/heads/emilia/data/CAI_Available_Models.json",
                                            text=True)
        self.get_available_models_git_signal.emit(response)

    @asyncSlot
    async def copy_chat(self, chat_id, end_turn_id):
        data = {
            "end_turn_id": end_turn_id
        }
        response = await self.request(f"chat/{chat_id}/copy", data, "post", domain="neo")
        self.copy_chat_signal.emit(response)

    @asyncSlot
    async def hide_chat(self, character_id):
        response = await self.request(f"chats/recent/{character_id}/hide", method="put", domain="neo")
        self.hide_chat_signal.emit(response)

    @asyncSlot
    async def get_history(self, chat_id, next_tokenq=None):
        if next_tokenq or not chat_id in self.chat_histories:
            url = f"turns/{chat_id}"
            if next_tokenq: url += f"?next_token={next_tokenq}"
            response = await self.request(url, domain="neo")
            chat = response.get("turns", [])
            next_token = response.get("meta", {}).get("next_token", "")
            if next_tokenq:
                new_chat_history = []
                for i in list(reversed(chat)):
                    new_chat_history.append(i)
                if self.chat_histories.get(chat_id):
                    for i in self.chat_histories[chat_id]:
                        new_chat_history.append(i)
                self.chat_histories[chat_id] = new_chat_history
            else:
                self.chat_histories[chat_id] = list(reversed(chat))
            self.chat_next_tokens[chat_id] = {"token": next_token}
        self.get_history_signal.emit(self.chat_histories[chat_id], self.chat_next_tokens.get(chat_id, {}).get('token'))

    @asyncSlot
    async def get_recent_chats(self):
        response = await self.request(f"chats/recent", domain="neo")
        self.recent_chats_signal.emit(response.get('chats', []))

    @asyncSlot
    async def get_featured_voices(self):
        response = await self.request("multimodal/api/v1/voices/featured", domain="neo")
        self.featured_voices_signal.emit(response.get("voices", []))

    @asyncSlot
    async def get_scenes_curated(self):
        response = await self.request("scene/v1/scenes/curated", domain="neo")
        self.get_scenes_curated_signal.emit(response.get("scenes", []))

    @asyncSlot
    async def get_scene_by_id(self, scene_id):
        response = await self.request(f"scene/v1/scenes/{scene_id}", domain="neo")
        self.get_scene_by_id_signal.emit(response.get("scene", {}))

    @asyncSlot
    async def get_scenes_by_user(self, username):
        response = await self.request(f"scene/v1/scenes?creator_username={username}", domain="neo")
        self.get_scenes_by_user_signal.emit(response.get("scenes", []))

    @asyncSlot
    async def get_trythis_chats(self):
        response = await self.request("character.info,character.info,character.info,character.info,character.info,character.info,character.info,character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22A9zlEuzpvWiH8h0PNWEvZPK-PQifYxS-V24D3ncqIyU%22%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22uD71krOYYFjVkYwspviH_8tYTybsf5eAGdwhNlFJAls%22%7D%7D%2C%222%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22f4hEGbw8ywUrjsrye03EJxiBdooy--HiOWgU2EiRJ0s%22%7D%7D%2C%223%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229ZSDyg3OuPbFgDqGwy3RpsXqJblE4S1fKA_oU3yvfTM%22%7D%7D%2C%224%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22Hu84TYGgte3qVoQuy75x6Q1-ORjQbgoe2qaFoTkjaOM%22%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22_FrgO6M-xCuTi72BYHbt-dQN2QsjNXnl-eKJGrjJttc%22%7D%7D%2C%226%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22WLcau8HDbkAPlnU9GPZvLVQ4QaWMhktCmgGFgG2nb5c%22%7D%7D%2C%227%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229wIR0NXzqD76sfJWRsHCGGb8IkPljhINj8WDy_2xjcg%22%7D%7D%2C%228%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%226HhWfeDjetnxESEcThlBQtEUo0O8YHcXyHqCgN7b2hY%22%7D%7D%7D",
                                      domain="trpc")
        res_data = []
        for i in response:
            res_data.append(i.get('result', {}).get("data", {})['json']['character'])
        self.trythis_chats_signal.emit(res_data)

    @asyncSlot
    async def get_category_characters(self, category):
        if not self.category_characters.get(category, []):
                response = await self.request(f"recommendation/v1/characters_with_tag/{category.replace(' ', '%20').replace('&', '%26')}",
                                              domain="neo")
                self.category_characters[category] = response.get("characters", [])[:20]
        self.category_characters_signal.emit(self.category_characters.get(category, {}))

    @asyncSlot
    async def get_character_chats(self, character_id, num_preview_turns=1):
        response = await self.request(f"chats/?character_ids={character_id}&num_preview_turns={num_preview_turns}",
                                      domain="neo")
        self.character_chats_signal.emit(response.get("chats", []))

    @asyncSlot
    async def get_main_page_chats(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.cookie}"
        }
        main_page_chats = await self.request(f"character.infos,discovery.curatedLists,character.info,character.info,character.info,character.info,character.info,character.info,character.info,character.info,discovery.curatedCategories,discovery.charactersByCurated,character.info,character.info,character.info,character.info,character.info,character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalIds%22%3A%5B%22OtlDvgun8lLEEI3mXxVhl7_e8ArdmnuHa-hKeFKxjSI%22%2C%221his4cFt1rPawY6N01u5p5CM_4BbWJM3A-RVHwuSnRI%22%2C%22BQShAudovnnwL0rWwNzPzpn1cg_MQm3C3yPvUVuVvfU%22%2C%22Alp8ttiB1mOVF937d_b0hix2ToM3npDijaXRwA_7PY0%22%2C%22roqeHT1P5--gMOjrHEjE7z1PJ6sAXRYVcpLI6MYRemA%22%2C%22q0akobJPMxSgums8Z1GsVmsr498Zm7YtxRpKVS_iUl0%22%2C%22sv54nR1qDnJaS5Zf8Yxze-rrCGKSEMZUKg4Ui-azMk4%22%2C%22T-Vpx4MmCwvlb0PG_TkjBhGdpDWAhPVIRRk5E-eeEl4%22%2C%222gzUbuu3eznfsZMG6g6VxuyAoY_qGRUE22DNa399_I0%22%2C%22xAB0gj88bLy0lng4wcNPn1RAwQ51mHv03Uzqfus-Epk%22%2C%22m0kuZJY-9lFmEydDwmX1ea8pROEffyRjty4a_9xy2EI%22%2C%22uA2zSUxOzrsIKJKTzZZRA9AL6M5D1CShe8RAZns91As%22%2C%22LNb8DCj6vQ2Z1d3ok111bxoxpRVqqeP9drQd7IL3BGg%22%2C%22zWgJMRcp2Q_9fWfY4uBgLfQb9iDTPXyGGlSmSyOABe4%22%2C%22fvdCvTk3AAVeW-h3y4a9_ajfbIo1_1jdughy1VQJ0-8%22%2C%22ADisxXRP6TgrjJ-9M04m1ctHCeLTw-DPFUHJ1p-1Rqk%22%2C%22NayYpcaCSn8IkQBnES0UcFH-2unn48_i39iiVmAzAIc%22%2C%22wbcZlYilRx1ep5_L01aFB6-g0PPqbxHi_O4RsFNbOtw%22%2C%22FeXcfHZPzoStZCwqcqpf-wO-yCxsA-MGToRoipKfvzA%22%2C%22ZVHoWO767A7mR4DHHtum7J-l8tMFwY-NRbAy1S8ub4c%22%2C%22v-GVsCZOUNU5-Xovuji14m16qCjGW-96UIBZhyTP3do%22%2C%22dAPSIb3xavyQ-aO4Q0BxmUBXqHqaoktxr_l2rbRgccc%22%2C%22W3IC9o8l8Cbjep8pskXpbjwRn7huVkBM4GzzaxtLTaw%22%2C%22i-mYsXbuRSyYpsPivuFhjDCy9EcMBBi-uPLzER63E4c%22%2C%22DlqmValOtaDUVyYCbb-krx7PRdAQUiagFodPkpDtwTw%22%2C%22mXNjk1FpX06Nkjv4D0zyIKW2vJnxNnatiXr8chdN9Yc%22%5D%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22listIds%22%3A%5B%22cold_start_popular_characters_l30d_v1%22%2C%22cold_start_trending_characters_v1%22%5D%7D%7D%2C%222%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22A9zlEuzpvWiH8h0PNWEvZPK-PQifYxS-V24D3ncqIyU%22%7D%7D%2C%223%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22uD71krOYYFjVkYwspviH_8tYTybsf5eAGdwhNlFJAls%22%7D%7D%2C%224%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22f4hEGbw8ywUrjsrye03EJxiBdooy--HiOWgU2EiRJ0s%22%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229ZSDyg3OuPbFgDqGwy3RpsXqJblE4S1fKA_oU3yvfTM%22%7D%7D%2C%226%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22Hu84TYGgte3qVoQuy75x6Q1-ORjQbgoe2qaFoTkjaOM%22%7D%7D%2C%227%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22_FrgO6M-xCuTi72BYHbt-dQN2QsjNXnl-eKJGrjJttc%22%7D%7D%2C%228%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22WLcau8HDbkAPlnU9GPZvLVQ4QaWMhktCmgGFgG2nb5c%22%7D%7D%2C%229%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%229wIR0NXzqD76sfJWRsHCGGb8IkPljhINj8WDy_2xjcg%22%7D%7D%2C%2210%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%2211%22%3A%7B%22json%22%3A%7B%22category%22%3A%22Helpers%22%7D%7D%2C%2212%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22W4MWmsvbFFnKF8b9e3Eg6ZUNzdhqvEZYy-tNRtxB_Og%22%7D%7D%2C%2213%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22GxP9L6QQ-qocxM9sYfvwywDw6wwfSmBJUjalAlD1ZCY%22%7D%7D%2C%2214%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%226HhWfeDjetnxESEcThlBQtEUo0O8YHcXyHqCgN7b2hY%22%7D%7D%2C%2215%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%227yDt2WH6Y_OpaAV4GsxKcY5xIQ8QT5M0kgpDQ6VAflI%22%7D%7D%2C%2216%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22YntB_ZeqRq2l_aVf2gWDCZl4oBttQzDvhj9cXafWcF8%22%7D%7D%2C%2217%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22YpuGnNPQiGvb0DIg77pDUruORvqEPQAxmabNuOIGylo%22%7D%7D%7D",
                                             domain="trpc")
        response_for_you_chats = await self.custom_request("https://feed.api.character.ai/api/feed/recommended", method='post',
                                             headers=headers)
        self.get_main_page_chats_signal.emit(main_page_chats)
        self.featured_chats_signal.emit(response_for_you_chats.get('contents', []))

    @asyncSlot
    async def get_character(self, character_id=None, path=None):
            if path and not character_id:
                headers = {
                    "Cookie": f"web-next-auth={self.cookie}"
                }
                match = re.match(r"^/character/([^/]+)(?:/([^/]+))?$", path)
                id_part = match.group(1)
                slug_part = match.group(2)

                if slug_part:
                    url = f"character/{id_part}/{slug_part}.json?id={id_part}&slug={slug_part}"
                else:
                    url = f"character/{id_part}.json?id={id_part}"
                response = await self.session.request("GET",
                                                      f"https://character.ai/_next/data/bP2i_9D3c_KrZ-_24-fQR/{url}",
                                                      headers=headers, timeout=100)
                pattern = re.compile(
                    r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*(\{.+?\})\s*</script>',
                    re.DOTALL
                )
                m = pattern.search(response.text)
                if m:
                    character_id = json.loads(m.group(1)).get('props', {}).get("pageProps", {}).get(
                        "prefetchedCharacterInfo", {}).get('external_id')
                else:
                    character_id = None

            if not character_id in self.characters:
                response = await self.request(f"character.info?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22externalId%22%3A%22{character_id}%22%7D%7D%7D", domain="trpc")
                character = response[0].get("result", {}).get("data", {}).get("json", {}).get("character", {})
                voted = await self.request(f"character/v1/character_voted/{character_id}/voted", method="get", domain="neo")
                headers = {
                    "Cookie": f"web-next-auth={self.cookie}"
                }
                response = await self.session.request("GET",f"https://character.ai/_next/data/bP2i_9D3c_KrZ-_24-fQR/chat/{character_id}.json?character={character_id}",headers=headers, timeout=100)
                pattern = re.compile(
                    r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*(\{.+?\})\s*</script>',
                    re.DOTALL
                )
                m = pattern.search(response.text)
                if m:
                    path = json.loads(m.group(1)).get('props', {}).get("pageProps", {}).get("characterPagePath")
                self.characters[character_id] = {
                    "character": character,
                    "voted": voted,
                    "path": path
                }
            self.get_char_signal.emit(self.characters[character_id])

    @asyncSlot
    async def get_recommend_chars_by_id(self, character_id):
        if not character_id in self.similar_characters:
            response = await self.request(f"recommendation/v1/character/similar/{character_id}", domain="neo")
            self.similar_characters[character_id] = response.get("characters", [])
        self.get_recommend_chars_by_id_signal.emit(self.similar_characters[character_id])

    @asyncSlot
    async def query_autocomplete(self, query_prefix):
        response = await self.request(f"search/v1/query/autocomplete?query_prefix={query_prefix}", method= "get", domain="neo")
        self.query_autocomplete_signal.emit(response.get('search_autocomplete', []))

    @asyncSlot
    async def get_user_following(self, pageParam=1, username=""):
        data = {"pageParam": pageParam, "username": username}
        response = await self.request("chat/user/public/following/", data, "post", "plus")
        self.user_following_signal.emit(response)

    @asyncSlot
    async def get_user_followers(self, pageParam=1, username=""):
        data = {"pageParam": pageParam, "username": username}
        response = await self.request("chat/user/public/followers/", data, "post", "plus")
        self.user_followers_signal.emit(response)

    @asyncSlot
    async def get_me_following(self):
        response = await self.request("chat/user/following/", method="get", domain="plus")
        self.me_following_signal.emit(response)

    @asyncSlot
    async def user_follow(self, username):
        data = {"username": username}
        response = await self.request("chat/user/follow/", data, "post", "plus")
        self.user_follow_signal.emit(response)

    @asyncSlot
    async def user_unfollow(self, username):
        data = {"username": username}
        response = await self.request("chat/user/unfollow/", data, "post")
        self.user_unfollow_signal.emit(response)

    @asyncSlot
    async def character_vote(self, character_id, vote):
        data = {"external_id": character_id, "vote": vote}
        response = await self.request("character/v1/vote_character", data, "post", "neo", text=True)
        self.character_vote_signal.emit(response)
        if vote == True:
            self.characters[character_id]['voted']['vote'] = True
            self.characters[character_id]['voted']['voted'] = True
        elif vote == False:
            self.characters[character_id]['voted']['vote'] = False
            self.characters[character_id]['voted']['voted'] = False
        elif vote == None:
            self.characters[character_id]['voted']['vote'] = None
            self.characters[character_id]['voted']['voted'] = False

    @asyncSlot
    async def character_search(self, query: str | None = None):
        response = await self.request(f"search.search?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{query}%22%7D%7D%7D",
                                      domain="trpc")
        self.character_search_signal.emit(response[0].get("result", {}).get("data", {}).get("json", []).get('characters', []))

    @asyncSlot
    async def scene_search(self, query: str | None = None):
        response = await self.request(f"search.searchScenes?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{query}%22%7D%7D%7D",
                                     domain="trpc")
        self.scene_search_signal.emit(response[0].get('result',{}).get('data', {}).get('json', {}).get('creators', []))

    @asyncSlot
    async def user_search(self, query: str | None = None):
        response = await self.request(
            f"search.searchCreators?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22searchQuery%22%3A%22{query}%22%2C%22sortedBy%22%3A%22relevance%22%7D%7D%7D",
            domain="trpc")
        self.user_search_signal.emit(response[0].get('result', {}).get('data', {}).get('json', {}).get('creators', []))

    @asyncSlot
    async def voices_search(self, query: str | None = None, character_name: str| None = None):
        url = "multimodal/api/v1/voices/search"
        if character_name: url += f"?characterName={character_name}"
        if query: url += f"?query={query}"
        response = await self.request(url, method="get", domain="neo")
        self.voices_search_signal.emit(response.get('voices', []))

    @asyncSlot
    async def voices_search_username(self, username: str | None = None):
        url = f"multimodal/api/v1/voices/search?creatorInfo.username={username}"
        response = await self.request(url, method="get", domain="neo")
        self.voices_search_username_signal.emit(response.get('voices', []))

    @asyncSlot
    async def get_voice(self, voice_id):
        response = await self.request(f"multimodal/api/v1/voices/{voice_id}", method="get", domain="neo")
        self.get_voice_signal.emit(response)

    @asyncSlot
    async def voice_override(self, character_id):
        response = await self.request(f"chat/character/{character_id}/voice_override/", method="get", domain="plus")
        self.voice_override_signal.emit(response)

    @asyncSlot
    async def voice_override_update(self, character_id, voice_id):
        data = {"voice_id": voice_id}
        response = await self.request(f"chat/character/{character_id}/voice_override/update/", data, "post", "plus")
        self.voice_override_update_signal.emit(response)

    @asyncSlot
    async def voice_override_delete(self, character_id):
        response = await self.request(f"chat/character/{character_id}/voice_override/delete/", method="post", domain="plus")
        self.voice_override_delete_signal.emit(response)

    @asyncSlot
    async def vtube_use_emote(self, emote):
        await self.eec.connect()
        await self.eec.UseEmote(emote)
        await self.eec.close()
        logging.debug(f'QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The emotion of "{emote}" was used')

    @asyncSlot
    async def get_upvoted_characters(self):
        response = await self.request("character/v1/upvoted_characters", method="get", domain="neo")
        self.get_upvoted_characters_signal.emit(response.get('characters', []))

    @asyncSlot
    async def create_character(self, data):
        response = await self.request("character/v1/create_character", data, "post", "neo")
        self.create_character_signal.emit(response)

    @asyncSlot
    async def update_character(self, data):
        result = await self.request("character/v1/update_character", data, "post", "neo")
        self.update_character_signal.emit(result)
        if data.get('status') == "OK":
            self.characters[result['character']['external_id']]['character'] = result['character']

    @asyncSlot
    async def get_user_personas(self, force_refresh=0):
        response = await self.request(f"character/v1/get_user_personas?force_refresh={force_refresh}", method="get",
                                      domain="neo")
        self.get_user_personas_signal.emit(response.get('personas', []))

    @asyncSlot
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
        response = await self.request("character/v1/create_persona", data, "post", "neo")
        self.create_persona_signal.emit(response.get('persona', {}))

    @asyncSlot
    async def update_persona(self, data):
        response = await self.request("character/v1/update_persona", data, "post", True)
        self.update_persona_signal.emit(response.get('persona', {}))

    @asyncSlot
    async def remove_persona(self, data):
        data['archived'] = True
        response = await self.request("character/v1/update_persona", data, "post", True)
        self.remove_persona_signal.emit(response)

    @asyncSlot
    async def get_scene(self, scene_id):
        response = await self.request(f"scene/v1/scenes/{scene_id}", method= "get", domain="neo")
        self.get_scene_signal.emit(response.get('scene', {}))

    @asyncSlot
    async def create_scene(self, data):
        response = await self.request("scene/v1/scenes", data, "post", "neo")
        self.create_scene_signal.emit(response.get('scene', {}))

    @asyncSlot
    async def update_scene(self, data, scene_id):
        response = await self.request(f"scene/v1/scenes/{scene_id}", data, "put", domain="neo")
        self.update_scene_signal.emit(response.get('scene', {}))

    @asyncSlot
    async def remove_scene(self, scene_id):
        response = await self.request(f"scene/v1/scenes/{scene_id}", method= "delete", domain="neo")
        self.remove_scene_signal.emit(response)

    @asyncSlot
    async def upload_avatar(self, filetype, image):
        data = {"0": {"json": {"imageDataUrl": f"data:image/{filetype};base64,{image}"}}}
        response = await self.request("user.uploadAvatar?batch=1", data, "post", "trpc")
        self.upload_avatar_signal.emit(response[0]['result']['data']['json'])

    @asyncSlot
    async def upload_image(self, multipart):
        headers = {
            "Content-Type": "multipart/form-data",
            "Authorization": f"Token {self.token}",
            "Cookie": f"web-next-auth={self.cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0"
        }

        response = await self.session.request("POST", "https://neo.character.ai/image/upload_private_image", headers=headers, multipart=multipart, timeout=100, impersonate="chrome")

        self.upload_image_signal.emit(response.json())
