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
        # 1. Test JS bridge with empty text
        with patch.object(ps, "pronounce_text") as mock_pronounce:
            res = ps._on_webview_did_receive_js_message((False, None), "pronounce_selected:", None)
            mock_pronounce.assert_not_called()
            self.assertEqual(res, (True, None))

        # 2. Test Qt trigger with empty clipboard & empty webview
        with patch.object(ps, "QApplication") as mock_app:
            mock_app.clipboard().supportsSelection.return_value = False
            with patch.object(ps, "_get_active_webview", return_value=None):
                with patch.object(ps, "pronounce_text") as mock_pronounce:
                    ps.trigger_pronounce()
                    mock_pronounce.assert_not_called()

    def test_js_bridge_triggers_pronounce(self):
        """Test JS bridge correctly decodes and triggers pronunciation."""
        with patch.object(ps, "pronounce_text") as mock_pronounce:
            res = ps._on_webview_did_receive_js_message((False, None), "pronounce_selected:buongiorno", None)
            mock_pronounce.assert_called_once_with("buongiorno", context_lang=None)
            self.assertEqual(res, (True, None))

    def test_js_listener_injected(self):
        """Verify DOM keydown listener is injected into web views."""
        mock_content = MagicMock()
        mock_content.head = ""
        ps._on_webview_will_set_content(mock_content, None)
        self.assertIn("pronounce_selected:", mock_content.head)
        self.assertIn("KeyC", mock_content.head)

    def test_auto_detect_language(self):
        """Requirement 3: Automatic language detection."""
        cases = [
            ("dire", "it-IT-ElsaNeural"),
            ("uno zaino", "it-IT-ElsaNeural"),
            ("Ho bisógno di ùno zàino per la scuòla.", "it-IT-ElsaNeural"),
            ("Con pròve miglióri, dirébbero il contrário.", "it-IT-ElsaNeural"),
            ("backpack", "en-US-JennyNeural"),
            ("With better evidence, they would say the opposite.", "en-US-JennyNeural"),
            ("to say / to tell", "en-US-JennyNeural"),
            ("apercevoir", "fr-FR-DeniseNeural"),
            ("J’ai aperçu mon voisin dans la foule.", "fr-FR-DeniseNeural"),
            ("estudiar", "es-ES-ElviraNeural"),
            ("buenos días", "es-ES-ElviraNeural"),
            ("geschrieben", "de-DE-KatjaNeural"),
            ("Guten Morgen", "de-DE-KatjaNeural"),
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
