import io
import logging
import time

import scipy.signal
import sounddevice
import soundfile
from PyQt6.QtCore import QThread, pyqtSignal


class PlayerThread(QThread):
    play_signal = pyqtSignal(object)
    stop_signal = pyqtSignal(object)

    def __init__(self, data):
        super().__init__()
        self.data = data
        self._is_running = False

    def run(self):
        self._is_running = True
        self.play(self.data)

    def play(self, data):
        try:
            audio_bytes = io.BytesIO(data)
            audio_array, sample_rate = soundfile.read(audio_bytes)

            target_rate = 44100
            if sample_rate != target_rate:
                new_length = int(round(len(audio_array) * target_rate / sample_rate))
                audio_array = scipy.signal.resample(audio_array, new_length)
                sample_rate = target_rate

            self.play_signal.emit(True)
            sounddevice.play(audio_array, sample_rate)

            duration = len(audio_array) / sample_rate
            time.sleep(duration)

            sounddevice.stop()
        except Exception as e:
            logging.error(f"PlayerThread Error: {e}")
        finally:
            self.stop_signal.emit(True)
            self._is_running = False

    def stop(self):
        if self._is_running:
            sounddevice.stop()
            self._is_running = False
            self.stop_signal.emit(True)
