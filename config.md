# Pronounce Selected Text Configuration

### `shortcut` (default: `"Alt+C"`)
Keyboard shortcut that triggers pronunciation. Can be changed to any combination such as `"Alt+C"`, `"Shift+Alt+C"`, `"Ctrl+Alt+P"`, or `"F4"`.

### `volume` (default: `140`)
Software audio volume percentage passed to `mpv` (100 = 100%, 140 = 140% volume boost).

### `speed` (default: `1.0`)
Speech playback rate multiplier (1.0 = normal, 0.9 = 10% slower, 1.1 = 10% faster).

### `audio_output` (default: `"pipewire,pulse"`)
Audio output driver for `mpv` (supports PipeWire and PulseAudio).

### `show_tooltip` (default: `false`)
Set to `true` if you want a subtle status tooltip showing the text and detected language voice. Default is `false` for completely distraction-free audio.

### `fallback_field` (default: `"ItalianExample"`)
Preferred field to pronounce when no text is highlighted or selected. The add-on always scopes this to the **current card**:
- If the active card’s template includes `fallback_field`, that field is read.
- Otherwise the add-on reads a target-language example field that the **current card** actually displays (e.g. `"Voi example"` on a Voi conjugation card, `"FrenchExample"` on a French card).
- It does not read sibling fields that belong to other cards of the same note (e.g. it will not read `"Io example"` while you are reviewing Voi).
- Set to any field name (e.g. `"ItalianExample"`, `"FrenchExample"`, `"Example"`, `"Front"`).
- Set to `""` (empty) if you prefer completely silent behavior when nothing is selected.

### `debug_log` (default: `true`)
Appends diagnostic logs to `user_files/debug.log`.
