import time
import pyperclip
from pynput.keyboard import Controller, Key
from src.utils.logger import logger

class TextInjector:
    def __init__(self, config):
        self.mode = config.get("output_mode", "type")
        self.keyboard = Controller()

    def output(self, text: str):
        if not text:
            return

        logger.info(f"Injecting text via {self.mode} mode.")
        if self.mode == "type":
            self._simulate_typing(text)
        else:
            self._clipboard_injection(text)

    def _simulate_typing(self, text: str):
        # Small buffer to allow focus to settle
        time.sleep(0.3)
        self.keyboard.type(text)

    def _clipboard_injection(self, text: str):
        # Write transcribed text to clipboard
        pyperclip.copy(text)

        # Wait longer to ensure clipboard write is complete before triggering paste
        time.sleep(0.5)

        # Simulate Cmd+V
        with self.keyboard.pressed(Key.cmd):
            self.keyboard.press('v')
            self.keyboard.release('v')

        # Wait for paste to complete before any further action
        time.sleep(0.3)