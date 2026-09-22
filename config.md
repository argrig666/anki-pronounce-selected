# Pronounce Selected Text Configuration

### `shortcut` (default: `"Shift+Alt+C"`)
Keyboard shortcut that triggers pronunciation. Can be changed to any combination such as `"Shift+Alt+C"`, `"Alt+C"`, `"Ctrl+Alt+P"`, or `"F4"`.

### `volume` (default: `140`)
Software audio volume percentage passed to `mpv` (100 = 100%, 140 = 140% volume boost).

### `speed` (default: `1.0`)
Speech playback rate multiplier (1.0 = normal, 0.9 = 10% slower, 1.1 = 10% faster).

### `audio_output` (default: `"pipewire,pulse"`)
Audio output driver for `mpv` (supports PipeWire and PulseAudio).

### `show_tooltip` (default: `false`)
Set to `true` if you want a subtle status tooltip showing the text and detected language voice. Default is `false` for completely distraction-free audio.

### `debug_log` (default: `true`)
Appends diagnostic logs to `user_files/debug.log`.
