import threading
import webbrowser
import json
import os
from flask import Flask, request, jsonify, render_template_string
from src.utils.logger import logger

HISTORY_PATH = os.path.expanduser("~/Library/Application Support/OmniScribe/history.json")

HISTORY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OmniScribe History</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    background: #f5f5f7;
    padding: 40px 16px;
  }
  .card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
    width: 100%;
    max-width: 700px;
    margin: 0 auto;
    padding: 36px 40px;
  }
  h1 {
    font-size: 22px;
    font-weight: 700;
    color: #1d1d1f;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  h1 span.dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    background: #34C759;
    display: inline-block;
  }
  .subtitle {
    font-size: 13px;
    color: #6e6e73;
    margin-bottom: 24px;
  }
  .toolbar {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }
  .btn {
    padding: 8px 16px;
    border-radius: 8px;
    border: none;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s;
  }
  .btn-export { background: #007AFF; color: white; }
  .btn-export:hover { background: #005ecb; }
  .btn-clear { background: #f0f0f5; color: #3a3a3c; }
  .btn-clear:hover { background: #e0e0e5; }
  .btn-danger { background: #FF3B30; color: white; }
  .btn-danger:hover { background: #cc2f26; }
  .entry {
    border-bottom: 1px solid #f0f0f5;
    padding: 14px 0;
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }
  .entry:last-child { border-bottom: none; }
  .entry-meta {
    min-width: 140px;
    flex-shrink: 0;
  }
  .entry-time {
    font-size: 12px;
    color: #6e6e73;
    margin-bottom: 4px;
  }
  .entry-engine {
    font-size: 11px;
    color: #007AFF;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .entry-text {
    font-size: 14px;
    color: #1d1d1f;
    line-height: 1.5;
    flex: 1;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
    transition: background 0.1s;
  }
  .entry-text:hover { background: #f0f7ff; }
  .entry-text.copied { background: #EDFAF1; color: #1a7a3a; }
  .empty {
    text-align: center;
    color: #6e6e73;
    padding: 60px 0;
    font-size: 15px;
  }
  .copy-hint {
    font-size: 12px;
    color: #6e6e73;
    margin-bottom: 16px;
  }
</style>
</head>
<body>
<div class="card">
  <h1><span class="dot"></span> Transcription History</h1>
  <div class="subtitle">{{ count }} entries — click any entry to copy it to clipboard</div>
  <div class="toolbar">
    <button class="btn btn-export" onclick="exportHistory()">⬇ Export JSON</button>
    <button class="btn btn-clear btn-danger" onclick="clearHistory()">🗑 Clear All</button>
  </div>
  {% if entries %}
  <div id="entries">
    {% for entry in entries %}
    <div class="entry">
      <div class="entry-meta">
        <div class="entry-time">{{ entry.timestamp }}</div>
        <div class="entry-engine">{{ entry.engine }}</div>
      </div>
      <div class="entry-text" onclick="copyEntry(this, '{{ entry.text | replace("'", "\\'") }}')">{{ entry.text }}</div>
    </div>
    {% endfor %}
  </div>
  {% else %}
  <div class="empty">No transcription history yet.<br>Start recording to see entries here.</div>
  {% endif %}
</div>
<script>
  function copyEntry(el, text) {
    navigator.clipboard.writeText(text).then(() => {
      el.classList.add('copied');
      const original = el.textContent;
      el.textContent = '✓ Copied!';
      setTimeout(() => {
        el.textContent = original;
        el.classList.remove('copied');
      }, 1500);
    });
  }

  function exportHistory() {
    fetch('/history/export')
      .then(r => r.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'omniscribe_history.json';
        a.click();
      });
  }

  function clearHistory() {
    if (!confirm('Clear all history? This cannot be undone.')) return;
    fetch('/history/clear', { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        if (data.ok) location.reload();
      });
  }
</script>
</body>
</html>
"""

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

  .field-hint {
    font-size: 11px;
    color: #6e6e73;
    margin-top: 4px;
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
    <div class="engine-btn {% if config.active_engine == 'whisper_local' %}active{% endif %}"
         onclick="selectEngine('whisper_local', this)">
      <span class="icon">🖥</span>Local
    </div>
  </div>

  <!-- Gemini Fields -->
  <div class="field-group {% if config.active_engine == 'gemini' %}visible{% endif %}" id="fields-gemini">
    <label>Gemini API Key</label>
    <input type="password" id="gemini_api_key" value="{{ config.gemini_api_key }}" placeholder="AIza...">
    <span class="show-key" onclick="toggleVisibility('gemini_api_key', this)">Show</span>
    <label>Gemini Model</label>
    <input type="text" id="gemini_model" value="{{ config.gemini_model }}" placeholder="e.g. gemini-2.0-flash-lite">
    <div class="field-hint">Find your model name in Google AI Studio → Get Code</div>
  </div>

  <!-- Whisper (API) Fields -->
  <div class="field-group {% if config.active_engine == 'whisper' %}visible{% endif %}" id="fields-whisper">
    <label>OpenAI API Key</label>
    <input type="password" id="openai_api_key" value="{{ config.openai_api_key }}" placeholder="sk-...">
    <span class="show-key" onclick="toggleVisibility('openai_api_key', this)">Show</span>
    <label>Custom Prompt <span style="font-weight:400;color:#6e6e73">(optional — e.g. domain-specific words)</span></label>
    <input type="text" id="whisper_prompt" value="{{ config.whisper_prompt }}" placeholder="e.g. Kubernetes, Splunk, Azure">
  </div>

  <!-- Whisper Local Fields -->
  <div class="field-group {% if config.active_engine == 'whisper_local' %}visible{% endif %}" id="fields-whisper_local">
    <label>Whisper Server URL</label>
    <input type="text" id="whisper_local_host" value="{{ config.whisper_local_host }}" placeholder="http://192.168.1.x:11500">
    <div class="field-hint">Format: http://[IP address]:[port] — e.g. http://192.168.1.250:11500</div>
  </div>

  <div class="divider"></div>

  <!-- Hotkey -->
  <div class="divider"></div>
  <div class="section-label">Hotkey</div>
  <label>Recording Shortcut</label>
  <input type="text" id="hotkey" value="{{ config.hotkey }}" placeholder="Click here, then press your shortcut"
         readonly style="cursor:pointer;"
         onfocus="this.style.borderColor='#007AFF'; this.placeholder='Press your shortcut now...'"
         onblur="this.style.borderColor=''; this.placeholder='Click here, then press your shortcut'">
  <div class="field-hint">Click the field above, then press your desired key combination (e.g. Cmd+Shift+U)</div>

  <!-- Output Mode -->
  <div class="divider"></div>
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

  // Known browser/system conflicting shortcuts (cmd+key)
  const browserConflicts = new Set(['p','s','w','t','r','n','l','a','c','v','x','z','f','h','j','k','d','o','b','u','i','g','m','e','q']);
  // Known Cmd+Shift conflicts
  const cmdShiftConflicts = new Set(['i','j','c','p','n','t','w','r','d','s','b','f','l','z','a','q','e','g','h','k','m','o','u','v','x']);

  // Hotkey capture
  const hotkeyInput = document.getElementById('hotkey');
  const hotkeyHint = hotkeyInput.nextElementSibling;

  hotkeyInput.addEventListener('keydown', function(e) {
    e.preventDefault();
    e.stopPropagation();

    // Ignore standalone modifier key presses
    if (['Meta', 'Shift', 'Control', 'Alt'].includes(e.key)) return;

    const parts = [];
    if (e.metaKey)  parts.push('<cmd>');
    if (e.ctrlKey)  parts.push('<ctrl>');
    if (e.altKey)   parts.push('<alt>');
    if (e.shiftKey) parts.push('<shift>');

    // Must have at least one modifier
    if (parts.length === 0) return;

    // Convert key to pynput format
    let key = e.key.toLowerCase();
    const specialKeys = {
      ' ': 'space', 'arrowup': '<up>', 'arrowdown': '<down>',
      'arrowleft': '<left>', 'arrowright': '<right>',
      'escape': '<esc>', 'tab': '<tab>', 'backspace': '<backspace>',
      'delete': '<delete>', 'enter': '<enter>',
      'f1':'<f1>','f2':'<f2>','f3':'<f3>','f4':'<f4>',
      'f5':'<f5>','f6':'<f6>','f7':'<f7>','f8':'<f8>',
      'f9':'<f9>','f10':'<f10>','f11':'<f11>','f12':'<f12>',
    };
    if (specialKeys[key]) {
      key = specialKeys[key];
    }

    parts.push(key);
    hotkeyInput.value = parts.join('+');

    // Warn if this shortcut conflicts with common browser/system shortcuts
    const isOnlyCmd = e.metaKey && !e.shiftKey && !e.ctrlKey && !e.altKey;
    const isCmdShift = e.metaKey && e.shiftKey && !e.ctrlKey && !e.altKey;
    if (isOnlyCmd && browserConflicts.has(e.key.toLowerCase())) {
      hotkeyHint.textContent = '⚠️ Warning: Cmd+' + e.key.toUpperCase() + ' may conflict with a system or browser shortcut. Consider adding Shift or using a different key.';
      hotkeyHint.style.color = '#FF9500';
    } else if (isCmdShift && cmdShiftConflicts.has(e.key.toLowerCase())) {
      hotkeyHint.textContent = '⚠️ Warning: Cmd+Shift+' + e.key.toUpperCase() + ' may conflict with a system or browser shortcut. Consider using a different key.';
      hotkeyHint.style.color = '#FF9500';
    } else {
      hotkeyHint.textContent = 'Click the field above, then press your desired key combination (e.g. Cmd+Shift+U)';
      hotkeyHint.style.color = '#6e6e73';
    }
  });

  function saveSettings() {
    const payload = {
      active_engine: currentEngine,
      output_mode: currentOutput,
      gemini_api_key: document.getElementById('gemini_api_key').value,
      gemini_model: document.getElementById('gemini_model').value,
      openai_api_key: document.getElementById('openai_api_key').value,
      whisper_prompt: document.getElementById('whisper_prompt').value,
      whisper_local_host: document.getElementById('whisper_local_host').value,
      hotkey: document.getElementById('hotkey').value,
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
    def __init__(self, config_mgr, on_save=None):
        self.config_mgr = config_mgr
        self.on_save = on_save  # Callback to notify gui_app when settings are saved
        self.app = Flask(__name__)
        self.port = 47891
        self._started = False
        self._lock = threading.Lock()
        self._register_routes()

    def _register_routes(self):
        config_mgr = self.config_mgr
        on_save = self.on_save

        @self.app.route("/")
        def index():
            conf = config_mgr.load_config()
            conf.setdefault("gemini_api_key", "")
            conf.setdefault("gemini_model", "")
            conf.setdefault("openai_api_key", "")
            conf.setdefault("whisper_prompt", "")
            conf.setdefault("whisper_local_host", "")
            conf.setdefault("hotkey", "<cmd>+<shift>+u")
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
                    "gemini_model": data.get("gemini_model", ""),
                    "openai_api_key": data.get("openai_api_key", ""),
                    "whisper_prompt": data.get("whisper_prompt", ""),
                    "whisper_local_host": data.get("whisper_local_host", ""),
                    "hotkey": data.get("hotkey", conf.get("hotkey", "<cmd>+<shift>+u")),
                })
                config_mgr.save_config(conf)
                logger.info(f"Settings saved via web UI. Engine: {conf['active_engine']}")

                # Notify gui_app so it can reload hotkey and refresh menu
                if on_save:
                    threading.Thread(target=on_save, args=(conf,), daemon=True).start()

                return jsonify({"ok": True})
            except Exception as e:
                logger.error(f"Settings save error: {e}")
                return jsonify({"ok": False, "error": str(e)})

        @self.app.route("/history")
        def history():
            try:
                if os.path.exists(HISTORY_PATH):
                    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                        entries = json.load(f)
                else:
                    entries = []
            except Exception:
                entries = []
            return render_template_string(HISTORY_HTML, entries=entries, count=len(entries))

        @self.app.route("/history/export")
        def history_export():
            from flask import Response
            try:
                if os.path.exists(HISTORY_PATH):
                    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                        data = f.read()
                else:
                    data = "[]"
            except Exception:
                data = "[]"
            return Response(data, mimetype='application/json',
                            headers={"Content-Disposition": "attachment; filename=omniscribe_history.json"})

        @self.app.route("/history/clear", methods=["POST"])
        def history_clear():
            try:
                with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                return jsonify({"ok": True})
            except Exception as e:
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
                time.sleep(0.6)
        webbrowser.open(f"http://127.0.0.1:{self.port}")
        logger.info("Settings page opened in browser.")

    def open_history(self):
        with self._lock:
            if not self._started:
                t = threading.Thread(target=self._run_server, daemon=True)
                t.start()
                self._started = True
                import time
                time.sleep(0.6)
        webbrowser.open(f"http://127.0.0.1:{self.port}/history")
        logger.info("History page opened in browser.")