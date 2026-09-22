# Support & Troubleshooting: Pronounce Selected Text

Welcome! If you are encountering issues, have questions, or want to suggest new features for **Pronounce Selected Text**, here is how to get help.

---

## 1. Quick Troubleshooting Checklist

### A. Nothing happens when I press Alt+C
1. **Selection & Fallback:**
   - If text is highlighted, the add-on pronounces the selected text.
   - If no text is highlighted, the add-on pronounces the configured `fallback_field` (defaults to `"ItalianExample"`, or template-specific example on verb cards). If `fallback_field` is set to `""` or the field is empty on the card, it remains silent.
2. **Keybinding Conflict:**
   Your desktop environment (Hyprland, GNOME, KDE) or window manager might reserve `Alt+C`.
   - In Anki, go to **Tools** → **Add-ons** → **Pronounce Selected Text** → **Config**.
   - Change `"shortcut": "Alt+C"` to another combination, such as `"Shift+Alt+C"`, `"Ctrl+Shift+P"`, or `"F4"`.
   - Restart Anki.
3. **Check the Debug Log:**
   Open your Anki add-on directory:
   `~/.local/share/Anki2/addons21/pronounce_selected/user_files/debug.log`
   This file records captured shortcuts, detected language, and playback attempts.

### B. No Sound / Audio Error
Ensure `mpv` is installed on your Linux distribution:
- **Arch Linux / Omarchy**: `sudo pacman -S mpv`
- **Ubuntu / Debian**: `sudo apt install mpv`
- **Fedora**: `sudo dnf install mpv`

If using PipeWire or PulseAudio, test mpv directly from your terminal:
```bash
mpv --ao=pipewire,pulse /path/to/any/audio.mp3
```

---

## 2. Reporting an Issue

If the problem persists, please open an issue on GitHub:
👉 **[Open a GitHub Issue](https://github.com/argrig666/anki-pronounce-selected/issues)**

When filing a bug report, please include:
1. **Anki Version**: (e.g. Anki 24.11 or 26.08) via **Help** → **About**.
2. **Linux Distribution & Desktop**: (e.g. Arch / Omarchy / Ubuntu, Hyprland / GNOME / KDE).
3. **Selected Text & Target Language**: The word or sentence that failed to pronounce.
4. **Debug Log**: The relevant lines from `user_files/debug.log`.

---

## 3. Feature Requests & Contributions

Feature suggestions, additional language voice mappings, and pull requests are warmly welcomed on our GitHub repository:
- **Repository**: [https://github.com/argrig666/anki-pronounce-selected](https://github.com/argrig666/anki-pronounce-selected)
- **Pull Requests**: [https://github.com/argrig666/anki-pronounce-selected/pulls](https://github.com/argrig666/anki-pronounce-selected/pulls)
