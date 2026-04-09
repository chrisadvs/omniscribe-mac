import time
import requests
import google.generativeai as genai
from openai import OpenAI
from src.utils.logger import logger

class SpeechEngineFactory:
    def __init__(self, config):
        self.engine_type = config.get("active_engine", "gemini")
        self.gemini_api_key = config.get("gemini_api_key", "")
        self.openai_api_key = config.get("openai_api_key", "")
        self.ollama_host = config.get("ollama_host", "http://mac-mini.local:11434")
        self.ollama_model = config.get("ollama_model", "gemma4:e4b")
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
        elif self.engine_type == "ollama":
            return self._run_ollama(path)
        logger.error(f"Unknown engine type: {self.engine_type}")
        return ""

    def _run_gemini(self, path):
        if not self.gemini_api_key:
            logger.error("Gemini API key is missing.")
            return ""
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-3-flash-preview')

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
                    prompt="SRE, Kubernetes, Splunk, Azure, API."
                )
            result = transcription.text.strip()
            logger.info(f"Transcription result: {result}")
            return result
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            return ""

    def _run_ollama(self, path):
        # Ollama does not support audio natively.
        # We use whisper.cpp or a local transcription step first,
        # then send the text to Ollama for cleanup/formatting.
        # For now, we use Ollama's OpenAI-compatible API to transcribe
        # via its /api/transcribe endpoint if available, otherwise log unsupported.
        try:
            url = f"{self.ollama_host}/api/transcribe"
            with open(path, "rb") as f:
                files = {"file": ("audio.wav", f, "audio/wav")}
                data = {"model": self.ollama_model}
                response = requests.post(url, files=files, data=data, timeout=60)

            if response.status_code == 200:
                result = response.json().get("text", "").strip()
                logger.info(f"Transcription result: {result}")
                return result
            else:
                logger.error(f"Ollama transcription failed: {response.status_code} {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return ""