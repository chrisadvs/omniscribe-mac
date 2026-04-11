import time
import requests
import google.generativeai as genai
from openai import OpenAI
from src.utils.logger import logger

class SpeechEngineFactory:
    def __init__(self, config):
        self.engine_type = config.get("active_engine", "gemini")
        self.gemini_api_key = config.get("gemini_api_key", "")
        self.gemini_model = config.get("gemini_model", "")
        self.openai_api_key = config.get("openai_api_key", "")
        self.whisper_prompt = config.get("whisper_prompt", "")
        self.whisper_local_host = config.get("whisper_local_host", "")
        self.prompt = (
            "You are a transcription engine. Transcribe the audio exactly as spoken. "
            "Output in Simplified Chinese (简体中文) if the speaker uses Chinese. "
            "If the speaker mixes English and Chinese, keep both languages as spoken. "
            "No explanations, no markdown, no filler words. Output transcription only."
        )

    def transcribe(self, path):
        if self.engine_type == "gemini":
            return self._run_gemini(path)
        elif self.engine_type == "whisper":
            return self._run_whisper(path)
        elif self.engine_type == "whisper_local":
            return self._run_whisper_local(path)
        logger.error(f"Unknown engine type: {self.engine_type}")
        return ""

    def _run_gemini(self, path):
        if not self.gemini_api_key:
            logger.error("Gemini API key is missing.")
            return ""
        if not self.gemini_model:
            logger.error("Gemini model name is missing. Please set it in Settings.")
            return ""
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.gemini_model)

            sample_file = genai.upload_file(path=path)
            logger.info(f"File uploaded to Gemini: {sample_file.name}")

            while sample_file.state.name == "PROCESSING":
                logger.debug("Waiting for Gemini to process audio...")
                time.sleep(1)
                sample_file = genai.get_file(sample_file.name)

            if sample_file.state.name == "FAILED":
                logger.error("Gemini file processing failed.")
                return ""

            response = model.generate_content([self.prompt, sample_file])
            genai.delete_file(sample_file.name)

            result = response.text.strip()
            logger.info(f"Transcription result: {result}")
            return result
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return ""

    def _run_whisper(self, path):
        if not self.openai_api_key:
            logger.error("OpenAI API key is missing.")
            return ""
        try:
            client = OpenAI(api_key=self.openai_api_key)
            with open(path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    prompt=self.whisper_prompt
                )
            result = transcription.text.strip()
            logger.info(f"Transcription result: {result}")
            return result
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            return ""

    def _run_whisper_local(self, path):
        if not self.whisper_local_host:
            logger.error("Whisper Local host is missing. Please set it in Settings.")
            return ""
        try:
            logger.info("[TIMER] Sending audio to Whisper Local server...")
            t_start = time.time()

            url = f"{self.whisper_local_host}/transcribe"
            with open(path, "rb") as f:
                files = {"file": ("audio.wav", f, "audio/wav")}
                response = requests.post(url, files=files, timeout=60)

            t_upload_done = time.time()
            logger.info(f"[TIMER] Server responded in {t_upload_done - t_start:.2f}s")

            if response.status_code == 200:
                result = response.json().get("text", "").strip()
                logger.info(f"Transcription result: {result}")
                return result
            else:
                logger.error(f"Whisper Local error: {response.status_code} {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Whisper Local error: {e}")
            return ""