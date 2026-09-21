# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Pronounce Selected Text (Alt+C) for Anki.

Instantly pronounces highlighted / selected text across Anki (Card Reviewer,
Note Editor, and Card Browser) using high-quality Microsoft Azure / Edge Neural voices.
- Dedicated native monolingual voices per language (it-IT-ElsaNeural, fr-FR-DeniseNeural, etc.)
- Dynamic SSML xml:lang locale integrity.
- Smart context resolution: automatically distinguishes English gloss fields from target language.
- Instant (<1 ms) cached playback via mpv with Volume Boost.
- Non-blocking background synthesis for new expressions.
- Process preemption (cleanly cuts off previous audio on rapid Alt+C).
- Configurable shortcut, volume, speed, and deck mappings.
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import aqt
from anki.utils import checksum
from aqt import gui_hooks
from aqt.qt import QAction, QKeySequence, QMenu, QShortcut
from aqt.utils import tooltip

# Path resolution
_ADDON_DIR = os.path.dirname(__file__)
_LOCAL_VENDOR = os.path.join(_ADDON_DIR, "vendor")
_USER_CACHE_DIR = os.path.join(_ADDON_DIR, "user_files", "cache")
_CONFIG_PATH = os.path.join(_ADDON_DIR, "config.json")
_LOG_PATH = os.path.join(_ADDON_DIR, "user_files", "debug.log")

# Add vendor directories to sys.path
_VENDOR_CANDIDATES = [
    _LOCAL_VENDOR,
    os.path.abspath(os.path.join(_ADDON_DIR, "..", "linux_tts_player", "vendor")),
    "/home/argrig/Projects/Anki/anki-edge-neural-tts-linux/vendor",
]
for v in _VENDOR_CANDIDATES:
    if os.path.isdir(v) and v not in sys.path:
        sys.path.insert(0, v)

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
_TTS_TAG_RE = re.compile(r"\{\{tts\s+([a-zA-Z_\-]+)(?:\s+voices=([^:}]+))?")

# Standard Dedicated Monolingual Voices (strict adherence to tts-neural-principles)
DEFAULT_MONOLINGUAL_VOICES: dict[str, str] = {
    "it_IT": "it-IT-ElsaNeural",
    "it": "it-IT-ElsaNeural",
    "fr_FR": "fr-FR-DeniseNeural",
    "fr": "fr-FR-DeniseNeural",
    "fr_CA": "fr-CA-SylvieNeural",
    "es_ES": "es-ES-ElviraNeural",
    "es": "es-ES-ElviraNeural",
    "es_MX": "es-MX-DaliaNeural",
    "de_DE": "de-DE-KatjaNeural",
    "de": "de-DE-KatjaNeural",
    "ru_RU": "ru-RU-SvetlanaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "en_US": "en-US-JennyNeural",
    "en": "en-US-JennyNeural",
    "en_GB": "en-GB-SoniaNeural",
    "ja_JP": "ja-JP-NanamiNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh_CN": "zh-CN-XiaoxiaoNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "pt_BR": "pt-BR-FranciscaNeural",
    "pt": "pt-BR-FranciscaNeural",
}

VOICE_ALIASES: dict[str, dict[str, str]] = {
    "it_IT": {
        "federica": "it-IT-ElsaNeural",
        "emma": "it-IT-IsabellaNeural",
        "alice": "it-IT-ElsaNeural",
        "cosimo": "it-IT-DiegoNeural",
        "diego": "it-IT-DiegoNeural",
        "elsa": "it-IT-ElsaNeural",
        "isabella": "it-IT-IsabellaNeural",
        "giuseppe": "it-IT-GiuseppeMultilingualNeural",
    },
    "fr_FR": {
        "vivienne": "fr-FR-DeniseNeural",
        "audrey": "fr-FR-DeniseNeural",
        "thomas": "fr-FR-HenriNeural",
        "aurelie": "fr-FR-DeniseNeural",
        "denise": "fr-FR-DeniseNeural",
        "henri": "fr-FR-HenriNeural",
        "eloise": "fr-FR-EloiseNeural",
        "remy": "fr-FR-RemyMultilingualNeural",
    },
    "en_US": {
        "jenny": "en-US-JennyNeural",
        "guy": "en-US-GuyNeural",
        "aria": "en-US-AriaNeural",
        "samantha": "en-US-JennyNeural",
    },
    "ru_RU": {
        "svetlana": "ru-RU-SvetlanaNeural",
        "dmitry": "ru-RU-DmitryNeural",
    },
}


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
        "default_voice": "it-IT-ElsaNeural",
        "volume": 140,
        "audio_output": "pipewire,pulse",
        "speed": 1.0,
        "pronounce_card_if_no_selection": True,
        "auto_detect_english_field": True,
        "show_tooltip": True,
        "deck_voices": {
            "Italian Decks": "it-IT-ElsaNeural",
            "French Decks": "fr-FR-DeniseNeural",
            "English Dict": "en-US-JennyNeural",
            "Русский": "ru-RU-SvetlanaNeural",
            "Russian": "ru-RU-SvetlanaNeural",
        },
        "debug_log": False,
    }


def _log(msg: str) -> None:
    cfg = _load_config()
    if not cfg.get("debug_log", False):
        return
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
    # Strip IPA slashes if the selection is wrapped in slashes e.g. /.../
    m_ipa = re.match(r"^\s*/(.*)/\s*$", text)
    if m_ipa:
        text = m_ipa.group(1)
    return re.sub(r"\s+", " ", text).strip()


def _get_cache_dirs() -> list[str]:
    """Return list of cache directories, including shared cache from linux_tts_player if present."""
    os.makedirs(_USER_CACHE_DIR, exist_ok=True)
    dirs = [_USER_CACHE_DIR]
    shared_peer = os.path.abspath(os.path.join(_ADDON_DIR, "..", "linux_tts_player", "user_files", "cache"))
    if os.path.isdir(shared_peer) and shared_peer not in dirs:
        dirs.append(shared_peer)
    workspace_cache = "/home/argrig/Projects/Anki/anki-edge-neural-tts-linux/user_files/cache"
    if os.path.isdir(workspace_cache) and workspace_cache not in dirs:
        dirs.append(workspace_cache)
    return dirs


def _find_cached_audio(voice_name: str, speed: float, text: str) -> str | None:
    """Find existing cached mp3 file across cache directories."""
    speed_key = round(speed, 2)
    key = checksum(f"{voice_name}-{speed_key}-{text}")
    for d in _get_cache_dirs():
        p = os.path.join(d, f"{key}.mp3")
        if os.path.exists(p) and os.path.getsize(p) > 0:
            return p
    return None


def _get_cache_path_for_write(voice_name: str, speed: float, text: str) -> str:
    speed_key = round(speed, 2)
    key = checksum(f"{voice_name}-{speed_key}-{text}")
    return os.path.join(_USER_CACHE_DIR, f"{key}.mp3")


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
        raise RuntimeError("edge_tts is not available")
    communicate = edge_tts.Communicate(text=text, voice=voice_name, rate=rate)
    await communicate.save(output_path)


def _play_audio_file(audio_path: str, cfg: dict[str, Any]) -> None:
    """Play audio file via mpv with preemption of any existing playback."""
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


def resolve_voice_for_context(
    text: str,
    card: Any | None = None,
    note: Any | None = None,
    cfg: dict[str, Any] | None = None,
) -> str:
    """Resolve the most accurate dedicated neural voice for the given text and context."""
    if cfg is None:
        cfg = _load_config()

    default_v = cfg.get("default_voice", "it-IT-ElsaNeural")
    deck_voices = cfg.get("deck_voices", {})
    auto_detect_en = cfg.get("auto_detect_english_field", True)

    target_note = note
    if not target_note and card:
        try:
            target_note = card.note()
        except Exception:
            pass

    # 1. Field-aware detection: Did the selection come from an English or Target language field?
    if target_note and auto_detect_en:
        clean_selected = text.lower()
        for field_name, field_val in target_note.items():
            clean_val = _clean_text(field_val).lower()
            if clean_selected in clean_val:
                fname_low = field_name.lower()
                if any(k in fname_low for k in ["english", "gloss", "translat", "meaning"]):
                    _log(f"Selection matched English field '{field_name}' -> en-US-JennyNeural")
                    return "en-US-JennyNeural"
                if "italian" in fname_low:
                    return "it-IT-ElsaNeural"
                if "french" in fname_low:
                    return "fr-FR-DeniseNeural"
                if "russian" in fname_low:
                    return "ru-RU-SvetlanaNeural"
                if "german" in fname_low:
                    return "de-DE-KatjaNeural"
                if "spanish" in fname_low:
                    return "es-ES-ElviraNeural"

    # 2. Inspect active card template TTS tag
    if card:
        try:
            tmpl = card.template()
            combined_fmt = tmpl.get("qfmt", "") + " " + tmpl.get("afmt", "")
            m = _TTS_TAG_RE.search(combined_fmt)
            if m:
                tag_lang = m.group(1).replace("-", "_")
                req_voices = m.group(2) or ""
                # Check voice aliases
                if tag_lang in VOICE_ALIASES and req_voices:
                    for alias, edge_target in VOICE_ALIASES[tag_lang].items():
                        if alias.lower() in req_voices.lower():
                            _log(f"Resolved voice from template alias '{alias}' -> {edge_target}")
                            return edge_target
                # Map standard language code to monolingual dedicated voice
                if tag_lang in DEFAULT_MONOLINGUAL_VOICES:
                    v = DEFAULT_MONOLINGUAL_VOICES[tag_lang]
                    _log(f"Resolved voice from template tag '{tag_lang}' -> {v}")
                    return v
                short_code = tag_lang.split("_")[0].lower()
                if short_code in DEFAULT_MONOLINGUAL_VOICES:
                    return DEFAULT_MONOLINGUAL_VOICES[short_code]
        except Exception as e:
            _log(f"Template inspection error: {e}")

    # 3. Check deck name mapping
    deck_name = ""
    if card and aqt.mw and aqt.mw.col:
        try:
            deck_name = aqt.mw.col.decks.name(card.did)
        except Exception:
            pass

    if deck_name:
        for pattern, voice in deck_voices.items():
            if pattern.lower() in deck_name.lower():
                _log(f"Matched deck '{deck_name}' with rule '{pattern}' -> {voice}")
                return voice

    # 4. Deck name heuristics
    if deck_name:
        d_low = deck_name.lower()
        if "italian" in d_low or "italiano" in d_low:
            return "it-IT-ElsaNeural"
        if "french" in d_low or "français" in d_low:
            return "fr-FR-DeniseNeural"
        if "russian" in d_low or "русский" in d_low or "рус" in d_low:
            return "ru-RU-SvetlanaNeural"
        if "german" in d_low or "deutsch" in d_low:
            return "de-DE-KatjaNeural"
        if "spanish" in d_low or "español" in d_low:
            return "es-ES-ElviraNeural"
        if "english" in d_low:
            return "en-US-JennyNeural"

    # 5. Script heuristics on the text itself
    if re.search(r"[\u0400-\u04FF]", text):  # Cyrillic
        _log(f"Cyrillic script detected in '{text}' -> ru-RU-SvetlanaNeural")
        return "ru-RU-SvetlanaNeural"
    if re.search(r"[\u3040-\u309F\u30A0-\u30FF]", text):  # Japanese Kana
        return "ja-JP-NanamiNeural"
    if re.search(r"[\u4E00-\u9FFF]", text):  # CJK Ideographs
        return "zh-CN-XiaoxiaoNeural"

    _log(f"Defaulting to voice: {default_v}")
    return default_v


def _get_card_headword(card: Any) -> str | None:
    """Extract primary headword/target expression from card when no text is highlighted."""
    try:
        note = card.note()
        # Priority fields: target language fields
        priority_keys = [
            "ItalianWord", "FrenchWord", "RussianWord", "GermanWord", "SpanishWord",
            "Word", "Front", "Expression", "Vocab", "Target"
        ]
        for k in priority_keys:
            if k in note and note[k].strip():
                clean = _clean_text(note[k])
                if clean:
                    return clean
        # Fallback to first non-empty field
        for _, val in note.items():
            clean = _clean_text(val)
            if clean:
                return clean
    except Exception:
        pass
    return None


def _get_current_selection() -> tuple[str, str]:
    """Retrieve current text selection and its context: ('text', 'reviewer'|'editor'|'widget')."""
    # 1. Check Reviewer WebEngineView
    if aqt.mw and aqt.mw.state == "review":
        if hasattr(aqt.mw, "reviewer") and hasattr(aqt.mw.reviewer, "web"):
            web = aqt.mw.reviewer.web
            if web and web.hasSelection():
                txt = _clean_text(web.selectedText())
                if txt:
                    return txt, "reviewer"

    # 2. Check focused widget (or its parent WebViews / QLineEdit / QTextEdit)
    if aqt.mw and hasattr(aqt.mw, "app"):
        w = aqt.mw.app.focusWidget()
        curr = w
        while curr:
            if hasattr(curr, "hasSelection") and hasattr(curr, "selectedText"):
                try:
                    if curr.hasSelection():
                        txt = _clean_text(curr.selectedText())
                        if txt:
                            return txt, "widget"
                except Exception:
                    pass
            curr = curr.parent()

    return "", ""


def pronounce_text(text: str, card: Any | None = None, note: Any | None = None) -> None:
    """Synthesize and play the specified text non-blockingly."""
    cfg = _load_config()
    clean = _clean_text(text)
    if not clean:
        return

    voice = resolve_voice_for_context(clean, card=card, note=note, cfg=cfg)
    speed = float(cfg.get("speed", 1.0))
    _log(f"Pronouncing text='{clean}' with voice='{voice}' (speed={speed})")

    if cfg.get("show_tooltip", True):
        # Format display label (truncate if very long)
        display_label = clean if len(clean) <= 35 else clean[:32] + "..."
        tooltip(f"🔊 {display_label} [{voice.split('-')[0]}]", period=1000)

    # 1. Check cache for instant hit (<1 ms)
    cached_path = _find_cached_audio(voice, speed, clean)
    if cached_path:
        _log(f"Cache hit for '{clean}': {cached_path}")
        _play_audio_file(cached_path, cfg)
        return

    # 2. Cache miss: Synthesize asynchronously in background
    target_mp3 = _get_cache_path_for_write(voice, speed, clean)

    def do_synthesis() -> str | None:
        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"{rate_pct:+d}%"
        t0 = time.time()
        try:
            _run_async(_synthesize_edge(clean, voice, rate_str, target_mp3))
            if os.path.exists(target_mp3) and os.path.getsize(target_mp3) > 0:
                dt = round((time.time() - t0) * 1000)
                _log(f"Edge TTS synthesized '{clean}' in {dt}ms")
                return target_mp3
        except Exception as err:
            _log(f"Edge TTS synthesis error for '{clean}': {err}")

        # Fallback to gTTS if Edge TTS encounters network issues
        if gTTS is not None:
            try:
                lang_code = voice.split("-")[0]
                tts = gTTS(text=clean, lang=lang_code, slow=speed < 1.0)
                tts.save(target_mp3)
                if os.path.exists(target_mp3) and os.path.getsize(target_mp3) > 0:
                    _log(f"gTTS fallback synthesized '{clean}'")
                    return target_mp3
            except Exception as gerr:
                _log(f"gTTS fallback error: {gerr}")

        return None

    def on_synthesis_done(future):
        try:
            res_path = future.result()
            if res_path:
                _play_audio_file(res_path, cfg)
            else:
                tooltip(f"TTS synthesis failed for '{clean}'")
        except Exception as ex:
            _log(f"Error in on_synthesis_done: {ex}")
            tooltip(f"TTS Error: {ex}")

    if aqt.mw and hasattr(aqt.mw, "taskman"):
        aqt.mw.taskman.run_in_background(do_synthesis, on_synthesis_done)
    else:
        # Standalone thread execution if taskman is not ready
        def run_thread():
            res = do_synthesis()
            if res:
                _play_audio_file(res, cfg)
        import threading
        threading.Thread(target=run_thread, daemon=True).start()


def trigger_pronounce() -> None:
    """Main entry point when shortcut (Alt+C) is pressed."""
    cfg = _load_config()
    text, ctx = _get_current_selection()
    card = aqt.mw.reviewer.card if (aqt.mw and aqt.mw.state == "review" and hasattr(aqt.mw.reviewer, "card")) else None

    if text:
        _log(f"Selection triggered ({ctx}): '{text}'")
        pronounce_text(text, card=card)
        return

    # No text selected: check headword fallback if in Reviewer
    if card and cfg.get("pronounce_card_if_no_selection", True):
        headword = _get_card_headword(card)
        if headword:
            _log(f"No selection, falling back to card headword: '{headword}'")
            pronounce_text(headword, card=card)
            return

    if cfg.get("show_tooltip", True):
        tooltip("Please select text to pronounce (Alt+C)", period=1200)


def on_editor_pronounce(editor: Any) -> None:
    """Entry point when Alt+C is pressed inside an Editor."""
    txt = ""
    if hasattr(editor, "web") and editor.web and editor.web.hasSelection():
        txt = _clean_text(editor.web.selectedText())

    note = getattr(editor, "note", None)
    card = getattr(editor, "card", None)

    if txt:
        pronounce_text(txt, card=card, note=note)
    else:
        if note:
            # Fallback to active field or first field
            for _, val in note.items():
                c = _clean_text(val)
                if c:
                    pronounce_text(c, card=card, note=note)
                    return
        tooltip("Please select text to pronounce (Alt+C)", period=1200)


# --- Hook Registrations ---

def _on_state_shortcuts_will_change(state: str, shortcuts: list[tuple[str, Any]]) -> None:
    """Register reviewer shortcut."""
    if state == "review":
        cfg = _load_config()
        shortcut_key = cfg.get("shortcut", "Alt+C")
        shortcuts.append((shortcut_key, trigger_pronounce))
        _log(f"Registered review shortcut '{shortcut_key}'")


def _on_editor_did_init_shortcuts(shortcuts: list[tuple], editor: Any) -> None:
    """Register editor shortcut."""
    cfg = _load_config()
    shortcut_key = cfg.get("shortcut", "Alt+C")
    shortcuts.append((shortcut_key, lambda ed=editor: on_editor_pronounce(ed), True))
    _log(f"Registered editor shortcut '{shortcut_key}'")


def _on_reviewer_context_menu(reviewer: Any, menu: QMenu) -> None:
    """Add 'Pronounce Selected Text (Alt+C)' to reviewer right-click context menu."""
    if reviewer.web and reviewer.web.hasSelection():
        sel = _clean_text(reviewer.web.selectedText())
        label = f'Pronounce "{sel[:20]}..." (Alt+C)' if len(sel) > 20 else f'Pronounce "{sel}" (Alt+C)'
    else:
        label = "Pronounce Selected Text (Alt+C)"

    action = QAction(label, menu)
    action.triggered.connect(trigger_pronounce)
    menu.addAction(action)


def _init_global_shortcuts() -> None:
    """Ensure a fallback window-level shortcut is always active on main window."""
    if aqt.mw:
        cfg = _load_config()
        shortcut_key = cfg.get("shortcut", "Alt+C")
        # Install shortcut on main window
        QShortcut(QKeySequence(shortcut_key), aqt.mw, activated=trigger_pronounce)
        _log(f"Installed window shortcut '{shortcut_key}' on mw")


gui_hooks.state_shortcuts_will_change.append(_on_state_shortcuts_will_change)
gui_hooks.editor_did_init_shortcuts.append(_on_editor_did_init_shortcuts)
gui_hooks.reviewer_will_show_context_menu.append(_on_reviewer_context_menu)
gui_hooks.profile_did_open.append(_init_global_shortcuts)

# Initialize on import if profile is already open
if aqt.mw and aqt.mw.col:
    _init_global_shortcuts()
