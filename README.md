# Pronounce Selected Text

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Anki](https://img.shields.io/badge/Anki-23.10%2B%20%7C%2024%2B%20%7C%2025%2B%20%7C%2026%2B-brightgreen)](https://apps.ankiweb.net/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20Omarchy-orange)](#system-requirements)

Instant, ultra-realistic text-to-speech pronunciation of highlighted text in Anki upon pressing **Shift+Alt+C** (or configurable shortcut). Powered by Microsoft Azure / Edge Neural voices with dynamic automatic language detection.

---

## Features

- **Selection Pronunciation**: Highlights any word, phrase, idiom, or full sentence across the Card Reviewer, Note Editor, or Card Browser and pronounces it instantly.
- **Smart Fallback on Non-Selection**: If no text is selected when pressing the shortcut, the add-on automatically pronounces a configurable card field (default: `"ItalianExample"`). On verb conjugation cards, it intelligently speaks the template-specific example (e.g. `"Loro example"`). Set to `""` in config if you prefer completely silent behavior when nothing is selected.
- **On-The-Fly Language Auto-Detection**: Automatically identifies the language of the selected text (Italian, French, Spanish, German, Russian, English, Portuguese, Japanese, Chinese, and more) and speaks it with the corresponding dedicated native voice.
- **Dedicated Native Monolingual Voices**: Enforces neural TTS invariants: uses dedicated native monolingual voices (`it-IT-ElsaNeural`, `fr-FR-DeniseNeural`, `es-ES-ElviraNeural`, `de-DE-KatjaNeural`, `ru-RU-SvetlanaNeural`) to prevent English phonetic leakage on shared vocabulary and cognates.
- **Dynamic SSML Locale Integrity**: Root `<speak xml:lang='...'>` dynamically matches the detected voice locale.
- **Dual DOM & Qt Capture**: Directly intercepts keypresses in the card webview DOM for 100% instant, reliable response on Linux.
- **Instant Disk Caching (<1 ms)**: Caches synthesized audio locally. Repeat reviews play instantly without network access.
- **Audio Preemption**: Rapidly highlighting words cleanly stops previous playback so the new pronunciation plays immediately.
- **Zero-Restart Live Config**: Any changes made in **Tools** → **Add-ons** → **Config** take effect immediately on-the-fly without needing to restart Anki.
- **Multi-Layout Keyboard Support**: Fully layout-resilient (physical key code + Cyrillic mapping). Works seamlessly whether your active keyboard layout is English or Russian.
- **100% Standalone**: Self-contained with all Python dependencies bundled. Zero setup or API keys needed.
- **Right-Click Menu**: Also adds a *"Pronounce Selected Text"* action to the reviewer right-click context menu.

---

## Default Shortcut & Configuration

Default shortcut is **Shift+Alt+C**.

To change the shortcut or adjust configuration, go to **Tools** → **Add-ons** → **Pronounce Selected Text** → **Config**:

```json
{
  "shortcut": "Shift+Alt+C",
  "volume": 140,
  "audio_output": "pipewire,pulse",
  "speed": 1.0,
  "show_tooltip": false,
  "fallback_field": "ItalianExample",
  "debug_log": true
}
```

---

## Prerequisites

Ensure `mpv` is installed on your Linux distribution:
- **Arch Linux / Omarchy**: `sudo pacman -S mpv`
- **Ubuntu / Debian**: `sudo apt install mpv`
- **Fedora**: `sudo dnf install mpv`

---

## License

GNU Affero General Public License v3.0 (AGPL-3.0). See [LICENSE](LICENSE) for details.
