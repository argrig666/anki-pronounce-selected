# Pronounce Selected Text (Alt+C) Configuration

### `shortcut` (default: `"Alt+C"`)
Keyboard shortcut that triggers pronunciation. Can be changed to any Qt key sequence such as `"Alt+C"`, `"Ctrl+Alt+P"`, or `"F4"`.

### `volume` (default: `140`)
Software audio volume percentage passed to `mpv` (100 = 100%, 140 = 140% boost).

### `speed` (default: `1.0`)
Speech speed multiplier (1.0 = normal, 0.9 = 10% slower, 1.1 = 10% faster).

### `audio_output` (default: `"pipewire,pulse"`)
Audio output driver for `mpv`.

### `show_tooltip` (default: `false`)
Whether to show a subtle tooltip showing the text and detected language voice. Default is `false` for clean, distraction-free audio playback.

### `debug_log` (default: `false`)
Set to `true` to append diagnostic logs to `user_files/debug.log`.
