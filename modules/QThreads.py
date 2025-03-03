import io, asyncio, re, os, hashlib, json, time
import requests, websockets

import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import google.generativeai as genai
import translators as ts
from PyQt6.QtWidgets import QMessageBox

from elevenlabs.client import ElevenLabs
from characterai import aiocai
from elevenlabs import VoiceSettings, play, save
from google.generativeai.types import HarmCategory

from PyQt6.QtCore import QThread, pyqtSignal, QLocale, Qt, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath

from modules.config import getconfig
from modules.CustomCharAI import Sync as ccas
from modules.CustomCharAI import Async as ccaa
from modules.eec import EEC
from modules.ets import translations as ets

class MainThreadCharAI(QThread):
    ouinput_signal = pyqtSignal(str, object, str, int, object, object)
    chatLoaded = pyqtSignal(list)
    audio_is_completed = pyqtSignal(bool)

    def __init__(self, parent, tts, get_chat_history=True):
        super().__init__()
        self._running = True

        self.client = aiocai.Client(getconfig("client", configfile="charaiconfig.json"))
        self.parent = parent
        self.get_chat_history = get_chat_history
        self.tts = tts
        self.vts = EEC()
        self.ccaa = ccaa()

        self.vtube_enable = getconfig("vtubeenable", False)
        self.umtranslate = getconfig("umtranslate", False)
        self.aimtranslate = getconfig("aimtranslate", False)
        self.show_notranslate_message = getconfig("show_notranslate_message", True)
        self.show_system_messages = getconfig("show_system_messages", True)
        self.lang = getconfig("language", QLocale.system().name())
        self.trls = ets(self.lang)

    async def generate_ai_response(self, text):
        while True:
            try:
                message = await self.connect.send_message(self.character, self.chat.chat_id, text)
                return message
            except websockets.exceptions.ConnectionClosedError:
                self.connect = await self.client.connect()

    async def recognize_speech(self, recognizer):
        while True:
            if not self.parent.microphone_muted:
                try:
                    audio = await self.listen_to_microphone(recognizer)
                    result = recognizer.recognize_google(audio, language=self.lang)
                    if not self.parent.microphone_muted:
                        return result
                    else:
                        await asyncio.sleep(0.5)
                except sr.UnknownValueError:
                    if self.show_system_messages:
                        self.ouinput_signal.emit("zxc", "sys", self.trls.tr("Main", "repeat"), 0, False, False)
                    pass
            else:
                await asyncio.sleep(0.5)

    async def listen_to_microphone(self, recognizer):
        if self.parent.microphone:
            with self.parent.microphone as source:
                return recognizer.listen(source)
        else:
            with sr.Microphone() as source:
                return recognizer.listen(source)

    async def charai_tts(self):
        message = self.message

        candidateId = re.search(r"candidate_id='([^']*)'", (str(message.candidates))).group(1)
        roomId = message.turn_key.chat_id
        turnId = message.turn_key.turn_id
        voiceId = self.parent.charaitts_voice_entry.text()
        voiceQuery = message.name

        response = await self.ccaa.tts(candidateId, roomId, turnId, voiceId, voiceQuery)
        link = response["replayUrl"]
        download = requests.get(link, stream=True)
        if download.status_code == 200: 
            audio_bytes = io.BytesIO(download.content)
            audio_array, samplerate = sf.read(audio_bytes)
            with open("temp_audio.mp3", 'wb') as file:
                for chunk in download.iter_content(chunk_size=8192):
                    file.write(chunk)
            return audio_array, samplerate

    async def play_audio_response(self, text):
        if self.vtube_enable:
            await self.vts.UseEmote("Thinks")

        try:
            if self.tts == "charai":
                audio, sample_rate = await self.charai_tts()
            elif self.tts == "elevenlabs":
                audio = self.elevenlabs.generate(
                    voice=getconfig("elevenlabs_voice", configfile="charaiconfig.json"),
                    output_format="mp3_22050_32",
                    text=text,
                    model="eleven_multilingual_v2",
                    voice_settings=VoiceSettings(
                        stability=0.2,
                        similarity_boost=0.8,
                        style=0.4,
                        use_speaker_boost=True,
                    )
                )

                if self.vtube_enable:
                    await self.vts.UseEmote("Says")

                save(audio, "temp_audio.wav")
                self.ouinput_signal.emit("zxc", "ai", text + self.ai_message_before_translate if self.aimtranslate and self.show_notranslate_message else text, len(text), True, True if self.aimtranslate and self.show_notranslate_message else False)
                self.audio_is_completed.emit(False)
                play(audio, use_ffmpeg=False)
                self.audio_is_completed.emit(True)
                return

            if self.vtube_enable:
                await self.vts.UseEmote("Says")

            audio_len = len(audio)
            self.ouinput_signal.emit("zxc", "ai",
                                     text + self.ai_message_before_translate if self.aimtranslate and self.show_notranslate_message else text,
                                     audio_len, True,
                                     True if self.aimtranslate and self.show_notranslate_message else False)
            self.audio_is_completed.emit(False)
            sd.play(audio, sample_rate)
            await asyncio.sleep(len(audio) / sample_rate)
            sd.stop()
            self.audio_is_completed.emit(True)

        except Exception as e:
            QMessageBox.critical(self.parent, self.trls.tr("Errors", "Label"), str(e))

    async def process_user_input(self):
        self.recognizer = sr.Recognizer()
        self.character = getconfig("char", configfile="charaiconfig.json")
        async with await self.client.connect() as self.connect:

            if self.vtube_enable:
                await self.vts.VTubeConnect()

            self.chat = await self.client.get_chat(self.character)

            if self.get_chat_history:
                if self.show_system_messages:
                    self.ouinput_signal.emit("zxc", "sys", self.trls.tr("Main", "your_recent_messages"), 0, False,
                                             False)
                history = await self.client.get_history(self.chat.chat_id)
                self.chatLoaded.emit(list(reversed(history.turns)))

            if self.tts == "elevenlabs":
                self.elevenlabs = ElevenLabs(api_key=getconfig("elevenlabs_api_key"))

            if self.show_system_messages:
                self.ouinput_signal.emit("zxc", "sys", self.trls.tr("Main", "you_can_start"), 0, False, False)

            while self._running:
                if not self._running:
                    break

                if self.vtube_enable:
                    await self.vts.UseEmote("Listening")

                user_message = await self.recognize_speech(self.recognizer)

                if not self._running:
                    break

                if self.umtranslate:
                    while True:
                        try:
                            user_message_translate = ts.translate_text(user_message, to_language="en", translator="google")
                            break
                        except:
                            if not self._running:
                                break
                            pass
                    user_message_before_translate = f"<p style='color: gray; font-style: italic; font-size: 12px;'>{user_message}</p>"
                    user_message = user_message_translate

                self.ouinput_signal.emit(
                    "zxc", "human",
                    user_message + user_message_before_translate
                    if self.umtranslate and self.show_notranslate_message else user_message,
                    len(user_message), True,
                    True if self.aimtranslate and self.show_notranslate_message else False
                )

                if not self._running:
                    break

                self.message = await self.generate_ai_response(user_message)

                if not self._running:
                    break

                self.ai_message = self.message.text

                if self.aimtranslate:
                    while True:
                        try:
                            self.ai_message_translate = ts.translate_text(self.ai_message, to_language=self.trls.slang, translator="google")
                            break
                        except:
                            pass
                    self.ai_message_before_translate = f"<p style='color: gray; font-style: italic; font-size: 12px;'>{self.ai_message}</p>"
                    self.ai_message = self.ai_message_translate

                if not self._running:
                    break

                await self.play_audio_response(self.ai_message)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.process_user_input())

class MainThreadGemini(QThread):
    ouinput_signal = pyqtSignal(str, object, str, int, object, object)
    audio_is_completed = pyqtSignal(bool)

    def __init__(self, parent, tts):
        super().__init__()
        self._running = True

        self.gemini_model = getconfig("gemini_model", "gemini-1.5-flash", "geminiconfig.json")
        self.model = genai.GenerativeModel(self.gemini_model)
        self.chat = self.model.start_chat(history=[])
        self.parent = parent
        genai.configure(api_key=self.parent.gemini_token_entry.text())
        self.tts = tts

        self.vtube_enable = getconfig("vtubeenable", False)
        self.umtranslate = getconfig("umtranslate", False)
        self.aimtranslate = getconfig("aimtranslate", False)
        self.show_notranslate_message = getconfig("show_notranslate_message", True)
        self.show_system_messages = getconfig("show_system_messages", True)
        self.lang = getconfig("language", QLocale.system().name())
        self.trls = ets(self.lang)

        self.gemini_harassment = getconfig("harassment", 3, "geminiconfig.json")
        self.gemini_hate = getconfig("hate", 3, "geminiconfig.json")
        self.gemini_se_exlicit = getconfig("se_exlicit", 3, "geminiconfig.json")
        self.gemini_dangerous_content = getconfig("dangerous_content", 3, "geminiconfig.json")

    async def generate_ai_response(self, text):
        try:
            self.chunk = self.chat.send_message(text, safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: self.gemini_harassment,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: self.gemini_hate,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: self.gemini_se_exlicit,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: self.gemini_dangerous_content
                })
            return self.chunk
        except Exception as e:
            if e.code == 400 and "User location is not supported" in e.message:
                QMessageBox.critical(self, self.trls.tr("Errors", "Label") + self.trls.tr("Errors", "Gemini 400"))
            else:
                QMessageBox.critical(self, self.trls.tr("Errors", "Label") + str(e))
            return ""

    async def recognize_speech(self, recognizer):
        while True:
            if not self.parent.microphone_muted:
                try:
                    audio = await self.listen_to_microphone(recognizer)
                    result = recognizer.recognize_google(audio, language=self.lang)
                    if not self.parent.microphone_muted:
                        return result
                    else:
                        await asyncio.sleep(0.5)
                except sr.UnknownValueError:
                    if self.show_system_messages:
                        self.ouinput_signal.emit("zxc", "sys", self.trls.tr("Main", "repeat"), 0, False, False)
                    pass
            else:
                await asyncio.sleep(0.5)

    async def listen_to_microphone(self, recognizer):
        if self.parent.microphone:
            with self.parent.microphone as source:
                return recognizer.listen(source)
        else:
            with sr.Microphone() as source:
                return recognizer.listen(source)

    async def play_audio_response(self, text):
        try:
            if self.tts == "elevenlabs":
                audio = self.elevenlabs.generate(
                    voice=getconfig("elevenlabs_voice", configfile="charaiconfig.json"),
                    output_format="mp3_22050_32",
                    text=text,
                    model="eleven_multilingual_v2",
                    voice_settings=VoiceSettings(
                        stability=0.2,
                        similarity_boost=0.8,
                        style=0.4,
                        use_speaker_boost=True,
                    )
                )

                if self.vtube_enable:
                    await self.vts.UseEmote("Says")

                save(audio, "temp_audio.wav")
                self.ouinput_signal.emit("zxc", "ai", text + self.ai_message_before_translate if self.aimtranslate and self.show_notranslate_message else text, len(text), True, True if self.aimtranslate and self.show_notranslate_message else False)
                self.audio_is_completed.emit(False)
                play(audio, use_ffmpeg=False)
                self.audio_is_completed.emit(True)
        except Exception as e:
            QMessageBox.critical(self.parent, self.trls.tr("Errors", "Label"), str(e))

    async def process_user_input(self):
        recognizer = sr.Recognizer()

        if self.vtube_enable:
            await self.vts.VTubeConnect()

        if self.tts == "elevenlabs":
            self.elevenlabs = ElevenLabs(api_key=getconfig("elevenlabs_api_key"))

        if self.show_system_messages:
            self.ouinput_signal.emit("zxc", "sys", self.trls.tr("Main", "you_can_start"), 0, False, False)

        while self._running:
            if self.vtube_enable:
                await self.vts.UseEmote("Listening")

            user_message = await self.recognize_speech(recognizer)

            if self.umtranslate:
                try:
                    user_message_translate = ts.translate_text(user_message, to_language="en", translator="google")
                    break
                except:
                    pass
                user_message_before_translate = f"<p style='color: gray; font-style: italic; font-size: 12px;'>{user_message}</p>"
                user_message = user_message_translate

            self.ouinput_signal.emit("zxc", "human", user_message + user_message_before_translate if self.umtranslate and self.show_notranslate_message else user_message, len(user_message), True, True if self.aimtranslate and self.show_notranslate_message else False)

            self.message = await self.generate_ai_response(user_message)
            self.ai_message = self.message.text

            if self.aimtranslate:
                while True:
                    try:
                        self.ai_message_translate = ts.translate_text(self.ai_message, to_languaget=self.trls.slang, translator="google")
                        break
                    except:
                        pass
                self.ai_message_before_translate = f"<p style='color: gray; font-style: italic; font-size: 12px;'>{self.ai_message}</p>"
                self.ai_message = self.ai_message_translate

            await self.play_audio_response(self.ai_message)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.process_user_input())

class ChatDataWorker(QThread):
    recommend_chats_signal = pyqtSignal(object)
    recent_chats_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ccas = ccas()

    def fetch_data(self):
        try:
            recommend_chats = self.ccas.get_recommend_chats()
            recent_chats = self.ccas.get_recent_chats()
            self.recommend_chats_signal.emit(recommend_chats)
            self.recent_chats_signal.emit(recent_chats)
        except Exception as e:
            self.error_signal.emit(str(e))

    def run(self):
        self.fetch_data()

class LoadChatThread(QThread):
    chatLoaded = pyqtSignal(list)
    errorOccurred = pyqtSignal(str)

    def __init__(self, parent, client, character_id):
        super().__init__(parent)
        self.parent = parent
        self.client = client
        self.character_id = character_id

        self.ccas = ccas()

    def run(self):
        try:
            self.parent.character = self.ccas.get_character(self.character_id)
            self.parent.setWindowTitle(f"Emilia: Chat With {self.parent.character['name']}")
            chat = self.ccas.get_recent_chat(self.character_id)
            if chat == {}: self.chatLoaded.emit([]); return
            turns = self.ccas.get_all_messages(chat[0]['chat_id'])
            self.chatLoaded.emit(list(reversed(turns)))
        except Exception as e:
            if str(e) == "Failed to get data, status code: 404":
                self.chatLoaded.emit([]); return
            else:
                self.errorOccurred.emit(str(e))

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QPixmap)
    error = pyqtSignal(str)
    save_cache = getconfig("save_cache", True)

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
        if os.path.exists(cache_path) and self.save_cache:
            pixmap.load(cache_path)
            pixmap = pixmap.scaled(self.width, self.height,
                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            self.image_loaded.emit(self.round_qpixmap(pixmap))
            return

        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            if pixmap.loadFromData(response.content) and self.save_cache:
                if not pixmap.save(cache_path):
                    self.error.emit(f"File saving error: {cache_path}")

            pixmap = pixmap.scaled(self.width, self.height,
                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            self.image_loaded.emit(self.round_qpixmap(pixmap))
        except Exception as e:
            self.error.emit(f"Image download error: {e}")
            self.image_loaded.emit(QPixmap())

class SearchLoaderThread(QThread):
    data = pyqtSignal(object)
    error = pyqtSignal(str)
    save_cache_status = getconfig("save_cache", True)

    def __init__(self, url, headers={}, query="", cache_dir="", cache_ttl=86400):
        super().__init__()
        self.url = url
        self.headers = headers
        self.query = query.lower()
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl

        os.makedirs(self.cache_dir, exist_ok=True)

    def get_cache_path(self, query):
        safe_query = query.replace(" ", "_")
        return os.path.join(self.cache_dir, f"{safe_query}.json")

    def load_cache(self, query):
        cache_path = self.get_cache_path(query)
        if os.path.exists(cache_path):
            if time.time() - os.path.getmtime(cache_path) < self.cache_ttl:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        return None

    def save_cache(self, query, data):
        cache_path = self.get_cache_path(query)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def run(self):
        try:
            if self.save_cache_status:
                cached_data = self.load_cache(self.query)
                if cached_data:
                    self.data.emit(cached_data)
                else:
                    response = requests.get(self.url, headers=self.headers)

                    if response.status_code == 200:
                        data = response.json()
                        if self.query: self.save_cache(self.query, data)
                        self.data.emit(data)
                    else:
                        self.error.emit(f"Error receiving data: {response.status_code}")
            else:
                response = requests.get(self.url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    if self.save_cache_status and self.query: self.save_cache(self.query, data)
                    self.data.emit(data)
                else:
                    self.error.emit(f"Error receiving data: {response.status_code}")

        except Exception as e:
            self.error.emit(str(e))

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
                self.error.emit(f"File download error: {response.status_code}")
        except Exception as e:
            self.error.emit(f"File download error: {e}")

class AudioPlayerThread(QThread):
    played = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, parent, audio_array, samplerate):
        super().__init__()
        self.parent = parent
        self.audio_array = audio_array
        self.samplerate = samplerate

    def run(self):
        try:
            self.played.emit(True)
            sd.play(self.audio_array, self.samplerate)
            time.sleep(len(self.audio_array) / self.samplerate)
            sd.stop()
            self.played.emit(False)
        except Exception as e:
            self.error.emit(f"Audio playback error: {e}")