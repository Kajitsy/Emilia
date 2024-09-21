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

from modules.character_search import LoadChatThread
from modules.config import getconfig, resource_path
from modules.eec import EEC
from modules.other import MessageBox
from modules.translations import translations

# Global Variables
vtube_enable = getconfig('vtubeenable', False)
umtranslate = getconfig('umtranslate', False)
aimtranslate = getconfig('aimtranslate', False)
show_notranslate_message = getconfig('show_notranslate_message', True)
lang = getconfig('language', QLocale.system().name())
tts = getconfig('tts', 'charai')
localesfolder = resource_path('locales')
trls = translations(lang, localesfolder)

# Gemini Variables
gemini_model = getconfig('gemini_model', 'gemini-1.5-flash', 'geminiconfig.json')
gemini_harassment = getconfig('harassment', 3, 'geminiconfig.json')
gemini_hate = getconfig('hate', 3, 'geminiconfig.json')
gemini_se_exlicit = getconfig('se_exlicit', 3, 'geminiconfig.json')
gemini_dangerous_content = getconfig('dangerous_content', 3, 'geminiconfig.json')

class MainThreadCharAI(QThread):
    ouinput_signal = pyqtSignal(str, bool, str)
    chatLoaded = pyqtSignal(list)

    def __init__(self, parent, tts):
        super().__init__()
        self.client = aiocai.Client(getconfig("client", configfile="charaiconfig.json"))
        self.parent = parent
        self.tts = tts
        self.vts = EEC()

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
                    result = recognizer.recognize_google(audio, language="ru-RU" if lang == "ru_RU" else "en-US")
                    if not self.parent.microphone_muted:
                        return result
                    else:
                        await asyncio.sleep(0.5)
                except sr.UnknownValueError:
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
        if vtube_enable:
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

                if vtube_enable:
                    await self.vts.UseEmote("Says")

                self.ouinput_signal.emit('zxc', False, self.ai_message + self.ai_message_before_translate if aimtranslate and show_notranslate_message else self.ai_message)

                play(audio, use_ffmpeg=False)
                return

            if vtube_enable:
                await self.vts.UseEmote("Says")

            self.ouinput_signal.emit('zxc', False, self.ai_message + self.ai_message_before_translate if aimtranslate and show_notranslate_message else self.ai_message)

            sd.play(audio, sample_rate)
            await asyncio.sleep(len(audio) / sample_rate)
            sd.stop()
        except Exception as e:
            print(e)
            MessageBox(trls.tr('Errors', 'Label'), str(e))

    async def process_user_input(self):
        recognizer = sr.Recognizer()
        self.character = getconfig('char', configfile='charaiconfig.json')
        self.connect = await self.client.connect()

        if vtube_enable:
            await self.vts.VTubeConnect()

        self.chat = await self.client.get_chat(self.character)

        history = await self.client.get_history(self.chat.chat_id)
        self.chatLoaded.emit(list(reversed(history.turns)))

        if self.tts == 'elevenlabs':
            self.elevenlabs = ElevenLabs(api_key=getconfig('elevenlabs_api_key'))

        while True:
            if vtube_enable:
                await self.vts.UseEmote("Listening")

            user_message = await self.recognize_speech(recognizer)

            if umtranslate:
                while True:
                    try:
                        user_message_translate = await Translator().translate(user_message, targetlang="en")
                        break
                    except:
                        pass
                user_message_before_translate = f'<p style="color: gray; font-style: italic; font-size: 12px;">{user_message}</p>'
                user_message = user_message_translate.text

            self.ouinput_signal.emit('zxc', True, user_message + user_message_before_translate if umtranslate and show_notranslate_message else user_message)

            self.message = await self.generate_ai_response(user_message)
            self.ai_message = self.message.text

            if aimtranslate:
                while True:
                    try:
                        self.ai_message_translate = await Translator().translate(self.ai_message, targetlang="ru")
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

class MainThreadGemini(QThread):
    ouinput_signal = pyqtSignal(str, bool, str)

    def __init__(self, parent, tts):
        super().__init__()
        self.model = genai.GenerativeModel(gemini_model)
        self.chat = self.model.start_chat(history=[])
        self.parent = parent
        genai.configure(api_key=self.parent.gemini_token_entry.text())
        self.tts = tts

    async def generate_ai_response(self, text):
        try:
            self.chunk = self.chat.send_message(text, safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: gemini_harassment,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: gemini_hate,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: gemini_se_exlicit,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: gemini_dangerous_content
                })
            return self.chunk
        except Exception as e:
            if e.code == 400 and "User location is not supported" in e.message:
                MessageBox(trls.tr('Errors', 'Label') + trls.tr('Errors', 'Gemini 400'))
            else:
                MessageBox(trls.tr('Errors', 'Label') + str(e))
            return ""

    async def recognize_speech(self, recognizer):
        while True:
            if not self.parent.microphone_muted:
                try:
                    audio = await self.listen_to_microphone(recognizer)
                    result = recognizer.recognize_google(audio, language="ru-RU" if lang == "ru_RU" else "en-US")
                    if not self.parent.microphone_muted:
                        return result
                    else:
                        await asyncio.sleep(0.5)
                except sr.UnknownValueError:
                    print('aboba')
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
                play(audio, use_ffmpeg=False)
                return
        except Exception as e:
            print(e)
            MessageBox(trls.tr('Errors', 'Label'), str(e))

    async def process_user_input(self):
        recognizer = sr.Recognizer()
        t = Translator()

        if self.tts == 'elevenlabs':
            self.elevenlabs = ElevenLabs(api_key=getconfig('elevenlabs_api_key'))

        while True:
            user_message = await self.recognize_speech(recognizer)

            if umtranslate:
                user_message_translate = await t.translate(user_message, targetlang="en")
                user_message_before_translate = f'<p style="color: gray; font-style: italic; font-size: 12px;">{user_message}</p>'
                user_message = user_message_translate.text

            self.ouinput_signal.emit('zxc', True, user_message + user_message_before_translate if umtranslate and show_notranslate_message else user_message)

            message = await self.generate_ai_response(user_message)
            ai_message = message.text

            if aimtranslate:
                ai_message_translate = await t.translate(ai_message, targetlang="ru")
                ai_message_before_translate = f'<p style="color: gray; font-style: italic; font-size: 12px;">{ai_message}</p>'
                ai_message = ai_message_translate.text

            await self.play_audio_response(ai_message)

            self.ouinput_signal.emit('zxc', False, ai_message + ai_message_before_translate if aimtranslate and show_notranslate_message else ai_message)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.process_user_input())

