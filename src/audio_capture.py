import queue
import threading
import os
import sounddevice as sd
import soundfile as sf
from pynput import keyboard
from src.utils.logger import logger

class OmniRecorder:
    def __init__(self, callback_ui_update, callback_process_audio):
        self.filename = os.path.expanduser("~/Library/Application Support/OmniScribe/temp.wav")
        self.is_recording = False
        self.lock = threading.Lock()
        self.audio_queue = queue.Queue()
        self.callback_ui_update = callback_ui_update
        self.callback_process_audio = callback_process_audio

    def _record_worker(self):
        self.callback_ui_update(True)
        try:
            with sf.SoundFile(self.filename, mode='w', samplerate=16000, channels=1) as f:
                with sd.InputStream(samplerate=16000, channels=1,
                                    callback=lambda i, fr, t, s: self.audio_queue.put(i.copy())):
                    while self.is_recording:
                        try:
                            # Timeout prevents the thread from blocking forever
                            data = self.audio_queue.get(timeout=0.5)
                            f.write(data)
                        except queue.Empty:
                            continue

                # Drain any remaining frames from the queue
                while not self.audio_queue.empty():
                    try:
                        f.write(self.audio_queue.get_nowait())
                    except queue.Empty:
                        break

        except Exception as e:
            logger.error(f"Recording error: {e}")
        finally:
            self.callback_ui_update(False)
            self.callback_process_audio(self.filename)

    def toggle(self):
        with self.lock:
            self.is_recording = not self.is_recording
            if self.is_recording:
                # Clear any leftover audio data before starting a new recording
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        break
                threading.Thread(target=self._record_worker, daemon=True).start()

    def start_listening(self, hotkey):
        logger.info(f"Hotkey listener active on: {hotkey}")
        with keyboard.GlobalHotKeys({hotkey: self.toggle}) as h:
            h.join()