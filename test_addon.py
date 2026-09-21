#!/usr/bin/env python3
"""Automated tests for anki-pronounce-selected add-on."""

import os
import sys
import unittest

addon_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, addon_dir)
sys.path.insert(0, os.path.join(addon_dir, "vendor"))

import __init__ as ps


class MockCard:
    def __init__(self, note_fields: dict[str, str], deck_name: str = "", qfmt: str = "", afmt: str = ""):
        self._note_fields = note_fields
        self.did = 1
        self._deck_name = deck_name
        self._tmpl = {"qfmt": qfmt, "afmt": afmt}

    def note(self):
        class Note:
            def __init__(self, fields):
                self._fields = fields
            def items(self):
                return self._fields.items()
            def __getitem__(self, k):
                return self._fields[k]
            def __contains__(self, k):
                return k in self._fields
        return Note(self._note_fields)

    def template(self):
        return self._tmpl


class TestPronounceSelected(unittest.TestCase):
    def setUp(self):
        self.cfg = ps._load_config()

    def test_clean_text(self):
        self.assertEqual(ps._clean_text("  <b>ciao</b>  "), "ciao")
        self.assertEqual(ps._clean_text("ùno&nbsp;zàino[sound:123.mp3]"), "ùno zàino")
        self.assertEqual(ps._clean_text("/ˈdzai.no/"), "ˈdzai.no")

    def test_voice_resolution_italian_card(self):
        fields = {
            "ItalianWord": "uno zaino",
            "IPA": "/ˈdzai.no/",
            "EnglishWord": "backpack; rucksack",
            "ItalianExample": "Ho bisógno di ùno zàino per la scuòla.",
            "EnglishExample": "I need a backpack for school.",
        }
        card = MockCard(
            fields,
            deck_name="Italian Decks::My Italian Vocabulary",
            qfmt="{{tts it_IT voices=Apple_Federica_(Premium):ItalianWord}}",
        )

        # 1. Target Italian word/phrase
        v_target = ps.resolve_voice_for_context("ùno zàino", card=card, cfg=self.cfg)
        self.assertEqual(v_target, "it-IT-ElsaNeural")

        v_ex = ps.resolve_voice_for_context("bisógno", card=card, cfg=self.cfg)
        self.assertEqual(v_ex, "it-IT-ElsaNeural")

        # 2. English gloss substring should resolve to English Jenny voice!
        v_en = ps.resolve_voice_for_context("backpack", card=card, cfg=self.cfg)
        self.assertEqual(v_en, "en-US-JennyNeural")

        v_en_ex = ps.resolve_voice_for_context("I need a backpack", card=card, cfg=self.cfg)
        self.assertEqual(v_en_ex, "en-US-JennyNeural")

    def test_voice_resolution_french_card(self):
        fields = {
            "FrenchWord": "apercevoir",
            "IPA": "/a.pɛʁ.sə.vwaʁ/",
            "EnglishWord": "to notice; to catch sight of",
            "FrenchExample": "J’ai aperçu mon voisin dans la foule.",
            "EnglishExample": "I caught sight of my neighbor in the crowd.",
        }
        card = MockCard(
            fields,
            deck_name="French Decks::My French Vocabulary",
            qfmt="{{tts fr_FR voices=Apple_Audrey_(Premium):FrenchWord}}",
        )

        v_fr = ps.resolve_voice_for_context("apercevoir", card=card, cfg=self.cfg)
        self.assertEqual(v_fr, "fr-FR-DeniseNeural")

        v_en = ps.resolve_voice_for_context("catch sight of", card=card, cfg=self.cfg)
        self.assertEqual(v_en, "en-US-JennyNeural")

    def test_voice_resolution_script_detection(self):
        # Cyrillic script
        v_ru = ps.resolve_voice_for_context("Здравствуйте", card=None, cfg=self.cfg)
        self.assertEqual(v_ru, "ru-RU-SvetlanaNeural")

    def test_headword_extraction(self):
        fields = {
            "ItalianWord": "uno zaino",
            "EnglishWord": "backpack",
        }
        card = MockCard(fields)
        headword = ps._get_card_headword(card)
        self.assertEqual(headword, "uno zaino")

    def test_synthesis_and_cache(self):
        text = "buongiorno"
        voice = "it-IT-ElsaNeural"
        speed = 1.0
        cache_path = ps._get_cache_path_for_write(voice, speed, text)
        if os.path.exists(cache_path):
            os.remove(cache_path)

        # Synthesize via edge_tts
        ps._run_async(ps._synthesize_edge(text, voice, "+0%", cache_path))
        self.assertTrue(os.path.exists(cache_path))
        self.assertGreater(os.path.getsize(cache_path), 0)

        # Verify cache lookup finds it
        found = ps._find_cached_audio(voice, speed, text)
        self.assertEqual(found, cache_path)

        # Clean up test file
        os.remove(cache_path)


if __name__ == "__main__":
    unittest.main()
