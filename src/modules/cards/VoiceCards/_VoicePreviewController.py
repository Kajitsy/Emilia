from modules.style.Icons import Svg
from modules.QThreads import PlayerThread, FileLoaderThread

class _VoicePreviewController:
    def __init__(self, main_window):
        self.mw = main_window
        self.svg_icons = Svg()
        self.active_loader = None
        self.active_player = None
        self.active_button = None
        self.is_playing = False
        self.is_loading = False

    def _set_button_play(self, button):
        if button:
            button.setIcon(self.svg_icons.play())

    def _set_button_pause(self, button):
        if button:
            button.setIcon(self.svg_icons.pause())

    def _reset_state(self):
        self.active_loader = None
        self.active_player = None
        self.active_button = None
        self.is_playing = False
        self.is_loading = False

    def stop(self):
        if self.active_player:
            self.active_player.stop()
        if self.active_button:
            self._set_button_play(self.active_button)
        self._reset_state()

    def toggle(self, url, button):
        if not url:
            return
        if self.active_button is button and (self.is_playing or self.is_loading):
            self.stop()
            return

        self.stop()
        self.active_button = button
        self.is_loading = True

        loader = FileLoaderThread(url)
        self.active_loader = loader
        self.mw.threads.append(loader)
        loader.file.connect(lambda data, loader_ref=loader: self._start_player(loader_ref, data))
        loader.start()

    def _start_player(self, loader, data):
        if loader is not self.active_loader:
            return
        self.is_loading = False
        player = PlayerThread(data)
        self.active_player = player
        self.mw.threads.append(player)
        player.play_signal.connect(lambda _: self._on_play(player))
        player.stop_signal.connect(lambda _: self._on_stop(player))
        player.start()

    def _on_play(self, player):
        if player is not self.active_player:
            return
        self.is_playing = True
        self._set_button_pause(self.active_button)

    def _on_stop(self, player):
        if player is not self.active_player:
            return
        self._set_button_play(self.active_button)
        self._reset_state()

def _preview_controller(main_window):
    if not hasattr(main_window, "_voice_preview_controller"):
        main_window._voice_preview_controller = _VoicePreviewController(main_window)
    return main_window._voice_preview_controller