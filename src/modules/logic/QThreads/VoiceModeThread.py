import logging, sounddevice, soundfile, io, asyncio, inspect, json

import curl_cffi.curl
import requests, speech_recognition
from PyQt6.QtCore import QThread, pyqtSignal

from modules.logic.VTubeCore import EEC

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
        self.token = token
        self.char = char
        self.chat_id = chat_id
        self.voice_id = voice_id
        self.muted = self.mw.muted
        self.lang = self.mw.current_language
        self.used_emotes = []

        self.session = curl_cffi.AsyncSession()
        self.ws = None
        self.chat_thread = self.mw.chat_thread
        self.recognizer = speech_recognition.Recognizer()
        self.eec = EEC(self.mw, self.mw.settings.value("vtube/address", "127.0.0.1"), self.mw.settings.value("vtube/port", 8001))
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

    async def request(self, endpoint, data = {}):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0"
        }

        response = await self.session.request('POST', f"https://neo.character.ai/{endpoint}", headers=headers, json=data, timeout=100)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get data, status code: {response.status_code}")

    async def tts(self, candidateId, roomId, turnId, voiceId: str = "", voiceQuery: str = ""):
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
        response = await self.request("multimodal/api/v1/memo/replay", data)
        link = response["replayUrl"]
        download = requests.get(link, stream=True)
        if download.status_code == 200:
            audio_bytes = io.BytesIO(download.content)
            audio_array, sample_rate = soundfile.read(audio_bytes)
            return audio_array, sample_rate

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

    async def send_message(self, text):
        while True:
            try:
                async for response in self._send_message(self.char, self.chat_id, text):
                    if not response['turn']['author']['author_id'].isdigit():
                            if response.get('turn', {}).get('candidates', [])[0].get('is_final'):
                                return response['turn']
            except curl_cffi.curl.CurlError:
                self.connected_signal.emit(False)
                self.ws = await self.session.ws_connect('wss://neo.character.ai/ws/', cookies={'HTTP_AUTHORIZATION': f'Token {self.token}'},
                                                        autoclose=False)
                self.connected_signal.emit(True)

    async def process_user_input(self):
        self.ws = await self.session.ws_connect('wss://neo.character.ai/ws/', cookies={'HTTP_AUTHORIZATION': f'Token {self.token}'}, autoclose=False)
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
