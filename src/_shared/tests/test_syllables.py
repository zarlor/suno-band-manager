#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for syllables: each adjustment rule of the shared counter, pinned by word.

The lyric transformer's syllable counter and the band manager's WIP capture both
count with this module, so a rule that slips shifts every per-line count.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from syllables import SYLLABLE_OVERRIDES, count_line_syllables, count_syllables  # noqa: E402


class SyllableCase(unittest.TestCase):
    def assert_counts(self, expected):
        for word, n in expected.items():
            with self.subTest(word=word):
                self.assertEqual(count_syllables(word), n)


class TestVowelClusters(SyllableCase):
    def test_one_cluster_one_syllable(self):
        self.assert_counts({"cat": 1, "tree": 1, "rain": 1, "sky": 1, "moon": 1})

    def test_separate_clusters_count_separately(self):
        self.assert_counts({"hello": 2, "window": 2, "morning": 2, "banana": 3, "america": 4})

    def test_a_word_with_no_vowel_still_counts_one(self):
        self.assert_counts({"hmm": 1, "shh": 1})

    def test_nothing_countable_is_zero(self):
        self.assert_counts({"": 0, "   ": 0, "!!!": 0, "42": 0, "—": 0})

    def test_case_and_punctuation_do_not_change_the_count(self):
        self.assert_counts({"Hello,": 2, "WINDOW!": 2, '"morning"': 2, "(rain)": 1})


class TestSilentE(SyllableCase):
    def test_final_e_is_silent(self):
        self.assert_counts({"time": 1, "love": 1, "home": 1, "smile": 1, "here": 1, "more": 1, "everyone": 3})

    def test_double_e_is_sounded(self):
        self.assert_counts({"coffee": 2, "free": 1, "agree": 2})

    def test_consonant_le_is_a_syllable(self):
        self.assert_counts({"table": 2, "candle": 2, "apple": 2, "whole": 1})


class TestEdEnding(SyllableCase):
    def test_ed_is_silent_after_most_consonants(self):
        self.assert_counts({"walked": 1, "loved": 1, "turned": 1, "jumped": 1})

    def test_ed_is_a_syllable_after_t_or_d(self):
        self.assert_counts({"wanted": 2, "needed": 2, "started": 2, "faded": 2})

    def test_short_ed_words_keep_their_vowel(self):
        self.assert_counts({"red": 1, "bed": 1})


class TestEsEnding(SyllableCase):
    def test_es_is_silent_after_most_consonants(self):
        self.assert_counts({"makes": 1, "times": 1, "names": 1, "loves": 1, "stones": 1})

    def test_es_is_a_syllable_after_s_z_x(self):
        self.assert_counts({"boxes": 2, "roses": 2, "kisses": 2, "buzzes": 2})

    def test_es_is_a_syllable_after_ch_and_sh(self):
        self.assert_counts({"wishes": 2, "watches": 2, "dishes": 2, "churches": 2, "reaches": 2})

    def test_es_is_a_syllable_after_soft_c_and_g(self):
        self.assert_counts({"faces": 2, "places": 2, "changes": 2, "bridges": 2, "voices": 2})

    def test_the_ache_family_keeps_its_silent_e(self):
        self.assert_counts({"ache": 1, "aches": 1, "heartache": 2, "heartaches": 2, "headaches": 2})


class TestOverrides(SyllableCase):
    def test_overrides_win_over_the_heuristic(self):
        self.assert_counts({"the": 1, "fire": 2, "every": 3, "people": 2, "beautiful": 3})

    def test_every_override_is_returned_as_written(self):
        for word, n in SYLLABLE_OVERRIDES.items():
            with self.subTest(word=word):
                self.assertEqual(count_syllables(word), n)

    def test_contractions(self):
        self.assert_counts({"I'm": 1, "don't": 1, "couldn't": 2, "didn't": 2, "isn't": 2})

    def test_curly_apostrophes_find_the_same_overrides(self):
        self.assert_counts({"I’m": 1, "don’t": 1, "couldn’t": 2, "didn’t": 2, "isn’t": 2})
        self.assertEqual(count_syllables("didnʼt"), 2)


class TestAccents(SyllableCase):
    def test_accented_final_e_is_sounded(self):
        self.assert_counts({"café": 2, "cliché": 2, "résumé": 3, "soufflé": 2, "café,": 2})

    def test_accented_e_survives_a_plural_or_possessive(self):
        self.assert_counts({"cafés": 2, "café’s": 2})

    def test_accented_e_before_a_final_e(self):
        self.assert_counts({"née": 1, "entrée": 2, "Renée": 2})

    def test_a_silent_e_after_an_accented_vowel_stays_silent(self):
        self.assert_counts({"crème": 1, "fête": 1})

    def test_other_accented_letters_count_as_their_base_letter(self):
        self.assert_counts({"corazón": 3, "señorita": 4, "déjà": 2, "über": 2, "mañana": 3})

    def test_accented_and_plain_spellings_agree_where_the_e_is_not_final(self):
        for accented, plain in (("corazón", "corazon"), ("señorita", "senorita"), ("déjà", "deja")):
            with self.subTest(word=accented):
                self.assertEqual(count_syllables(accented), count_syllables(plain))


class TestLines(unittest.TestCase):
    def test_a_line_is_the_sum_of_its_words(self):
        self.assertEqual(count_line_syllables("hello window morning"), 6)
        self.assertEqual(count_line_syllables("cat dog"), 2)

    def test_inline_tags_are_not_counted(self):
        self.assertEqual(count_line_syllables("[Whispered] hello world"), 3)
        self.assertEqual(count_line_syllables("hello [soft, breathy] world [fade out]"), 3)

    def test_a_tag_only_or_empty_line_is_zero(self):
        self.assertEqual(count_line_syllables("[Verse 1]"), 0)
        self.assertEqual(count_line_syllables(""), 0)

    def test_curly_apostrophes_and_accents_in_a_line(self):
        self.assertEqual(count_line_syllables("I didn’t walk to the café"), 8)

    def test_punctuation_between_words_adds_nothing(self):
        self.assertEqual(count_line_syllables("hello, world — hello!"), 5)


if __name__ == "__main__":
    unittest.main()
