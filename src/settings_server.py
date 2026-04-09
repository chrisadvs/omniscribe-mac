import threading
import webbrowser
from flask import Flask, request, jsonify, render_template_string
from src.utils.logger import logger

SETTINGS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OmniScribe Settings</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    background: #f5f5f7;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    padding: 40px 16px;
  }

  .card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
    width: 100%;
    max-width: 520px;
    padding: 36px 40px 32px;
  }

  h1 {
    font-size: 22px;
    font-weight: 700;
    color: #1d1d1f;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  h1 span.dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    background: #007AFF;
    display: inline-block;
  }

  .section-label {
    font-size: 11px;
    font-weight: 600;
    color: #6e6e73;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
    margin-top: 24px;
  }

  .engine-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 4px;
  }

  .engine-btn {
    border: 2px solid #e0e0e5;
    border-radius: 10px;
    padding: 12px 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.15s;
    background: white;
    font-size: 13px;
    font-weight: 500;
    color: #3a3a3c;
  }

  .engine-btn:hover { border-color: #007AFF; color: #007AFF; }
  .engine-btn.active {
    border-color: #007AFF;
    background: #EBF4FF;
    color: #007AFF;
    font-weight: 600;
  }

  .engine-btn .icon { font-size: 20px; display: block; margin-bottom: 4px; }

  .field-group { display: none; }
  .field-group.visible { display: block; }

  label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: #3a3a3c;
    margin-bottom: 6px;
    margin-top: 14px;
  }

  input[type="text"], input[type="password"] {
    width: 100%;
    padding: 10px 14px;
    border: 1.5px solid #d1d1d6;
    border-radius: 8px;
    font-size: 14px;
    color: #1d1d1f;
    outline: none;
    transition: border-color 0.15s;
    background: #fafafa;
  }

  input[type="text"]:focus, input[type="password"]:focus {
    border-color: #007AFF;
    background: white;
  }

  .show-key {
    font-size: 12px;
    color: #007AFF;
    cursor: pointer;
    margin-top: 4px;
    display: inline-block;
  }

  .output-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 4px;
  }

  .output-btn {
    border: 2px solid #e0e0e5;
    border-radius: 10px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.15s;
    background: white;
    font-size: 13px;
    font-weight: 500;
    color: #3a3a3c;
    text-align: left;
  }

  .output-btn:hover { border-color: #34C759; }
  .output-btn.active { border-color: #34C759; background: #EDFAF1; color: #1a7a3a; font-weight: 600; }
  .output-btn .mode-title { font-size: 14px; font-weight: 600; margin-bottom: 2px; }
  .output-btn .mode-desc { font-size: 11px; color: #6e6e73; }
  .output-btn.active .mode-desc { color: #2a8a4a; }

  .divider {
    height: 1px;
    background: #f0f0f5;
    margin: 28px 0 4px;
  }

  .save-row {
    margin-top: 28px;
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .save-btn {
    background: #007AFF;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 32px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }

  .save-btn:hover { background: #005ecb; }
  .save-btn:active { background: #004aaa; }

  .status {
    font-size: 13px;
    color: #34C759;
    font-weight: 500;
    opacity: 0;
    transition: opacity 0.3s;
  }

  .status.visible { opacity: 1; }
  .status.error { color: #FF3B30; }
</style>
</head>
<body>
<div class="card">
  <h1><span class="dot"></span> OmniScribe Settings</h1>

  <!-- Engine Selection -->
  <div class="section-label">Transcription Engine</div>
  <div class="engine-grid">
    <div class="engine-btn {% if config.active_engine == 'gemini' %}active{% endif %}"
         onclick="selectEngine('gemini', this)">
      <span class="icon">✦</span>Gemini
    </div>
    <div class="engine-btn {% if config.active_engine == 'whisper' %}active{% endif %}"
         onclick="selectEngine('whisper', this)">
      <span class="icon">🎙</span>Whisper
    </div>
    <div class="engine-btn {% if config.active_engine == 'ollama' %}active{% endif %}"
         onclick="selectEngine('ollama', this)">
      <span class="icon">🦙</span>Ollama
    </div>
  </div>

  <!-- Gemini Fields -->
  <div class="field-group {% if config.active_engine == 'gemini' %}visible{% endif %}" id="fields-gemini">
    <label>Gemini API Key</label>
    <input type="password" id="gemini_api_key" value="{{ config.gemini_api_key }}" placeholder="AIza...">
    <span class="show-key" onclick="toggleVisibility('gemini_api_key', this)">Show</span>
  </div>

  <!-- Whisper Fields -->
  <div class="field-group {% if config.active_engine == 'whisper' %}visible{% endif %}" id="fields-whisper">
    <label>OpenAI API Key</label>
    <input type="password" id="openai_api_key" value="{{ config.openai_api_key }}" placeholder="sk-...">
    <span class="show-key" onclick="toggleVisibility('openai_api_key', this)">Show</span>
  </div>

  <!-- Ollama Fields -->
  <div class="field-group {% if config.active_engine == 'ollama' %}visible{% endif %}" id="fields-ollama">
    <label>Ollama Host</label>
    <input type="text" id="ollama_host" value="{{ config.ollama_host }}" placeholder="http://mac-mini.local:11434">
    <label>Model Name</label>
    <input type="text" id="ollama_model" value="{{ config.ollama_model }}" placeholder="gemma4:e4b">
  </div>

  <div class="divider"></div>

  <!-- Output Mode -->
  <div class="section-label">Output Mode</div>
  <div class="output-grid">
    <div class="output-btn {% if config.output_mode == 'clipboard' %}active{% endif %}"
         onclick="selectOutput('clipboard', this)">
      <div class="mode-title">📋 Clipboard</div>
      <div class="mode-desc">Cmd+V — works in browsers & all apps</div>
    </div>
    <div class="output-btn {% if config.output_mode == 'type' %}active{% endif %}"
         onclick="selectOutput('type', this)">
      <div class="mode-title">⌨️ Type</div>
      <div class="mode-desc">Simulated keystrokes — native apps only</div>
    </div>
  </div>

  <!-- Save -->
  <div class="save-row">
    <button class="save-btn" onclick="saveSettings()">Save Settings</button>
    <span class="status" id="status"></span>
  </div>
</div>

<script>
  let currentEngine = "{{ config.active_engine }}";
  let currentOutput = "{{ config.output_mode }}";

  function selectEngine(engine, el) {
    currentEngine = engine;
    document.querySelectorAll('.engine-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.field-group').forEach(f => f.classList.remove('visible'));
    document.getElementById('fields-' + engine).classList.add('visible');
  }

  function selectOutput(mode, el) {
    currentOutput = mode;
    document.querySelectorAll('.output-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
  }

  function toggleVisibility(fieldId, btn) {
    const input = document.getElementById(fieldId);
    if (input.type === 'password') {
      input.type = 'text';
      btn.textContent = 'Hide';
    } else {
      input.type = 'password';
      btn.textContent = 'Show';
    }
  }

  function saveSettings() {
    const payload = {
      active_engine: currentEngine,
      output_mode: currentOutput,
      gemini_api_key: document.getElementById('gemini_api_key').value,
      openai_api_key: document.getElementById('openai_api_key').value,
      ollama_host: document.getElementById('ollama_host').value,
      ollama_model: document.getElementById('ollama_model').value,
    };

    fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
      const s = document.getElementById('status');
      if (data.ok) {
        s.textContent = '✓ Saved successfully';
        s.className = 'status visible';
      } else {
        s.textContent = '✗ Save failed';
        s.className = 'status error visible';
      }
      setTimeout(() => s.classList.remove('visible'), 3000);
    });
  }
</script>
</body>
</html>
"""

class SettingsServer:
    def __init__(self, config_mgr):
        self.config_mgr = config_mgr
        self.app = Flask(__name__)
        self.port = 47891
        self._started = False
        self._lock = threading.Lock()
        self._register_routes()

    def _register_routes(self):
        config_mgr = self.config_mgr

        @self.app.route("/")
        def index():
            conf = config_mgr.load_config()
            # Provide safe defaults for template rendering
            conf.setdefault("gemini_api_key", "")
            conf.setdefault("openai_api_key", "")
            conf.setdefault("ollama_host", "http://mac-mini.local:11434")
            conf.setdefault("ollama_model", "gemma4:e4b")
            conf.setdefault("output_mode", "clipboard")
            conf.setdefault("active_engine", "gemini")
            return render_template_string(SETTINGS_HTML, config=conf)

        @self.app.route("/save", methods=["POST"])
        def save():
            try:
                data = request.get_json()
                conf = config_mgr.load_config()
                conf.update({
                    "active_engine": data.get("active_engine", conf.get("active_engine")),
                    "output_mode": data.get("output_mode", conf.get("output_mode")),
                    "gemini_api_key": data.get("gemini_api_key", ""),
                    "openai_api_key": data.get("openai_api_key", ""),
                    "ollama_host": data.get("ollama_host", ""),
                    "ollama_model": data.get("ollama_model", ""),
                })
                config_mgr.save_config(conf)
                logger.info(f"Settings saved via web UI. Engine: {conf['active_engine']}")
                return jsonify({"ok": True})
            except Exception as e:
                logger.error(f"Settings save error: {e}")
                return jsonify({"ok": False, "error": str(e)})

    def _run_server(self):
        import logging as pylogging
        pylogging.getLogger("werkzeug").setLevel(pylogging.ERROR)
        self.app.run(host="127.0.0.1", port=self.port, debug=False, use_reloader=False)

    def open(self):
        with self._lock:
            if not self._started:
                t = threading.Thread(target=self._run_server, daemon=True)
                t.start()
                self._started = True
                import time
                time.sleep(0.6)  # Give Flask a moment to start
        webbrowser.open(f"http://127.0.0.1:{self.port}")
        logger.info("Settings page opened in browser.")