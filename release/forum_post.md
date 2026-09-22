# [Release] Pronounce Selected Text — Instant Neural TTS (Azure / Edge) on Highlighted Text for Linux

Hey everyone!

I'm excited to share a focused and lightweight add-on for Anki on Linux: **Pronounce Selected Text**.

### The Idea
When reviewing cards or editing notes, we often encounter unfamiliar words, idioms, clitic combinations, or full sentences where we just want to hear how they sound immediately.

With **Pronounce Selected Text**, you simply highlight any text on a card (or in the note editor) and press **Shift+Alt+C**.

### Key Features
1. **Pure & Silent**: If no text is selected, **NOTHING happens**. No popups, no errors, no sounds. Complete silence.
2. **Automatic Language Detection**: Automatically recognizes whether the highlighted text is Italian, French, Spanish, German, Russian, English, Japanese, Chinese, etc., and routes it to the matching native voice.
3. **Dedicated Native Monolingual Neural Voices**: Uses high-quality Microsoft Azure / Edge Neural voices (`it-IT-ElsaNeural`, `fr-FR-DeniseNeural`, etc.) with dynamic SSML locale tagging to eliminate English phonetic leakage on shared vocabulary.
4. **Instant Caching**: Fast background synthesis on first review, instant (<1 ms) playback from disk on subsequent reviews.
5. **Zero Setup & Zero Keys**: Requires no accounts or API keys. 100% standalone.
6. **Low Latency Linux Audio**: Plays directly via `mpv` (PipeWire/PulseAudio) with preemption (rapid presses cleanly stop previous audio).

### Installation & Download
- Download the `.ankiaddon` file directly from GitHub Releases: [anki-pronounce-selected Releases](https://github.com/argrig666/anki-pronounce-selected/releases)
- In Anki: **Tools** -> **Add-ons** -> **Install from file...** -> select `pronounce_selected.ankiaddon`.

Feedback and contributions welcome on GitHub:
https://github.com/argrig666/anki-pronounce-selected
