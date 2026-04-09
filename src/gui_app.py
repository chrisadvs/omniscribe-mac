import rumps
import threading
import os
from src.config_manager import ConfigManager
from src.audio_capture import OmniRecorder
from src.speech_engine import SpeechEngineFactory
from src.text_injector import TextInjector
from src.settings_server import SettingsServer
from src.utils.logger import logger

# Dynamically locate the project root to avoid path drift after packaging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OmniScribeApp(rumps.App):
    def __init__(self):
        icon_path = os.path.join(BASE_DIR, "assets", "icon_idle.png")
        super(OmniScribeApp, self).__init__("OmniScribe", icon=icon_path)

        self.config_mgr = ConfigManager()
        self.config = self.config_mgr.load_config()

        # Pending icon state flag — set by background thread, consumed by main thread timer
        self._pending_icon_state = None

        # Settings web server — lazy start on first open
        self.settings_server = SettingsServer(self.config_mgr)

        self.menu = [
            rumps.MenuItem("Settings", callback=self.open_settings),
            rumps.MenuItem("View Logs", callback=self.view_logs),
            rumps.separator,
            rumps.MenuItem("Quit OmniScribe", callback=rumps.quit_application)
        ]

        self.start_background_pipeline()

    def start_background_pipeline(self):
        logger.info("Initializing Core Pipeline Thread...")
        self.recorder = OmniRecorder(
            callback_ui_update=self.update_icon_state,
            callback_process_audio=self.process_audio_pipeline
        )
        hotkey = self.config.get("hotkey", "<cmd>+<shift>+u")
        threading.Thread(target=self.recorder.start_listening, args=(hotkey,), daemon=True).start()

    def process_audio_pipeline(self, audio_filepath: str):
        # Always reload config so engine changes take effect without restart
        current_config = self.config_mgr.load_config()
        engine = SpeechEngineFactory(current_config)
        text = engine.transcribe(audio_filepath)
        if text:
            injector = TextInjector(current_config)
            injector.output(text)

    def update_icon_state(self, is_recording: bool):
        # Called from background thread — only set the flag, never touch UI directly
        self._pending_icon_state = is_recording

    @rumps.timer(0.2)
    def _sync_icon(self, _):
        # Runs on the main thread every 0.2s — safe to update UI here
        if self._pending_icon_state is not None:
            name = "icon_active.png" if self._pending_icon_state else "icon_idle.png"
            self.icon = os.path.join(BASE_DIR, "assets", name)
            self._pending_icon_state = None

    def open_settings(self, _):
        # Open settings in browser — no thread issues, works from any callback
        threading.Thread(target=self.settings_server.open, daemon=True).start()

    def view_logs(self, _):
        log_path = os.path.expanduser("~/Library/Application Support/OmniScribe/omniscribe.log")
        os.system(f'open "{log_path}"')


if __name__ == "__main__":
    OmniScribeApp().run()