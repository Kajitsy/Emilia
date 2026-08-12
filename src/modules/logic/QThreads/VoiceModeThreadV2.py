import asyncio
import logging

import curl_cffi.curl
import numpy as np
import sounddevice
from livekit import rtc
from PyQt6.QtCore import QThread, pyqtSignal

from modules.logic.VTubeCore import EEC


class VoiceModeThreadV2(QThread):
    connected_signal = pyqtSignal(bool)
    speech_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)
    volume_signal = pyqtSignal(float)

    def __init__(
        self, parent, token, char, chat_id, username, char_name=None, voice_id=None
    ):
        super().__init__()
        self.parent = parent
        self.mw = self.parent.mw
        self.token = token
        self.char = char
        self.chat_id = chat_id
        self.username = username
        self.char_name = char_name
        self.voice_id = voice_id

        input_dev = self.mw.settings.value("input_device", False)
        self.input_index = (
            0
            if input_dev is False
            else self.mw.settings.value("input_device", 0, type=int) + 1
        )
        output_dev = self.mw.settings.value("output_device", False)
        self.output_index = (
            0
            if output_dev is False
            else self.mw.settings.value("output_device", 0, type=int)
        )

        self.room = None
        self.output_stream = None
        self.is_bot_speaking = False
        self.vtube_studio = self.mw.settings.value("vtube/use", False, type=bool)
        self.eec = EEC(
            self.mw,
            self.mw.settings.value("vtube/address", "127.0.0.1"),
            self.mw.settings.value("vtube/port", 8001),
        )

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.stop_event = asyncio.Event()

        try:
            self.loop.run_until_complete(self.start_call())
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).error(f"Critical Error in run: {e}")
            self.error_signal.emit(str(e))
        finally:
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            if pending:
                self.loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            self.loop.close()

    async def start_call(self):
        self.session = curl_cffi.AsyncSession()
        self.room = rtc.Room()
        self.audio_devices = rtc.MediaDevices()

        url = "https://neo.character.ai/multimodal/api/v1/sessions/joinOrCreateSession"
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0",
        }

        if self.voice_id:
            payload = {
                "enableASR": True,
                "platform": "web",
                "roomId": self.chat_id,
                "rtcBackend": "lk",
                "userAuthToken": self.token,
                "username": self.username,
                "voiceQueries": {},
                "voices": {self.char: self.voice_id},
            }
        else:
            payload = {
                "enableASR": True,
                "platform": "web",
                "roomId": self.chat_id,
                "rtcBackend": "lk",
                "userAuthToken": self.token,
                "username": self.username,
                "voiceQueries": {self.char: self.char_name},
                "voices": {},
            }

        async with curl_cffi.AsyncSession() as session:
            request = await session.post(
                url, headers=headers, json=payload, timeout=100
            )
            data = request.json()
            call_token = data["lkToken"]
            ws_url = data["lkUrl"]

            await self.connect_livekit(ws_url, call_token)

    def set_mute(self, is_muted: bool):
        if self.mic_track:
            if is_muted:
                self.mic_track.mute()
            else:
                self.mic_track.unmute()

    async def connect_livekit(self, url, token):
        @self.room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                asyncio.create_task(self.handle_incoming_audio(track))

        try:
            self.output_stream = sounddevice.OutputStream(
                channels=1, samplerate=48000, dtype="int16", device=self.output_index
            )
            self.output_stream.start()
            await self.room.connect(url, token)
            self.connected_signal.emit(True)
            await self._enable_microphone()
            await self.stop_event.wait()

        except Exception as e:  # noqa: BLE001
            await self.room.disconnect()
            self.error_signal.emit(f"LiveKit error: {e}")
        finally:
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()
            await self.room.disconnect()
            self.connected_signal.emit(False)

    async def handle_incoming_audio(self, track):
        audio_stream = rtc.AudioStream(track)

        silence_timer = 0
        silence_threshold = 1

        async for event in audio_stream:
            if self.stop_event.is_set():
                break

            frame = event.frame
            if not frame:
                continue
            data_np = np.frombuffer(frame.data, dtype=np.int16)

            self.output_stream.write(data_np)

            if len(data_np) > 0:
                rms = np.max(np.abs(data_np))
                volume = min(1.0, float(rms) / 32768.0)
            else:
                rms = 0
                volume = 0.0

            self.volume_signal.emit(volume)

            if rms > 500:
                if not self.is_bot_speaking:
                    self.is_bot_speaking = True
                    if self.vtube_studio:
                        await self.eec.UseEmote("Says")
                    self.speech_signal.emit(False)
                silence_timer = 0
            else:
                if self.is_bot_speaking:
                    silence_timer += 0.01

                    if silence_timer > silence_threshold:
                        self.is_bot_speaking = False
                        if self.vtube_studio:
                            await self.eec.UseEmote("Listening")
                        self.speech_signal.emit(True)

    async def _enable_microphone(self):
        mic_device = self.audio_devices.open_input(
            input_device=self.input_index, enable_aec=True, noise_suppression=True
        )
        self.mic_track = rtc.LocalAudioTrack.create_audio_track(
            "microphone", mic_device.source
        )

        await self.room.local_participant.publish_track(self.mic_track)
        self.speech_signal.emit(True)

    def stop_call(self):
        if hasattr(self, "loop") and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._safe_stop(), self.loop)

    async def _safe_stop(self):
        if hasattr(self, "stop_event"):
            self.stop_event.set()
