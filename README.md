# Pronounce Selected Text (Alt+C) for Anki

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Anki](https://img.shields.io/badge/Anki-23.10%2B%20%7C%2024%2B%20%7C%2025%2B%20%7C%2026%2B-brightgreen)](https://apps.ankiweb.net/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20Omarchy-orange)](#system-requirements)

Instant, ultra-realistic pronunciation of highlighted or selected text in Anki upon pressing **Alt+C**. Powered by state-of-the-art Microsoft Azure / Edge Neural voices.

---

## Features

- **Instant Hotkey (`Alt+C`)**: Highlight any word, clitic group, idiom, or full example sentence anywhere in Anki (Reviewer, Editor, or Browser) and press `Alt+C` for instant pronunciation.
- **Dedicated Native Monolingual Voices**: Enforces the neural TTS principle of dedicated monolingual voices (`it-IT-ElsaNeural`, `fr-FR-DeniseNeural`, `es-ES-ElviraNeural`, `de-DE-KatjaNeural`, `ru-RU-SvetlanaNeural`) to prevent English phonetic leakage on shared vocabulary.
- **Dynamic SSML Locale Integrity**: Derives root `<speak xml:lang='...'>` dynamically from the voice locale.
- **Context-Aware Field Intelligence**: Automatically distinguishes when you select an English gloss (`EnglishWord`, `EnglishExample`) versus target language vocabulary, routing to the appropriate native voice.
- **Smart Headword Fallback**: If no text is selected when `Alt+C` is pressed in the Reviewer, automatically pronounces the primary target expression of the card.
- **Instant Disk Caching (<1 ms)**: Caches synthesized audio locally and shares cache hits with `linux_tts_player`. Repeat reviews play with zero network latency.
- **Non-Blocking Background Synthesis**: New words are synthesized asynchronously without freezing or stuttering the Anki user interface.
- **Audio Preemption**: Rapidly highlighting words cleanly stops any previous playback and begins the new pronunciation immediately.
- **Context Menu Integration**: Right-click context menu options in both Card Reviewer and Note Editor.

---

## Default Voices

| Language | Default Dedicated Voice | Gender | Alternative Voices |
| :--- | :--- | :--- | :--- |
| **Italian (`it_IT`)** | `it-IT-ElsaNeural` | Female | `it-IT-DiegoNeural` (M), `it-IT-IsabellaNeural` (F) |
| **French (`fr_FR`)** | `fr-FR-DeniseNeural` | Female | `fr-FR-HenriNeural` (M), `fr-FR-EloiseNeural` (F) |
| **French Canada (`fr_CA`)** | `fr-CA-SylvieNeural` | Female | `fr-CA-JeanNeural` (M), `fr-CA-AntoineNeural` (M) |
| **Spanish Spain (`es_ES`)** | `es-ES-ElviraNeural` | Female | `es-ES-AlvaroNeural` (M) |
| **Spanish Mexico (`es_MX`)** | `es-MX-DaliaNeural` | Female | `es-MX-JorgeNeural` (M) |
| **German (`de_DE`)** | `de-DE-KatjaNeural` | Female | `de-DE-ConradNeural` (M) |
| **Russian (`ru_RU`)** | `ru-RU-SvetlanaNeural` | Female | `ru-RU-DmitryNeural` (M) |
| **English US (`en_US`)** | `en-US-JennyNeural` | Female | `en-US-GuyNeural` (M), `en-US-AriaNeural` (F) |
| **English UK (`en_GB`)** | `en-GB-SoniaNeural` | Female | `en-GB-RyanNeural` (M) |

---

## Configuration

In Anki, navigate to **Tools** → **Add-ons** → select **Pronounce Selected Text (Alt+C)** → click **Config**.

```json
{
  "shortcut": "Alt+C",
  "default_voice": "it-IT-ElsaNeural",
  "volume": 140,
  "audio_output": "pipewire,pulse",
  "speed": 1.0,
  "pronounce_card_if_no_selection": true,
  "auto_detect_english_field": true,
  "show_tooltip": true,
  "deck_voices": {
    "Italian Decks": "it-IT-ElsaNeural",
    "French Decks": "fr-FR-DeniseNeural",
    "English Dict": "en-US-JennyNeural",
    "Русский": "ru-RU-SvetlanaNeural"
  },
  "debug_log": false
}
```

---

## License

GNU Affero General Public License v3.0 (AGPL-3.0).
