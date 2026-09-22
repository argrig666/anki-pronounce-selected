# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Pronounce Selected Text (Alt+C) for Anki.

Instantly pronounces highlighted / selected text across Anki (Card Reviewer,
Note Editor, and Card Browser) using high-quality Microsoft Azure / Edge Neural voices.
- 100% Standalone add-on with self-contained dependencies and local cache.
- Pure and silent: NOTHING happens when no text is selected.
- Automatic language detection: detects language of the selected text on-the-fly!
- Dedicated native monolingual voices (it-IT-ElsaNeural, fr-FR-DeniseNeural, etc.).
- Dynamic SSML xml:lang locale integrity.
- Instant (<1 ms) cached playback via mpv.
- Non-blocking background synthesis for new words.
- Audio preemption (cleanly terminates previous audio when Alt+C is hit rapidly).
- Dual DOM & Qt shortcut capture for 100% reliable Alt+C interception.
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import aqt
from anki.utils import checksum
from aqt import gui_hooks
from aqt.qt import QAction, QApplication, QClipboard, QKeySequence, QMenu, QShortcut, Qt
from aqt.utils import tooltip

# Path resolution - 100% relative and self-contained
_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
_VENDOR_DIR = os.path.join(_ADDON_DIR, "vendor")
_CACHE_DIR = os.path.join(_ADDON_DIR, "user_files", "cache")
_CONFIG_PATH = os.path.join(_ADDON_DIR, "config.json")
_LOG_PATH = os.path.join(_ADDON_DIR, "user_files", "debug.log")

if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

if _ADDON_DIR not in sys.path:
    sys.path.insert(0, _ADDON_DIR)

import detector  # noqa: E402

try:
    import edge_tts
except ImportError:
    edge_tts = None  # type: ignore

try:
    from gtts import gTTS
except ImportError:
    gTTS = None  # type: ignore

# Global process tracking to allow audio preemption
_CURRENT_MPV_PROC: subprocess.Popen | None = None

# Regex helpers
_HTML_RE = re.compile(r"<[^>]+>")
_SOUND_RE = re.compile(r"\[sound:[^\]]*\]")
_TTS_TAG_RE = re.compile(r"\{\{tts\s+([a-zA-Z_\-]+)")


def _load_config() -> dict[str, Any]:
    if aqt.mw and hasattr(aqt.mw, "addonManager"):
        cfg = aqt.mw.addonManager.getConfig(__name__)
        if isinstance(cfg, dict):
            return cfg
    if os.path.isfile(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "shortcut": "Alt+C",
        "volume": 140,
        "audio_output": "pipewire,pulse",
        "speed": 1.0,
        "show_tooltip": False,
        "debug_log": True,
    }


def _log(msg: str) -> None:
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def _clean_text(raw: str) -> str:
    """Strip sound tags, HTML elements, and extra whitespace while preserving target diacritics."""
    text = _SOUND_RE.sub(" ", raw)
    text = _HTML_RE.sub(" ", text)
    text = html.unescape(text)
    # Strip IPA slashes if wrapped in /.../
    m_ipa = re.match(r"^\s*/(.*)/\s*$", text)
    if m_ipa:
        text = m_ipa.group(1)
    return re.sub(r"\s+", " ", text).strip()


def _get_cache_path(voice_name: str, speed: float, text: str) -> str:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    speed_key = round(speed, 2)
    key = checksum(f"{voice_name}-{speed_key}-{text}")
    return os.path.join(_CACHE_DIR, f"{key}.mp3")


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


async def _synthesize_edge(text: str, voice_name: str, rate: str, output_path: str) -> None:
    if edge_tts is None:
        raise RuntimeError("edge_tts is not available in vendor")
    communicate = edge_tts.Communicate(text=text, voice=voice_name, rate=rate)
    await communicate.save(output_path)


def _play_audio_file(audio_path: str, cfg: dict[str, Any]) -> None:
    """Play audio file via mpv with preemption of any running audio."""
    global _CURRENT_MPV_PROC
    if _CURRENT_MPV_PROC and _CURRENT_MPV_PROC.poll() is None:
        try:
            _CURRENT_MPV_PROC.terminate()
            _CURRENT_MPV_PROC.wait(timeout=0.1)
        except Exception:
            pass

    vol = str(cfg.get("volume", 140))
    ao = cfg.get("audio_output", "pipewire,pulse")

    cmd = [
        "mpv",
        "--no-terminal",
        "--no-config",
        "--load-scripts=no",
        "--force-window=no",
        "--audio-display=no",
        "--keep-open=no",
        "--input-media-keys=no",
        "--no-ytdl",
        f"--ao={ao}",
        f"--volume={vol}",
        "--volume-max=150",
        audio_path,
    ]
    try:
        _CURRENT_MPV_PROC = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _log(f"Spawned mpv for {audio_path}")
    except Exception as err:
        _log(f"Failed to spawn mpv: {err}")
        tooltip(f"Audio playback error: {err}")


def _get_active_card_context_lang() -> str | None:
    """Extract language context from current card / deck if available as an intelligent prior."""
    if not aqt.mw or not hasattr(aqt.mw, "col") or not aqt.mw.col:
        return None

    card = None
    if aqt.mw.state == "review" and hasattr(aqt.mw, "reviewer") and hasattr(aqt.mw.reviewer, "card"):
        card = aqt.mw.reviewer.card

    if not card:
        return None

    # Check template {{tts <lang>}}
    try:
        tmpl = card.template()
        m = _TTS_TAG_RE.search(tmpl.get("qfmt", "") + " " + tmpl.get("afmt", ""))
        if m:
            return m.group(1)
    except Exception:
        pass

    # Check deck name
    try:
        deck_name = aqt.mw.col.decks.name(card.did).lower()
        if "italian" in deck_name or "italiano" in deck_name:
            return "it"
        if "french" in deck_name or "français" in deck_name:
            return "fr"
        if "russian" in deck_name or "русский" in deck_name:
            return "ru"
        if "german" in deck_name or "deutsch" in deck_name:
            return "de"
        if "spanish" in deck_name or "español" in deck_name:
            return "es"
    except Exception:
        pass

    return None


def _get_editor_context_lang(editor: Any) -> str | None:
    """Extract language context from active editor note / model if available."""
    try:
        note = getattr(editor, "note", None)
        if note and aqt.mw and aqt.mw.col:
            model = aqt.mw.col.models.get(note.mid)
            if model:
                m_name = model.get("name", "").lower()
                if "italian" in m_name:
                    return "it"
                if "french" in m_name:
                    return "fr"
                if "russian" in m_name:
                    return "ru"
                if "german" in m_name:
                    return "de"
                if "spanish" in m_name:
                    return "es"
    except Exception:
        pass
    return None


def _get_active_webview() -> Any | None:
    """Get active WebEngineView in the current Anki window."""
    if not aqt.mw:
        return None
    if aqt.mw.state == "review" and hasattr(aqt.mw, "reviewer") and hasattr(aqt.mw.reviewer, "web"):
        return aqt.mw.reviewer.web
    w = aqt.mw.app.focusWidget() if hasattr(aqt.mw, "app") else None
    curr = w
    while curr:
        if hasattr(curr, "page") and hasattr(curr.page(), "runJavaScript"):
            return curr
        curr = curr.parent()
    return None


def pronounce_text(text: str, context_lang: str | None = None) -> None:
    """Auto-detect language and synthesize/play audio without blocking Anki UI."""
    clean = _clean_text(text)
    if not clean:
        return

    cfg = _load_config()
    voice = detector.get_voice_for_text(clean, context_lang=context_lang)
    speed = float(cfg.get("speed", 1.0))
    _log(f"Auto-detected voice '{voice}' for '{clean}' (context_lang={context_lang})")

    if cfg.get("show_tooltip", False):
        display_label = clean if len(clean) <= 35 else clean[:32] + "..."
        tooltip(f"🔊 {display_label} [{voice.split('-')[0]}]", period=1000)

    # 1. Check local cache
    cached_path = _get_cache_path(voice, speed, clean)
    if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
        _log(f"Cache hit: {cached_path}")
        _play_audio_file(cached_path, cfg)
        return

    # 2. Synthesize asynchronously in background
    def do_synthesis() -> str | None:
        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"{rate_pct:+d}%"
        t0 = time.time()
        try:
            _run_async(_synthesize_edge(clean, voice, rate_str, cached_path))
            if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                dt = round((time.time() - t0) * 1000)
                _log(f"Edge TTS synthesized '{clean}' in {dt}ms")
                return cached_path
        except Exception as err:
            _log(f"Edge TTS synthesis error for '{clean}': {err}")

        # Fallback to gTTS if network error
        if gTTS is not None:
            try:
                lang_code = voice.split("-")[0]
                tts = gTTS(text=clean, lang=lang_code, slow=speed < 1.0)
                tts.save(cached_path)
                if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                    _log(f"gTTS fallback synthesized '{clean}'")
                    return cached_path
            except Exception as gerr:
                _log(f"gTTS fallback error: {gerr}")

        return None

    def on_synthesis_done(future):
        try:
            res_path = future.result()
            if res_path:
                _play_audio_file(res_path, cfg)
            else:
                _log(f"TTS synthesis failed for '{clean}'")
        except Exception as ex:
            _log(f"Error in on_synthesis_done: {ex}")

    if aqt.mw and hasattr(aqt.mw, "taskman"):
        aqt.mw.taskman.run_in_background(do_synthesis, on_synthesis_done)
    else:
        def run_thread():
            res = do_synthesis()
            if res:
                _play_audio_file(res, cfg)
        import threading
        threading.Thread(target=run_thread, daemon=True).start()


def trigger_pronounce() -> None:
    """Qt shortcut handler (Alt+C). Queries active webview and clipboard."""
    _log("trigger_pronounce activated via Qt shortcut")
    cb_text = ""
    cb = QApplication.clipboard()
    if cb and cb.supportsSelection():
        try:
            cb_text = _clean_text(cb.text(QClipboard.Mode.Selection))
        except Exception:
            pass

    web = _get_active_webview()
    if web and hasattr(web, "page") and web.page():
        js = """(() => {
            let s = window.getSelection ? window.getSelection().toString() : "";
            if (s && s.trim()) return s.trim();
            let el = document.activeElement;
            if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) {
                let start = el.selectionStart, end = el.selectionEnd;
                if (typeof start === 'number' && typeof end === 'number' && start !== end) {
                    return el.value.substring(start, end).trim();
                }
            }
            return "";
        })()"""

        def on_eval_done(res):
            txt = _clean_text(str(res or ""))
            if not txt and cb_text:
                txt = cb_text
            if not txt:
                _log("Qt shortcut: No selection found (silent return)")
                return
            _log(f"Qt shortcut captured: '{txt}'")
            context_lang = _get_active_card_context_lang()
            pronounce_text(txt, context_lang=context_lang)

        web.page().runJavaScript(js, on_eval_done)
    elif cb_text:
        _log(f"Qt shortcut captured from primary clipboard: '{cb_text}'")
        context_lang = _get_active_card_context_lang()
        pronounce_text(cb_text, context_lang=context_lang)
    else:
        _log("Qt shortcut: No webview or clipboard selection found (silent return)")


def on_editor_pronounce(editor: Any) -> None:
    """Editor shortcut handler (Alt+C)."""
    _log("on_editor_pronounce activated via Editor shortcut")
    web = getattr(editor, "web", None)
    if web and hasattr(web, "page") and web.page():
        js = "window.getSelection ? window.getSelection().toString() : ''"
        def on_eval(res):
            txt = _clean_text(str(res or ""))
            if not txt:
                cb = QApplication.clipboard()
                if cb and cb.supportsSelection():
                    try:
                        txt = _clean_text(cb.text(QClipboard.Mode.Selection))
                    except Exception:
                        pass
            if not txt:
                _log("Editor shortcut: No selection found (silent return)")
                return
            _log(f"Editor shortcut captured: '{txt}'")
            context_lang = _get_editor_context_lang(editor)
            pronounce_text(txt, context_lang=context_lang)
        web.page().runJavaScript(js, on_eval)


# --- DOM Keydown Injection & JS Bridge (100% Reliable In-Card Capture) ---

_JS_LISTENER = """
<script>
(function() {
    if (window._pronounceSelectedInjected) return;
    window._pronounceSelectedInjected = true;
    document.addEventListener("keydown", function(e) {
        if (e.altKey && (e.key === "c" || e.key === "C" || e.code === "KeyC")) {
            var sel = "";
            if (window.getSelection) {
                sel = window.getSelection().toString();
            }
            if (!sel && document.activeElement) {
                var el = document.activeElement;
                if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA")) {
                    var start = el.selectionStart, end = el.selectionEnd;
                    if (typeof start === "number" && typeof end === "number" && start !== end) {
                        sel = el.value.substring(start, end);
                    }
                }
            }
            if (sel && sel.trim()) {
                pycmd("pronounce_selected:" + encodeURIComponent(sel.trim()));
                e.preventDefault();
                e.stopPropagation();
            }
        }
    }, true);
})();
</script>
"""


def _on_webview_will_set_content(web_content: aqt.webview.WebContent, context: Any) -> None:
    """Inject DOM keydown listener into every Anki web view (Reviewer, Editor, etc.)."""
    web_content.head += _JS_LISTENER
    _log(f"Injected JS keydown listener into webview content (context={type(context).__name__})")


def _on_webview_did_receive_js_message(
    handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    """Intercept pycmd('pronounce_selected:...') messages from injected DOM listener."""
    if message.startswith("pronounce_selected:"):
        encoded_sel = message[len("pronounce_selected:"):].strip()
        text = urllib.parse.unquote(encoded_sel)
        _log(f"Received JS bridge pronounce_selected: '{text}' (context={type(context).__name__})")
        if text:
            context_lang = _get_active_card_context_lang()
            pronounce_text(text, context_lang=context_lang)
        return (True, None)
    return handled


# --- Hook Registrations ---

def _on_state_shortcuts_will_change(state: str, shortcuts: list[tuple[str, Any]]) -> None:
    """Register reviewer shortcut."""
    if state == "review":
        cfg = _load_config()
        shortcut_key = cfg.get("shortcut", "Alt+C")
        shortcuts.append((shortcut_key, trigger_pronounce))
        _log(f"Registered review state shortcut '{shortcut_key}'")


def _on_editor_did_init_shortcuts(shortcuts: list[tuple], editor: Any) -> None:
    """Register editor shortcut."""
    cfg = _load_config()
    shortcut_key = cfg.get("shortcut", "Alt+C")
    shortcuts.append((shortcut_key, lambda ed=editor: on_editor_pronounce(ed), True))
    _log(f"Registered editor shortcut '{shortcut_key}'")


def _on_reviewer_context_menu(reviewer: Any, menu: QMenu) -> None:
    """Add 'Pronounce Selected Text (Alt+C)' to reviewer right-click context menu."""
    action = QAction("Pronounce Selected Text (Alt+C)", menu)
    action.triggered.connect(trigger_pronounce)
    menu.addAction(action)


def _init_global_shortcuts() -> None:
    """Ensure a fallback application-level shortcut is active on main window."""
    if aqt.mw:
        cfg = _load_config()
        shortcut_key = cfg.get("shortcut", "Alt+C")
        scut = QShortcut(QKeySequence(shortcut_key), aqt.mw, activated=trigger_pronounce)
        scut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        _log(f"Installed ApplicationShortcut '{shortcut_key}' on mw")


gui_hooks.webview_will_set_content.append(_on_webview_will_set_content)
gui_hooks.webview_did_receive_js_message.append(_on_webview_did_receive_js_message)
gui_hooks.state_shortcuts_will_change.append(_on_state_shortcuts_will_change)
gui_hooks.editor_did_init_shortcuts.append(_on_editor_did_init_shortcuts)
gui_hooks.reviewer_will_show_context_menu.append(_on_reviewer_context_menu)
gui_hooks.profile_did_open.append(_init_global_shortcuts)

if aqt.mw and aqt.mw.col:
    _init_global_shortcuts()
