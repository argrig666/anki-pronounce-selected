#!/usr/bin/env python3
"""Comprehensive test suite for anki-pronounce-selected."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

addon_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, addon_dir)
sys.path.insert(0, os.path.join(addon_dir, "vendor"))

import __init__ as ps
import detector


class TestPronounceSelected(unittest.TestCase):
    def test_no_hardcoded_paths(self):
        """Requirement 1: 100% standalone, no hardcoded /home paths."""
        with open(os.path.join(addon_dir, "__init__.py"), "r") as f:
            content = f.read()
        self.assertNotIn("/home/", content)

    def test_non_selection_does_nothing(self):
        """Requirement 2: NOTHING happens on non-selection."""
        with patch.object(ps, "_get_current_selection", return_value=""):
            with patch.object(ps, "pronounce_text") as mock_pronounce:
                with patch.object(ps, "tooltip") as mock_tooltip:
                    ps.trigger_pronounce()
                    mock_pronounce.assert_not_called()
                    mock_tooltip.assert_not_called()

        mock_editor = MagicMock()
        mock_editor.web.hasSelection.return_value = False
        mock_editor.web.selectedText.return_value = ""
        with patch.object(ps, "pronounce_text") as mock_pronounce:
            with patch.object(ps, "tooltip") as mock_tooltip:
                ps.on_editor_pronounce(mock_editor)
                mock_pronounce.assert_not_called()
                mock_tooltip.assert_not_called()

    def test_auto_detect_language(self):
        """Requirement 3: Automatic language detection."""
        cases = [
            # Italian
            ("dire", "it-IT-ElsaNeural"),
            ("uno zaino", "it-IT-ElsaNeural"),
            ("Ho bisógno di ùno zàino per la scuòla.", "it-IT-ElsaNeural"),
            ("Con pròve miglióri, dirébbero il contrário.", "it-IT-ElsaNeural"),
            # English
            ("backpack", "en-US-JennyNeural"),
            ("With better evidence, they would say the opposite.", "en-US-JennyNeural"),
            ("to say / to tell", "en-US-JennyNeural"),
            # French
            ("apercevoir", "fr-FR-DeniseNeural"),
            ("J’ai aperçu mon voisin dans la foule.", "fr-FR-DeniseNeural"),
            # Spanish
            ("estudiar", "es-ES-ElviraNeural"),
            ("buenos días", "es-ES-ElviraNeural"),
            # German
            ("geschrieben", "de-DE-KatjaNeural"),
            ("Guten Morgen", "de-DE-KatjaNeural"),
            # Russian
            ("Здравствуйте", "ru-RU-SvetlanaNeural"),
            ("спасибо большое", "ru-RU-SvetlanaNeural"),
        ]

        for text, expected_voice in cases:
            voice = detector.get_voice_for_text(text)
            self.assertEqual(voice, expected_voice, f"Failed for text '{text}': got {voice}")

    def test_clean_text(self):
        self.assertEqual(ps._clean_text("  <b>ciao</b>  "), "ciao")
        self.assertEqual(ps._clean_text("ùno&nbsp;zàino[sound:123.mp3]"), "ùno zàino")
        self.assertEqual(ps._clean_text("/ˈdzai.no/"), "ˈdzai.no")

    def test_cache_and_synthesis(self):
        text = "buonasera"
        voice = "it-IT-ElsaNeural"
        speed = 1.0
        cache_file = ps._get_cache_path(voice, speed, text)
        if os.path.exists(cache_file):
            os.remove(cache_file)

        ps._run_async(ps._synthesize_edge(text, voice, "+0%", cache_file))
        self.assertTrue(os.path.exists(cache_file))
        self.assertGreater(os.path.getsize(cache_file), 0)
        os.remove(cache_file)


if __name__ == "__main__":
    unittest.main()
