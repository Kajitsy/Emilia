import os, hashlib, logging, sounddevice, soundfile, io, asyncio, time, scipy.signal, inspect
import requests, websockets, speech_recognition
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QRectF, QLocale
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from gpytranslate import Translator
from functools import wraps
from pypresence import AioPresence

from modules.CustomCharAI import Async as ccaa
from modules.VTubeCore import EEC

def asyncSlot(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.ensure_future(func(*args, **kwargs))
    return wrapper

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QPixmap)

    def __init__(self, url, width, height, cache_dir="cache/avatars"):
        super().__init__()
        self.url = url
        self.cache_dir = cache_dir
        self.width = width
        self.height = height
        self.radius: int or float | None = 100

        os.makedirs(self.cache_dir, exist_ok=True)

    def round_qpixmap(self, pixmap: QPixmap):
        target = QPixmap(self.width, self.height)
        target.fill(Qt.GlobalColor.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width, self.height), self.radius, self.radius)
        painter.setClipPath(path)

        scaled_pixmap = pixmap.scaled(self.width, self.height,
                                      Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation)

        x = (self.width - scaled_pixmap.width()) // 2
        y = (self.height - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)

        painter.end()
        return target

    def get_cache_path(self):
        filename = hashlib.md5(self.url.encode('utf-8')).hexdigest() + ".png"
        return os.path.join(self.cache_dir, filename)

    def run(self):
        cache_path = self.get_cache_path()
        pixmap = QPixmap()
        if os.path.exists(cache_path):
            pixmap.load(cache_path)
            pixmap = pixmap.scaled(self.width, self.height,
                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            self.image_loaded.emit(self.round_qpixmap(pixmap))
            return

        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            if pixmap.loadFromData(response.content):
                if not pixmap.save(cache_path):
                    logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): File saving error: {cache_path}")

            pixmap = pixmap.scaled(self.width, self.height,
                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            self.image_loaded.emit(self.round_qpixmap(pixmap))
        except Exception as e:
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Image download error: {e}")
            self.image_loaded.emit(QPixmap())

class FileLoaderThread(QThread):
    file = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, url, headers={}):
        super().__init__()
        self.url = url
        self.headers = headers

    def run(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            if response.status_code == 200:
                self.file.emit(response.content)
            else:
                logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): File download error: {response.status_code}")
        except Exception as e:
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): File download error: {e}")

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(self.save_path, 'wb') as file:
                for chunk in response.iter_content(4096):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        percent = int((downloaded_size / total_size) * 100)
                        self.progress.emit(percent)

            self.finished.emit(self.save_path)
        except Exception as e:
            self.finished.emit(str(e))

class PlayerThread(QThread):
    play_signal = pyqtSignal(object)
    stop_signal = pyqtSignal(object)

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        self.play(self.data)

    def play(self, data):
        audio_bytes = io.BytesIO(data)
        audio_array, sample_rate = soundfile.read(audio_bytes)

        new_length = int(round(len(audio_array) * 44100 / sample_rate))
        audio_array = scipy.signal.resample(audio_array, new_length)
        sample_rate = 44100

        self.play_signal.emit(True)
        sounddevice.play(audio_array, sample_rate)
        time.sleep(len(audio_array) / sample_rate)
        sounddevice.stop()
        self.stop_signal.emit(True)

    def stop(self):
        sounddevice.stop()
        self.stop_signal.emit(True)

class DiscordRPC(QThread):
    rpc_connected = pyqtSignal(object)

    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.discord_rpc: AioPresence | None = None
        self.start_time = time.time()
        self.latest_rpc = {}

    @property
    def rpc_check(self):
        return True if self.discord_rpc and self.mw.settings.value("discord_rpc/enable", True, type=bool) else False

    @asyncSlot
    async def connect(self):
        try:
            self.discord_rpc = AioPresence('1358471829165047819')
            self.rpc_connected.emit(await self.discord_rpc.connect())
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC connected!")
        except Exception as e:
            self.mw.settings.setValue("discord_rpc/enable", False)
            logging.error(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}")

    @asyncSlot
    async def update(self, *args, **kwargs):
        if self.rpc_check:
            try:
                self.latest_rpc = {
                    "args": args,
                    "kwargs": kwargs
                }
                await getattr(self.discord_rpc, "update")(*self.latest_rpc["args"], **self.latest_rpc["kwargs"], start=self.start_time)
                logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated!")
            except RuntimeError:
                logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated, but RuntimeError!")
            except Exception as e:
                self.mw.settings.setValue("discord_rpc/enable", False)
                logging.error(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}")
        else:
            logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC not initialized")

    @asyncSlot
    async def update_wlrpc(self):
        if self.rpc_check:
            try:
                await getattr(self.discord_rpc, "update")(*self.latest_rpc["args"], **self.latest_rpc["kwargs"], start=self.start_time)
                logging.debug("QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated!")
            except RuntimeError:
                logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated, but RuntimeError!")
            except Exception as e:
                self.mw.settings.setValue("discord_rpc/enable", False)
                logging.error(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}")
        else:
            logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC not initialized")

    @asyncSlot
    async def clear(self):
        if self.rpc_check:
            try:
                await self.discord_rpc.clear()
                logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC cleared!")
            except Exception as e:
                self.mw.settings.setValue("discord_rpc/enable", False)
                logging.error(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}")
        else:
            logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC not initialized")

    @asyncSlot
    async def close(self):
        try:
            await self.discord_rpc.close()
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC closed!")
        except Exception as e:
            self.mw.settings.setValue("discord_rpc/enable", False)
            logging.error(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}")

class ChatThread(QThread):
    finished = pyqtSignal(object)
    connected_signal = pyqtSignal(bool)
    user_message_signal = pyqtSignal(object)
    message_signal = pyqtSignal(object)
    turn_remove_signal = pyqtSignal(object)
    turn_regenerate_signal = pyqtSignal(object, object, object)
    resurrect_signal = pyqtSignal(object)
    new_chat_created_signal = pyqtSignal(object)
    chat_signal = pyqtSignal(object)
    get_history_signal = pyqtSignal(object)
    get_char_signal = pyqtSignal(object)
    get_chat_by_id_signal = pyqtSignal(object)
    get_me_signal = pyqtSignal(object)
    get_user_settings_signal = pyqtSignal(object)
    get_available_models_signal = pyqtSignal(object)
    get_available_models_git_signal = pyqtSignal(object)
    get_user_signal = pyqtSignal(object)
    hide_chat_signal = pyqtSignal(object)
    character_search_signal = pyqtSignal(object)

    recent_chats_signal = pyqtSignal(object)
    get_popular_and_trending_chars_signal = pyqtSignal(object)
    get_main_page_chats_signal = pyqtSignal(object)
    featured_chats_signal = pyqtSignal(object)
    recommended_chats_signal = pyqtSignal(object)
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
    get_upvoted_characters_signal = pyqtSignal(list)

    join_or_create_session_signal = pyqtSignal(object)

    voices_search_signal = pyqtSignal(object)
    voices_search_username_signal = pyqtSignal(object)
    featured_voices_signal = pyqtSignal(object)
    replay_signal = pyqtSignal(object)
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
        self.ccaa: ccaa | None = None
        self.connect: ccaa().connect() | None = {}
        self.me = {}
        self.connect = {}
        self.eec = EEC(self.mw, self.mw.settings.value("vtube/port", 8001))

        self.microphone_muted = True
        self.voiced = False
        self.lang = QLocale.system().name().split('_')[0]
        self.translator = Translator()

        self.chat_histories = {}
        self.category_characters = {}
        self.characters = {}

    @asyncSlot
    async def create_connect(self):
        self.connect = await self.ccaa.connect()
        self.connected_signal.emit(True)

    @asyncSlot
    async def check_vtube_connect(self):
        try:
            await self.eec.connect()
            self.vtube_connect_signal.emit(self.tr("Successful connection!"))
            await self.eec.close()
        except Exception as e:
            self.vtube_connect_signal.emit(self.tr("Connection error: ") + str(e))
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): VTube Check Error: {e}")

    def create_client(self, token):
        self.token = token
        self.ccaa = ccaa(token)

    def set_cookie(self, cookie):
        self.cookie = cookie
        self.ccaa = ccaa(self.token, cookie)
        logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Cookies are installed")

    async def _call_ccaa(self, method, signal, *args, **kwargs):
        if self.ccaa:
            response = await getattr(self.ccaa, method)(*args, **kwargs)
            signal.emit(response)

    @asyncSlot
    async def send_message(self, char, chat_id, text, tts_enabled=False, voice_id=""):
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
            if self.connect:
                try:
                    async for response in self.connect.send_message(char, chat_id, text):
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
                                await self._call_ccaa('resurrect', self.resurrect_signal, chat_id)
                                return
                            self.message_signal.emit(response)
                            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The message has been updated")
                except websockets.WebSocketException:
                    self.connect = await self.ccaa.connect()
                    logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Reconnecting to websockets...")

    @asyncSlot
    async def turn_remove(self, chat_id, turn_ids):
        await self._call_ccaa('turn_remove', self.turn_remove_signal, chat_id, turn_ids)
        for i, turn in enumerate(self.chat_histories.get(chat_id, [])):
            if turn.get('turn_key', {}).get('turn_id') in turn_ids:
                del self.chat_histories[chat_id][i]

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
        while True:
            if self.connect:
                try:
                    async for response in self.connect.generate_turn_candidate(char, chat_id, turn_id, user_name):
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
                                await self._call_ccaa('resurrect', self.resurrect_signal, chat_id)
                                return
                            self.turn_regenerate_signal.emit(response, turn_id, message_bubble_added)
                            message_bubble_added = True
                            turn_id = response['turn']['turn_key']['turn_id']
                            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The message has been updated")
                except websockets.WebSocketException:
                    self.connect = await self.ccaa.connect()
                    logging.warning(f"QThreads.py: ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}) Reconnecting to websockets...")

    @asyncSlot
    async def replay(self, candidateId, roomId, turnId, voiceId="", voiceQuery=""):
        await self._call_ccaa('tts', self.replay_signal, candidateId, roomId, turnId, voiceId, voiceQuery)

    @asyncSlot
    async def get_me(self):
        await self._call_ccaa('get_me', self.get_me_signal)

    @asyncSlot
    async def get_user_settings(self):
        await self._call_ccaa('get_user_settings', self.get_user_settings_signal)

    @asyncSlot
    async def get_user(self, username):
        await self._call_ccaa('get_user', self.get_user_signal, username)

    @asyncSlot
    async def new_chat(self, char, chat_id = None, preferred_model_type = "MODEL_TYPE_BALANCED"):
        if not self.me and self.ccaa: self.me = await self.ccaa.get_me()
        if self.connect:
            response = await self.connect.new_chat(char, self.me['id'], preferred_model_type=preferred_model_type)
            self.new_chat_created_signal.emit(response)
            if chat_id: del self.chat_histories[chat_id]
            logging.debug(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): New chat started")

    @asyncSlot
    async def get_chat(self, char):
        await self._call_ccaa('get_recent_chat', self.chat_signal, char)

    @asyncSlot
    async def get_chat_by_id(self, chat_id, load_metadata=False):
        await self._call_ccaa('get_chat_by_id', self.get_chat_by_id_signal, chat_id, load_metadata)

    @asyncSlot
    async def get_available_models(self):
        await self._call_ccaa('get_available_models', self.get_available_models_signal)

    @asyncSlot
    async def get_available_models_git(self):
        await self._call_ccaa('get_available_models_git', self.get_available_models_git_signal)

    @asyncSlot
    async def copy_chat(self, chat_id, end_turn_id):
        await self._call_ccaa('copy_chat', self.copy_chat_signal, chat_id, end_turn_id)

    @asyncSlot
    async def hide_chat(self, character_external_id):
        await self._call_ccaa('hide_recent_chat', self.hide_chat_signal, character_external_id)

    @asyncSlot
    async def get_history(self, chat_id):
        if self.ccaa:
            if not chat_id in self.chat_histories:
                chat, next_token = await self.ccaa.get_messages(chat_id)
                self.chat_histories[chat_id] = list(reversed(chat))
            self.get_history_signal.emit(self.chat_histories[chat_id])

    @asyncSlot
    async def get_recent_chats(self, userCanUseRooms: bool = False):
        await self._call_ccaa('get_recent_chats', self.recent_chats_signal, userCanUseRooms)

    @asyncSlot
    async def get_featured_voices(self):
        await self._call_ccaa('get_featured_voices', self.featured_voices_signal)

    @asyncSlot
    async def get_trythis_chats(self):
        await self._call_ccaa('get_trythis_chats', self.trythis_chats_signal)

    @asyncSlot
    async def get_category_characters(self, category):
        if not self.category_characters.get(category, []) and self.ccaa:
                response = await self.ccaa.get_category_characters(category)
                self.category_characters[category] = response
        self.category_characters_signal.emit(self.category_characters.get(category, {}))

    @asyncSlot
    async def get_character_chats(self, character_id):
        await self._call_ccaa('get_chats_with_character', self.character_chats_signal, character_id)

    @asyncSlot
    async def get_main_page_chats(self):
        await self._call_ccaa('get_main_page_chats', self.get_main_page_chats_signal, self.mw.current_language.split("_")[0])

    @asyncSlot
    async def get_character(self, character_id):
        if self.ccaa:
            if not character_id in self.characters:
                character = await self.ccaa.get_character(character_id)
                voted = await self.ccaa.voted(character_id)
                self.characters[character_id] = {
                    "character": character,
                    "voted": voted
                }
            self.get_char_signal.emit(self.characters[character_id])

    @asyncSlot
    async def get_user_following(self, pageParam=1, username=""):
        await self._call_ccaa('get_following', self.user_following_signal, pageParam, username)

    @asyncSlot
    async def get_user_followers(self, pageParam=1, username=""):
        await self._call_ccaa('get_followers', self.user_followers_signal, pageParam, username)

    @asyncSlot
    async def get_me_following(self):
        await self._call_ccaa('get_me_following', self.me_following_signal)

    @asyncSlot
    async def user_follow(self, username):
        await self._call_ccaa('follow', self.user_follow_signal, username)

    @asyncSlot
    async def user_unfollow(self, username):
        await self._call_ccaa('unfollow', self.user_unfollow_signal, username)

    @asyncSlot
    async def character_vote(self, character_id, vote):
        await self._call_ccaa('vote', self.character_vote_signal, character_id, vote)

    @asyncSlot
    async def character_search(self, query: str | None = None):
        await self._call_ccaa('character_search', self.character_search_signal, query)

    @asyncSlot
    async def voices_search(self, query: str | None = None, character_name: str| None = None):
        await self._call_ccaa('voices_search', self.voices_search_signal, query, character_name)

    @asyncSlot
    async def voices_search_username(self, username: str | None = None):
        await self._call_ccaa('voices_search_username', self.voices_search_username_signal, username)

    @asyncSlot
    async def get_voice(self, voice_id):
        await self._call_ccaa('get_voice', self.get_voice_signal, voice_id)

    @asyncSlot
    async def voice_override(self, character_id):
        await self._call_ccaa('voice_override', self.voice_override_signal, character_id)

    @asyncSlot
    async def voice_override_update(self, character_id, voice_id):
        await self._call_ccaa('voice_override_update', self.voice_override_update_signal, character_id, voice_id)

    @asyncSlot
    async def voice_override_delete(self, character_id):
        await self._call_ccaa('voice_override_delete', self.voice_override_delete_signal, character_id)

    @asyncSlot
    async def vtube_use_emote(self, emote):
        await self.eec.connect()
        await self.eec.UseEmote(emote)
        await self.eec.close()
        logging.debug(f'QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): The emotion of "{emote}" was used')

    @asyncSlot
    async def get_upvoted_characters(self):
        await self._call_ccaa('get_upvoted_characters', self.get_upvoted_characters_signal)

class VoiceModeThread(QThread):
    connected_signal = pyqtSignal(bool)
    speech_signal = pyqtSignal(object)
    speech_error_signal = pyqtSignal(object)

    user_message = pyqtSignal(str)
    char_message = pyqtSignal(object)

    def __init__(self, parent, token, char, chat_id, voice_id):
        super().__init__()
        self.parent = parent
        self.mw = self.parent.mw
        self.char = char
        self.chat_id = chat_id
        self.voice_id = voice_id
        self.muted = parent.muted
        self.lang = self.mw.current_language
        self.used_emotes = []

        self.connect = None
        self.ccaa = ccaa(token)
        self.recognizer = speech_recognition.Recognizer()
        self.eec = EEC(self.mw)
        self.vtube_studio = self.mw.settings.value("vtube/use", False, type=bool)
        if self.mw.settings.value('input_device', False) is False:
            self.input_index = 0
        else:
            self.input_index = self.mw.settings.value('input_device', 0, type=int) + 1

    def sd_stop(self):
        sounddevice.stop()

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.process_user_input())

    async def recognize_speech(self):
        while True:
            if not self.muted:
                try:
                    audio = self.listen_to_microphone(self.recognizer)
                    result = self.recognizer.recognize_google(audio, language=self.lang.split('_')[0])
                    if not self.muted:
                        self.speech_signal.emit(False)
                        return result
                    else:
                        QThread.sleep(3)
                except speech_recognition.UnknownValueError:
                    self.speech_error_signal.emit(True)
                    logging.warning(f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Error converting speech to text")
                    pass
            else:
                QThread.sleep(1)

    def listen_to_microphone(self, recognizer):
        self.speech_signal.emit(True)
        with speech_recognition.Microphone(device_index=self.input_index) as source:
            return recognizer.listen(source)

    async def tts(self, candidateId, roomId, turnId, voiceId: str = "", voiceQuery: str = ""):
        response = await self.ccaa.tts(candidateId, roomId, turnId, voiceId, voiceQuery)
        link = response["replayUrl"]
        download = requests.get(link, stream=True)
        if download.status_code == 200:
            audio_bytes = io.BytesIO(download.content)
            audio_array, sample_rate = soundfile.read(audio_bytes)
            return audio_array, sample_rate

    async def send_message(self, text):
        if self.connect:
            while True:
                try:
                    async for response in self.connect.send_message(self.char, self.chat_id, text):
                        if not response['turn']['author']['author_id'].isdigit():
                                if response.get('turn', {}).get('candidates', [])[0].get('is_final'):
                                    return response['turn']
                except websockets.WebSocketException:
                    self.connected_signal.emit(False)
                    self.connect = await self.ccaa.connect()
                    self.connected_signal.emit(True)

    async def process_user_input(self):
        self.connect = await self.ccaa.connect()
        if self.vtube_studio: await self.eec.connect()
        self.connected_signal.emit(True)
        while True:
            if self.vtube_studio: await self.eec.UseEmote("Listening")
            user_input = await self.recognize_speech()
            self.user_message.emit(str(user_input))
            if self.vtube_studio: await self.eec.UseEmote("Thinks")
            ai_message = await self.send_message(user_input)
            audio_array, sample_rate = await self.tts(ai_message['primary_candidate_id'], self.chat_id, ai_message['turn_key']['turn_id'], self.voice_id, ai_message['author']['name'])
            self.char_message.emit(ai_message)
            if self.vtube_studio: await self.eec.UseEmote("Says")
            sounddevice.play(audio_array, sample_rate)
            sounddevice.wait()
            sounddevice.stop()