import logging, asyncio
from functools import wraps
from PyQt6.QtCore import QThread, pyqtSignal, QLocale
from future.backports.urllib import response
from gpytranslate import Translator
import curl_cffi.curl

from modules.logic.VTubeCore import EEC

from modules.api import WSClient, CharacterAPI, ChatsAPI, EmiliaAPI, UsersAPI, VoicesAPI, ScenesAPI, CAILimitAPI

def asyncSlot(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.ensure_future(func(*args, **kwargs))

    return wrapper


class ChatThread(QThread):
    finished = pyqtSignal(object)
    notification_signal = pyqtSignal(str)

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

    get_voice_call_limit_signal = pyqtSignal(dict)
    get_chat_image_attachment_limit_signal = pyqtSignal(dict)

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

    get_update_servers_signal = pyqtSignal(object)
    get_themes_signal = pyqtSignal(object)
    get_user_themes_signal = pyqtSignal(object)
    get_theme_signal = pyqtSignal(object)
    download_theme_signal = pyqtSignal(object)
    upload_theme_signal = pyqtSignal(object)
    update_theme_signal = pyqtSignal(object)
    delete_theme_signal = pyqtSignal(object)

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

        self.client = WSClient()
        self.api_chars = CharacterAPI(self.client)
        self.api_chats = ChatsAPI(self.client)
        self.api_emilia = EmiliaAPI(self.client)
        self.api_cai_limit = CAILimitAPI(self.client)
        self.api_users = UsersAPI(self.client)
        self.api_voices = VoicesAPI(self.client)
        self.api_scenes = ScenesAPI(self.client)

        self.eec = EEC(self.mw, self.mw.settings.value("vtube/address", "127.0.0.1"),
                       self.mw.settings.value("vtube/port", 8001))

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
        self.me = {}
        self.current_limits = {}

    def set_token(self, token):
        self.client.set_token(token)

    def set_cookie(self, cookie):
        self.client.set_cookie(cookie)

    @asyncSlot
    async def create_connect(self):
        return await self.client.connect_ws()

    @asyncSlot
    async def check_vtube_connect(self):
        try:
            await self.eec.connect()
            self.vtube_connect_signal.emit(self.tr("Successful connection!"))
            await self.eec.close()
        except Exception as e:
            self.vtube_connect_signal.emit(self.tr("Connection error: ") + str(e))
            logging.debug(f"ChatThread: VTube Check Error: {e}")

    @asyncSlot
    async def vtube_use_emote(self, emote):
        await self.eec.connect()
        await self.eec.UseEmote(emote)
        await self.eec.close()
        logging.debug(f'ChatThread: The emotion "{emote}" was used')

    @asyncSlot
    async def send_message(self, char, chat_id, text, tts_enabled=False, voice_id="", attachments=None):
        used_emotes = []
        vtube_studio = self.mw.settings.value("vtube/use", False, type=bool)
        if attachments:
            count = self.current_limits.get('chat_image_attachment', {}).get('count_remaining', 0)
            if count >> 0:
                self.current_limits['chat_image_attachment']['count_remaining'] -= 1
            elif count == 0:
                self.notification_signal.emit(self.tr("Attached message limit exceeded"))
                attachments = None

        if vtube_studio:
            await self.eec.connect()
            await self.eec.UseEmote("Thinks")
            used_emotes.append("Thinks")

        if self.mw.settings.value("tr_user_msg", False, type=bool):
            lang_code = self.mw.settings_page.languages.get(self.mw.settings.value("tr_user_msg_to", "en_US"))[
                'google_code']
            translation = await self.translator.translate(text, targetlang=lang_code)
            text = translation.text

        while True:
            if self.client.ws:
                try:
                    async for response in self.client.send_message_stream(char, chat_id, text, attachments=attachments):
                        author = response['turn']['author']

                        if author['author_id'].isdigit() and author.get('is_human'):
                            self._append_to_history(chat_id, text, response['turn']['turn_key']['turn_id'], True)
                            self.user_message_signal.emit(response)

                        if vtube_studio and "Says" not in used_emotes:
                            await self.eec.UseEmote("Says")
                            used_emotes.append("Says")

                        if not author['author_id'].isdigit():
                            candidate = response.get('turn', {}).get('candidates', [{}])[0]
                            if candidate.get('is_final'):
                                if tts_enabled:
                                    char_name = self.characters.get(char, {}).get('character', {}).get('name', '')
                                    await self.replay(response['turn']['primary_candidate_id'], chat_id,
                                                      response['turn']['turn_key']['turn_id'], voice_id, char_name)

                                raw_content = candidate['raw_content']
                                self._append_to_history(chat_id, raw_content, response['turn']['turn_key']['turn_id'],
                                                        False)

                                if self.mw.settings.value("tr_char_msg", False, type=bool):
                                    lang_code = self.mw.settings_page.languages.get(
                                        self.mw.settings.value("tr_char_msg_to", self.mw.current_language))[
                                        'google_code']
                                    translation = await self.translator.translate(raw_content, targetlang=lang_code)
                                    response['turn']['candidates'][0]['raw_content'] = translation.text

                                self.message_signal.emit(response)
                                await self.client.request(f"chat/{chat_id}/resurrect", method="get", domain="neo")
                                return

                            self.message_signal.emit(response)
                except curl_cffi.curl.CurlError:
                    await self.client.connect_ws()
                    logging.warning("ChatThread: Reconnecting to websockets...")

    def _append_to_history(self, chat_id, text, turn_id, is_human):
        if chat_id not in self.chat_histories:
            self.chat_histories[chat_id] = []
        self.chat_histories[chat_id].append({
            'author': {'is_human': is_human},
            'candidates': [{'raw_content': text, 'is_final': True}],
            'turn_key': {'chat_id': chat_id, 'turn_id': turn_id}
        })

    @asyncSlot
    async def edit_message(self, chat_id: str, turn_id: str, text: str):
        response = await self.client.edit_message(chat_id, turn_id, text)

        turn = response.get("turn", {})
        pci = turn.get('primary_candidate_id')
        current, current_id = "", ""

        for candidate in turn.get('candidates', []):
            if candidate.get('candidate_id') == pci:
                current = candidate.get('raw_content', '')
                current_id = candidate.get('candidate_id')
                break

        for message in self.chat_histories.get(chat_id, []):
            if message.get('turn_key', {}).get('turn_id') == turn_id:
                message['candidates'][0]['raw_content'] = current
                message['candidates'][0]['candidate_id'] = current_id
                message['primary_candidate_id'] = pci
                break

        self.edit_message_signal.emit(response)

    @asyncSlot
    async def turn_regenerate(self, char, chat_id, turn_id, user_name="", tts_enabled=False, voice_id=""):
        used_emotes = []
        message_bubble_added = False
        vtube_studio = self.mw.settings.value("vtube/use", False, type=bool)

        if vtube_studio:
            await self.eec.connect()
            await self.eec.UseEmote("Thinks")
            used_emotes.append("Thinks")

        while True:
            if self.client.ws:
                try:
                    async for response in self.client.regenerate_turn_stream(char, chat_id, turn_id, user_name):
                        if vtube_studio and "Says" not in used_emotes:
                            await self.eec.UseEmote("Says")
                            used_emotes.append("Says")

                        if not response['turn']['author']['author_id'].isdigit():
                            candidate = response.get('turn', {}).get('candidates', [{}])[0]
                            if candidate.get('is_final'):
                                if tts_enabled:
                                    char_name = self.characters.get(char, {}).get('character', {}).get('name', '')
                                    await self.replay(response['turn']['primary_candidate_id'], chat_id,
                                                      response['turn']['turn_key']['turn_id'], voice_id, char_name)

                                raw_content = candidate['raw_content']
                                self._append_to_history(chat_id, raw_content, response['turn']['turn_key']['turn_id'],
                                                        False)

                                if self.mw.settings.value("tr_char_msg", False, type=bool):
                                    lang_code = self.mw.settings_page.languages.get(
                                        self.mw.settings.value("tr_char_msg_to", self.mw.current_language))[
                                        'google_code']
                                    translation = await self.translator.translate(raw_content, targetlang=lang_code)
                                    response['turn']['candidates'][0]['raw_content'] = translation.text

                                self.turn_regenerate_signal.emit(response, turn_id, message_bubble_added)
                                await self.client.request(f"chat/{chat_id}/resurrect", method="get", domain="neo")
                                return

                            self.turn_regenerate_signal.emit(response, turn_id, message_bubble_added)
                            message_bubble_added = True
                            turn_id = response['turn']['turn_key']['turn_id']
                except curl_cffi.curl.CurlError:
                    await self.client.connect_ws()
                    logging.warning("ChatThread: Reconnecting to websockets...")

    @asyncSlot
    async def new_chat(self, char, chat_id=None, preferred_model_type="MODEL_TYPE_BALANCED", scene_id=""):
        if not self.me:
            self.me = await self.api_users.get_me()

        while True:
            if self.client.ws:
                try:
                    response, new_chat_id = await self.client.create_new_chat(char, self.me.get('user', {}).get('id', ''),
                                                                              preferred_model_type, scene_id)
                    if new_chat_id and new_chat_id in self.chat_histories:
                        del self.chat_histories[new_chat_id]
                    self.new_chat_created_signal.emit(response)
                    break
                except curl_cffi.curl.CurlError:
                    await self.client.connect_ws()

    @asyncSlot
    async def turn_remove(self, chat_id, turn_ids):
        res = await self.api_chats.remove_turns(chat_id, turn_ids)
        self.turn_remove_signal.emit(res)
        self.chat_histories[chat_id] = [t for t in self.chat_histories.get(chat_id, []) if
                                        t.get('turn_key', {}).get('turn_id') not in turn_ids]

    @asyncSlot
    async def get_history(self, chat_id, next_token=None):
        if next_token or chat_id not in self.chat_histories:
            data = await self.api_chats.get_history(chat_id, next_token)

            if next_token:
                self.chat_histories[chat_id] = data['turns'] + self.chat_histories.get(chat_id, [])
            else:
                self.chat_histories[chat_id] = data['turns']

            self.chat_next_tokens[chat_id] = {"token": data['next_token']}

        self.get_history_signal.emit(self.chat_histories[chat_id], self.chat_next_tokens.get(chat_id, {}).get('token'))

    @asyncSlot
    async def get_character(self, character_id=None, path=None):
        if character_id not in self.characters:
            data = await self.api_chars.get_character(character_id, path)
            if data:
                self.characters[data['character_id']] = data
                character_id = data['character_id']
        self.get_char_signal.emit(self.characters.get(character_id, {}))

    @asyncSlot
    async def character_vote(self, character_id, vote):
        res = await self.api_chars.vote_character(character_id, vote)
        self.character_vote_signal.emit(res)
        if character_id in self.characters:
            self.characters[character_id]['voted']['vote'] = vote
            self.characters[character_id]['voted']['voted'] = vote is not None

    @asyncSlot
    async def get_me(self):
        self.me = await self.api_users.get_me()
        self.get_me_signal.emit(self.me)

    @asyncSlot
    async def update_character(self, data):
        res = await self.api_chars.update_character(data)
        self.update_character_signal.emit(res)
        if data.get('status') == "OK" and res.get('character'):
            char_id = res['character']['external_id']
            if char_id in self.characters:
                self.characters[char_id]['character'] = res['character']

    @asyncSlot
    async def get_update_servers(self):
        self.get_update_servers_signal.emit(await self.api_emilia.get_update_servers())

    @asyncSlot
    async def get_themes(self, query: str = "", author: str = "", count: int = 0, offset: int = 0):
        self.get_themes_signal.emit(await self.api_emilia.get_themes(query, author, count, offset))

    @asyncSlot
    async def get_user_themes(self, creator_id: int):
        self.get_user_themes_signal.emit(await self.api_emilia.get_user_themes(creator_id))

    @asyncSlot
    async def get_theme(self, theme_id: str):
        self.get_theme_signal.emit(await self.api_emilia.get_theme(theme_id))

    @asyncSlot
    async def download_theme(self, theme_name: str, theme_id: str):
        self.download_theme_signal.emit(await self.api_emilia.download_theme(theme_name, theme_id))

    @asyncSlot
    async def upload_theme(self, theme_name: str):
        if not self.me:
            self.me = await self.api_users.get_me()
        user = self.me.get('user', {})
        user_id = user.get('id')
        if not user_id:
            self.upload_theme_signal.emit({"error": "User not authenticated"})
            return

        username = user.get('username')
        avatar_file_name = user.get('account', {}).get('avatar_file_name')
        token = self.client.token

        res = await self.api_emilia.upload_theme(theme_name, user_id, username, avatar_file_name, token)
        self.upload_theme_signal.emit(res)

    @asyncSlot
    async def update_theme(self, theme_name: str, theme_id: str):
        if not self.me:
            self.me = await self.api_users.get_me()
        user = self.me.get('user', {})
        user_id = user.get('id')
        if not user_id:
            self.update_theme_signal.emit({"error": "User not authenticated"})
            return

        username = user.get('username')
        avatar_file_name = user.get('account', {}).get('avatar_file_name')
        token = self.client.token

        res = await self.api_emilia.update_theme(theme_name, theme_id, user_id, username, avatar_file_name, token)
        self.update_theme_signal.emit(res)

    @asyncSlot
    async def delete_theme(self, theme_id: str):
        user = self.me.get('user', {})
        user_id = user.get('id')
        if not user_id:
            self.update_theme_signal.emit({"error": "User not authenticated"})
            return

        username = user.get('username')
        avatar_file_name = user.get('account', {}).get('avatar_file_name')
        token = self.client.token
        res = await self.api_emilia.delete_theme(theme_id, token, user_id, username, avatar_file_name)
        self.delete_theme_signal.emit(res)

    @asyncSlot
    async def get_user_settings(self):
        self.get_user_settings_signal.emit(await self.api_users.get_user_settings())

    @asyncSlot
    async def update_user_settings(self, data):
        self.update_user_settings_signal.emit(await self.api_users.update_user_settings(data))

    @asyncSlot
    async def update_user_settings_2(self, data):
        self.update_user_settings_2_signal.emit(await self.api_users.update_user_settings_2(data))

    @asyncSlot
    async def get_user(self, username):
        self.get_user_signal.emit(await self.api_users.get_user(username))

    @asyncSlot
    async def get_chat(self, character_id):
        self.chat_signal.emit(await self.api_chats.get_chat(character_id))

    @asyncSlot
    async def get_chat_by_id(self, chat_id, load_metadata=False):
        self.get_chat_by_id_signal.emit(await self.api_chats.get_chat_by_id(chat_id, load_metadata))

    @asyncSlot
    async def copy_chat(self, chat_id, end_turn_id):
        self.copy_chat_signal.emit(await self.api_chats.copy_chat(chat_id, end_turn_id))

    @asyncSlot
    async def hide_chat(self, character_id):
        self.hide_chat_signal.emit(await self.api_chats.hide_chat(character_id))

    @asyncSlot
    async def get_voice_limit(self):
        response = await self.api_cai_limit.voice_call()
        self.current_limits['voice_limit'] = response
        self.get_voice_call_limit_signal.emit(response)

    @asyncSlot
    async def get_chat_image_attachment_limit_signal(self):
        response = await self.api_cai_limit.chat_image_attachment()
        self.current_limits['chat_image_attachment'] = response
        self.get_chat_image_attachment_limit_signal.emit(response)

    @asyncSlot
    async def get_recent_chats(self):
        self.recent_chats_signal.emit(await self.api_chats.get_recent_chats())

    @asyncSlot
    async def get_featured_voices(self):
        self.featured_voices_signal.emit(await self.api_voices.get_featured_voices())

    @asyncSlot
    async def get_scenes_curated(self):
        self.get_scenes_curated_signal.emit(await self.api_scenes.get_curated_scenes())

    @asyncSlot
    async def get_scene_by_id(self, scene_id):
        self.get_scene_by_id_signal.emit(await self.api_scenes.get_scene(scene_id))

    @asyncSlot
    async def get_scenes_by_user(self, username):
        self.get_scenes_by_user_signal.emit(await self.api_scenes.get_user_scenes(username))

    @asyncSlot
    async def get_trythis_chats(self):
        self.trythis_chats_signal.emit(await self.api_chats.get_trythis_chats())

    @asyncSlot
    async def get_main_page_chats(self):
        self.get_main_page_chats_signal.emit(await self.api_chats.get_main_page_chats())

    @asyncSlot
    async def get_recommended_chars(self):
        self.featured_chats_signal.emit(await self.api_chats.get_recommended_chars())

    @asyncSlot
    async def get_recommend_chars_by_id(self, char_id):
        self.get_recommend_chars_by_id_signal.emit(await self.api_chars.get_similar_characters(char_id))

    @asyncSlot
    async def query_autocomplete(self, query):
        self.query_autocomplete_signal.emit(await self.api_chars.query_autocomplete(query))

    @asyncSlot
    async def get_user_following(self, page=1, username=""):
        self.user_following_signal.emit(await self.api_users.get_user_following(page, username))

    @asyncSlot
    async def get_user_followers(self, page=1, username=""):
        self.user_followers_signal.emit(await self.api_users.get_user_followers(page, username))

    @asyncSlot
    async def get_me_following(self):
        self.me_following_signal.emit(await self.api_users.get_me_following())

    @asyncSlot
    async def user_follow(self, username):
        self.user_follow_signal.emit(await self.api_users.user_follow(username))

    @asyncSlot
    async def user_unfollow(self, username):
        self.user_unfollow_signal.emit(await self.api_users.user_unfollow(username))

    @asyncSlot
    async def character_search(self, query):
        self.character_search_signal.emit(await self.api_chars.search_characters(query))

    @asyncSlot
    async def scene_search(self, query):
        self.scene_search_signal.emit(await self.api_scenes.search_scenes(query))

    @asyncSlot
    async def user_search(self, query):
        self.user_search_signal.emit(await self.api_users.user_search(query))

    @asyncSlot
    async def voices_search(self, query=None, char_name=None):
        self.voices_search_signal.emit(await self.api_voices.search_voices(query, char_name))

    @asyncSlot
    async def voices_search_username(self, username):
        self.voices_search_username_signal.emit(await self.api_voices.search_voices_by_username(username))

    @asyncSlot
    async def get_voice(self, voice_id):
        self.get_voice_signal.emit(await self.api_voices.get_voice(voice_id))

    @asyncSlot
    async def voice_override(self, char_id):
        self.voice_override_signal.emit(await self.api_voices.get_voice_override(char_id))

    @asyncSlot
    async def voice_override_update(self, char_id, voice_id):
        self.voice_override_update_signal.emit(await self.api_voices.update_voice_override(char_id, voice_id))

    @asyncSlot
    async def voice_override_delete(self, char_id):
        self.voice_override_delete_signal.emit(await self.api_voices.delete_voice_override(char_id))

    @asyncSlot
    async def get_upvoted_characters(self):
        self.get_upvoted_characters_signal.emit(await self.api_chars.get_upvoted_characters())

    @asyncSlot
    async def create_character(self, data):
        self.create_character_signal.emit(await self.api_chars.create_character(data))

    @asyncSlot
    async def get_user_personas(self, fr=0):
        self.get_user_personas_signal.emit(await self.api_chars.get_user_personas(fr))

    @asyncSlot
    async def create_persona(self, a, b, c, d):
        self.create_persona_signal.emit(await self.api_chars.create_persona(a, b, c, d))

    @asyncSlot
    async def update_persona(self, data):
        self.update_persona_signal.emit(await self.api_chars.update_persona(data))

    @asyncSlot
    async def remove_persona(self, data):
        self.remove_persona_signal.emit(await self.api_chars.remove_persona(data))

    @asyncSlot
    async def get_scene(self, scene_id):
        self.get_scene_signal.emit(await self.api_scenes.get_scene(scene_id))

    @asyncSlot
    async def create_scene(self, data):
        self.create_scene_signal.emit(await self.api_scenes.create_scene(data))

    @asyncSlot
    async def update_scene(self, data, scene_id):
        self.update_scene_signal.emit(await self.api_scenes.update_scene(scene_id, data))

    @asyncSlot
    async def remove_scene(self, scene_id):
        self.remove_scene_signal.emit(await self.api_scenes.remove_scene(scene_id))

    @asyncSlot
    async def upload_avatar(self, ft, img):
        self.upload_avatar_signal.emit(await self.api_users.upload_avatar(ft, img))

    @asyncSlot
    async def upload_image(self, mp):
        self.upload_image_signal.emit(await self.api_users.upload_image(mp))

    @asyncSlot
    async def replay(self, cid, rid, tid, vid="", vq=""):
        self.replay_signal.emit(await self.api_voices.replay(cid, rid, tid, vid, vq))

    @asyncSlot
    async def join_or_create_session(self, r, u, n=None, vq=None, v=None):
        self.join_or_create_session_signal.emit(await self.api_voices.join_or_create_session(r, u, n, vq, v))

    @asyncSlot
    async def get_category_characters(self, cat):
        self.category_characters_signal.emit(await self.api_chars.get_category_characters(cat))

    @asyncSlot
    async def get_character_chats(self, char_id, pt=1):
        self.character_chats_signal.emit(await self.api_chats.get_character_chats(char_id, pt))

    @asyncSlot
    async def get_available_models(self):
        res = await self.client.request("get-available-models", domain="neo")
        self.get_available_models_signal.emit(res.get('available_models', []))

    @asyncSlot
    async def get_available_models_git(self):
        res = await self.client.custom_request(
            "https://raw.githubusercontent.com/Kajitsy/Emilia/refs/heads/emilia/data/CAI_Available_Models.json",
            text=True)
        self.get_available_models_git_signal.emit(res)