import io, asyncio, re
import requests, websockets

import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import google.generativeai as genai
import modules.CustomCharAI as CustomCharAI

from gpytranslate import Translator
from elevenlabs.client import ElevenLabs
from characterai import aiocai
from elevenlabs import VoiceSettings, play
from google.generativeai.types import HarmCategory

from PyQt6.QtCore import QThread, pyqtSignal, QLocale
from PyQt6.QtGui import QPixmap

from modules.config import getconfig, resource_path
from modules.eec import EEC
from modules.other import MessageBox
from modules.translations import translations

class MainThreadCharAI(QThread):
    ouinput_signal = pyqtSignal(str, object, str, int, object, object)
    chatLoaded = pyqtSignal(list)

    def __init__(self, parent, tts):
        super().__init__()
        self.client = aiocai.Client(getconfig("client", configfile="charaiconfig.json"))
        self.parent = parent
        self.tts = tts
        self.vts = EEC()

        self.vtube_enable = getconfig('vtubeenable', False)
        self.umtranslate = getconfig('umtranslate', False)
        self.aimtranslate = getconfig('aimtranslate', False)
        self.show_notranslate_message = getconfig('show_notranslate_message', True)
        self.show_system_messages = getconfig('show_system_messages', True)
        self.lang = getconfig('language', QLocale.system().name())
        self.localesfolder = resource_path('locales')
        self.trls = translations(self.lang, self.localesfolder)

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
                        self.ouinput_signal.emit('zxc', 'sys', 'Repeat...', 0, False, False)
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

        response = await CustomCharAI.tts(candidateId, roomId, turnId, voiceId, voiceQuery)
        link = response["replayUrl"]
        download = requests.get(link, stream=True)
        if download.status_code == 200: 
            audio_bytes = io.BytesIO(download.content)
            audio_array, samplerate = sf.read(audio_bytes)
            return audio_array, samplerate

    async def play_audio_response(self, text):
        if self.vtube_enable:
            await self.vts.UseEmote("Thinks")

        try:
            if self.tts == 'charai':
                audio, sample_rate = await self.charai_tts()
            elif self.tts == 'elevenlabs':
                audio = self.elevenlabs.generate(
                    voice=getconfig('elevenlabs_voice', configfile='charaiconfig.json'),
                    output_format='mp3_22050_32',
                    text=text,
                    model='eleven_multilingual_v2',
                    voice_settings=VoiceSettings(
                        stability=0.2,
                        similarity_boost=0.8,
                        style=0.4,
                        use_speaker_boost=True,
                    )
                )

                if self.vtube_enable:
                    await self.vts.UseEmote("Says")

                self.ouinput_signal.emit('zxc', 'ai', text + self.ai_message_before_translate if self.aimtranslate and self.show_notranslate_message else text, len(text), True, True if self.aimtranslate and self.show_notranslate_message else False)

                play(audio, use_ffmpeg=False)
                return

            if self.vtube_enable:
                await self.vts.UseEmote("Says")

            audio_len = len(audio)
            self.ouinput_signal.emit('zxc', 'ai', text + self.ai_message_before_translate if self.aimtranslate and self.show_notranslate_message else text, audio_len, True, True if self.aimtranslate and self.show_notranslate_message else False)

            sd.play(audio, sample_rate)
            await asyncio.sleep(len(audio) / sample_rate)
            sd.stop()
        except Exception as e:
            print(e)
            MessageBox(self.trls.tr('Errors', 'Label'), str(e))

    async def process_user_input(self):
        self.recognizer = sr.Recognizer()
        self.character = getconfig('char', configfile='charaiconfig.json')
        self.connect = await self.client.connect()

        if self.vtube_enable:
            await self.vts.VTubeConnect()

        self.chat = await self.client.get_chat(self.character)

        if self.show_system_messages:
            self.ouinput_signal.emit('zxc', 'sys', 'Your recent messages', 0, False, False)

        history = await self.client.get_history(self.chat.chat_id)
        self.chatLoaded.emit(list(reversed(history.turns)))

        if self.tts == 'elevenlabs':
            self.elevenlabs = ElevenLabs(api_key=getconfig('elevenlabs_api_key'))

        if self.show_system_messages:
            self.ouinput_signal.emit('zxc', 'sys', 'You can start', 0, False, False)

        while True:
            if self.vtube_enable:
                await self.vts.UseEmote("Listening")

            user_message = await self.recognize_speech(self.recognizer)

            if self.umtranslate:
                while True:
                    try:
                        user_message_translate = await Translator().translate(user_message, targetlang="en")
                        break
                    except:
                        pass
                user_message_before_translate = f'<p style="color: gray; font-style: italic; font-size: 12px;">{user_message}</p>'
                user_message = user_message_translate.text

            self.ouinput_signal.emit('zxc', 'human', user_message + user_message_before_translate if self.umtranslate and self.show_notranslate_message else user_message, len(user_message), True, True if self.aimtranslate and self.show_notranslate_message else False)

            self.message = await self.generate_ai_response(user_message)

            self.ai_message = self.message.text

            if self.aimtranslate:
                while True:
                    try:
                        self.ai_message_translate = await Translator().translate(self.ai_message, targetlang=self.lang)
                        break
                    except:
                        pass
                self.ai_message_before_translate = f'<p style="color: gray; font-style: italic; font-size: 12px;">{self.ai_message}</p>'
                self.ai_message = self.ai_message_translate.text

            await self.play_audio_response(self.ai_message)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.process_user_input())

class MainThreadGemini(QThread):
    ouinput_signal = pyqtSignal(str, object, str, int, object, object)

    def __init__(self, parent, tts):
        super().__init__()
        self.gemini_model = getconfig('gemini_model', 'gemini-1.5-flash', 'geminiconfig.json')
        self.model = genai.GenerativeModel(self.gemini_model)
        self.chat = self.model.start_chat(history=[])
        self.parent = parent
        genai.configure(api_key=self.parent.gemini_token_entry.text())
        self.tts = tts

        self.vtube_enable = getconfig('vtubeenable', False)
        self.umtranslate = getconfig('umtranslate', False)
        self.aimtranslate = getconfig('aimtranslate', False)
        self.show_notranslate_message = getconfig('show_notranslate_message', True)
        self.show_system_messages = getconfig('show_system_messages', True)
        self.lang = getconfig('language', QLocale.system().name())
        self.localesfolder = resource_path('locales')
        self.trls = translations(self.lang, self.localesfolder)

        self.gemini_model = getconfig('gemini_model', 'gemini-1.5-flash', 'geminiconfig.json')
        self.gemini_harassment = getconfig('harassment', 3, 'geminiconfig.json')
        self.gemini_hate = getconfig('hate', 3, 'geminiconfig.json')
        self.gemini_se_exlicit = getconfig('se_exlicit', 3, 'geminiconfig.json')
        self.gemini_dangerous_content = getconfig('dangerous_content', 3, 'geminiconfig.json')

        self.parent.send_user_message_button.clicked.connect(self.handle_button_clicked)
        self.parent.user_input.returnPressed.connect(self.handle_return_pressed)

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
                MessageBox(self.trls.tr('Errors', 'Label') + self.trls.tr('Errors', 'Gemini 400'))
            else:
                MessageBox(self.trls.tr('Errors', 'Label') + str(e))
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
                        self.ouinput_signal.emit('zxc', 'sys', 'Repeat...', 0, False, False)
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
            if self.tts == 'elevenlabs':
                audio = self.elevenlabs.generate(
                    voice=getconfig('elevenlabs_voice', configfile='charaiconfig.json'),
                    output_format='mp3_22050_32',
                    text=text,
                    model='eleven_multilingual_v2',
                    voice_settings=VoiceSettings(
                        stability=0.2,
                        similarity_boost=0.8,
                        style=0.4,
                        use_speaker_boost=True,
                    )
                )

                if self.vtube_enable:
                    await self.vts.UseEmote("Says")

                self.ouinput_signal.emit('zxc', 'ai', text + self.ai_message_before_translate if self.aimtranslate and self.show_notranslate_message else text, len(text), True, True if self.aimtranslate and self.show_notranslate_message else False)

                play(audio, use_ffmpeg=False)
        except Exception as e:
            print(e)
            MessageBox(self.trls.tr('Errors', 'Label'), str(e))

    async def process_user_input(self):
        recognizer = sr.Recognizer()

        if self.vtube_enable:
            await self.vts.VTubeConnect()

        if self.tts == 'elevenlabs':
            self.elevenlabs = ElevenLabs(api_key=getconfig('elevenlabs_api_key'))

        if self.show_system_messages:
            self.ouinput_signal.emit('zxc', 'sys', 'You can start', 0, False, False)

        while True:
            if self.vtube_enable:
                await self.vts.UseEmote("Listening")

            user_message = await self.recognize_speech(recognizer)

            if self.umtranslate:
                try:
                    user_message_translate = await Translator().translate(user_message, targetlang="en")
                    break
                except:
                    pass
                user_message_before_translate = f'<p style="color: gray; font-style: italic; font-size: 12px;">{user_message}</p>'
                user_message = user_message_translate.text

            self.ouinput_signal.emit('zxc', 'human', user_message + user_message_before_translate if self.umtranslate and self.show_notranslate_message else user_message, len(user_message), True, True if self.aimtranslate and self.show_notranslate_message else False)

            self.message = await self.generate_ai_response(user_message)
            self.ai_message = self.message.text

            if self.aimtranslate:
                while True:
                    try:
                        self.ai_message_translate = await Translator().translate(self.ai_message, targetlang=self.lang)
                        break
                    except:
                        pass
                self.ai_message_before_translate = f'<p style="color: gray; font-style: italic; font-size: 12px;">{self.ai_message}</p>'
                self.ai_message = self.ai_message_translate.text

            await self.play_audio_response(self.ai_message)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.process_user_input())

class ChatDataWorker(QThread):
    recommend_chats_signal = pyqtSignal(object)
    recent_chats_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, custom_char_ai):
        super().__init__()
        self.custom_char_ai = custom_char_ai

    async def fetch_data(self):
        try:
            recommend_chats = await CustomCharAI.get_recommend_chats()
            recent_chats = await CustomCharAI.get_recent_chats()
            self.recommend_chats_signal.emit(recommend_chats)
            self.recent_chats_signal.emit(recent_chats)
        except Exception as e:
            self.error_signal.emit(str(e))

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetch_data())

class LoadChatThread(QThread):
    finished = pyqtSignal()
    chatLoaded = pyqtSignal(list)
    errorOccurred = pyqtSignal(str)

    def __init__(self, parent, client, character_id):
        super().__init__(parent)
        self.parent = parent
        self.client = client
        self.character_id = character_id

    async def load_chat_async(self):
        try:
            self.parent.character = await CustomCharAI.get_character(self.character_id)
            self.parent.setWindowTitle(f'Emilia: Chat With {self.parent.character["name"]}')
            chat = await self.client.get_chat(self.character_id)
            history = await self.client.get_history(chat.chat_id)
            self.chatLoaded.emit(list(reversed(history.turns)))
        except Exception as e:
            self.errorOccurred.emit(str(e))

    def run(self):
        asyncio.run(self.load_chat_async())
        self.finished.emit()

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QPixmap)
    
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            image = QPixmap()
            image.loadFromData(response.content)
            self.image_loaded.emit(image)
        except:
            self.image_loaded.emit(QPixmap())
