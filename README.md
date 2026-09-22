# Pronounce Selected Text

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Anki](https://img.shields.io/badge/Anki-23.10%2B%20%7C%2024%2B%20%7C%2025%2B%20%7C%2026%2B-brightgreen)](https://apps.ankiweb.net/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20Omarchy-orange)](#system-requirements)

Instant, ultra-realistic text-to-speech pronunciation in Anki upon pressing **Alt+C** (configurable). Powered by Microsoft Azure / Edge Neural voices with automatic on-the-fly language detection.

---

## Key Highlights

- **Dual-Mode Pronunciation**:
  - **Selection Mode**: Highlight any word, clause, idiom, or full sentence across the Card Reviewer, Note Editor, or Card Browser and press **Alt+C** to hear it spoken instantly.
  - **Fallback Field Mode (New!)**: Press **Alt+C** without selecting any text, and the add-on automatically pronounces a designated note field (default: `"ItalianExample"`).
  - **Smart Conjugation Matching**: On verb conjugation cards, the add-on dynamically extracts the card's active grammatical person (e.g. *Io*, *Tu*, *Loro*) and pronounces the matching example field (e.g. `"Loro example"`).
- **On-The-Fly Language Auto-Detection**: Pure-Python zero-dependency detector automatically identifies the language (Italian, French, Spanish, German, Russian, English, Portuguese, Japanese, Chinese, etc.) and routes to the dedicated native monolingual voice.
- **Dedicated Native Monolingual Voices**: Enforces neural TTS principles: defaults to dedicated native voices (`it-IT-ElsaNeural`, `fr-FR-DeniseNeural`, `es-ES-ElviraNeural`, `de-DE-KatjaNeural`, `ru-RU-SvetlanaNeural`, `en-US-JennyNeural`) to prevent English phonetic leakage on shared vocabulary.
- **Dynamic SSML Locale Integrity**: Root `<speak xml:lang='...'>` dynamically matches the detected voice locale for authentic native intonation.
- **Multi-Layout Keyboard Support (English & Russian)**: Built-in physical key code and Cyrillic mapping. `Alt+C` works seamlessly whether your active keyboard layout is English or Russian.
- **Zero-Restart Live Configuration**: Adjust shortcut, volume, or fallback fields in **Tools** → **Add-ons** → **Config** and changes apply immediately on-the-fly without restarting Anki.
- **Instant Disk Caching (<1 ms)**: Caches synthesized audio locally. Repeat reviews play instantly without network requests.
- **Audio Preemption**: Rapid keypresses cleanly terminate previous playback so new audio begins immediately.
- **100% Standalone**: Self-contained with bundled dependencies. Zero setup or API keys required.
- **Right-Click Context Menu**: Also adds a *"Pronounce Selected Text (Alt+C)"* action to the reviewer context menu.

---

## Default Shortcut & Configuration

Default shortcut is **Alt+C**.

To customize the shortcut or adjust settings, go to **Tools** → **Add-ons** → **Pronounce Selected Text** → **Config**:

```json
{
  "shortcut": "Alt+C",
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
