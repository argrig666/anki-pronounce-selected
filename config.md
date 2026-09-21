# Pronounce Selected Text (Alt+C) Configuration

### `shortcut` (default: `"Alt+C"`)
Keyboard shortcut that triggers pronunciation. Can be changed to any Qt key sequence such as `"Alt+C"`, `"Ctrl+Alt+P"`, or `"F4"`.

### `default_voice` (default: `"it-IT-ElsaNeural"`)
Fallback Azure Neural voice if no deck mapping or template tag matches.

Recommended dedicated monolingual voices:
- **Italian**: `it-IT-ElsaNeural` (F) or `it-IT-DiegoNeural` (M)
- **French**: `fr-FR-DeniseNeural` (F) or `fr-FR-HenriNeural` (M)
- **Spanish**: `es-ES-ElviraNeural` (F) or `es-ES-AlvaroNeural` (M)
- **German**: `de-DE-KatjaNeural` (F) or `de-DE-ConradNeural` (M)
- **Russian**: `ru-RU-SvetlanaNeural` (F) or `ru-RU-DmitryNeural` (M)
- **English US**: `en-US-JennyNeural` (F) or `en-US-GuyNeural` (M)
- **English UK**: `en-GB-SoniaNeural` (F) or `en-GB-RyanNeural` (M)

### `deck_voices`
Map deck names (or deck name substrings) directly to specific voices:
```json
"deck_voices": {
  "Italian Decks": "it-IT-ElsaNeural",
  "French Decks": "fr-FR-DeniseNeural",
  "Русский": "ru-RU-SvetlanaNeural"
}
```

### `pronounce_card_if_no_selection` (default: `true`)
If `true`, pressing `Alt+C` in the Card Reviewer when no text is selected will automatically pronounce the primary target word/expression of the card (e.g. `ItalianWord`, `FrenchWord`, or the first non-empty field).

### `auto_detect_english_field` (default: `true`)
If `true`, when you select text in an English gloss field (e.g. `EnglishWord`, `EnglishExample`), it will be pronounced using the English neural voice (`en-US-JennyNeural`) rather than the target language voice.

### `volume` (default: `140`)
Software audio volume percentage passed to `mpv` (100 = 100%, 140 = 140% boost).

### `speed` (default: `1.0`)
Speech speed multiplier (1.0 = normal, 0.9 = 10% slower, 1.1 = 10% faster).

### `audio_output` (default: `"pipewire,pulse"`)
Audio output driver for `mpv`.

### `show_tooltip` (default: `true`)
Whether to show a brief tooltip showing what is being pronounced.

### `debug_log` (default: `false`)
Set to `true` to append diagnostic logs to `user_files/debug.log`.
