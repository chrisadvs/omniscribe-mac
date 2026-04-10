import json
import os
from src.utils.logger import logger

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/Library/Application Support/OmniScribe")
        self.config_path = os.path.join(self.config_dir, "config.json")
        self._ensure_config_exists()

    def _default_config(self) -> dict:
        return {
            "active_engine": "gemini",
            "gemini_api_key": "",
            "gemini_model": "",
            "openai_api_key": "",
            "whisper_prompt": "",
            "whisper_local_host": "",
            "output_mode": "clipboard",
            "hotkey": "<cmd>+<shift>+u"
        }

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
        if not os.path.exists(self.config_path):
            self.save_config(self._default_config())

    def load_config(self) -> dict:
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            # Migrate old single api_key field to new structure if needed
            if "api_key" in data and "gemini_api_key" not in data:
                logger.info("Migrating old config format to new structure.")
                data["gemini_api_key"] = data.pop("api_key")
                data.setdefault("gemini_model", "")
                data.setdefault("openai_api_key", "")
                data.setdefault("whisper_prompt", "")
                data.setdefault("whisper_local_host", "")
                self.save_config(data)
            return data
        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            logger.error(f"Config corrupted or missing ({e}), resetting to default.")
            default = self._default_config()
            self.save_config(default)
            return default

    def save_config(self, config_dict: dict):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")