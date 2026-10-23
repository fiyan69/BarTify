"""
Unit tests for LRC parser and synchronizer.
"""

import unittest
from bartify.core.lrc_parser import parse_lrc


class TestLRCParser(unittest.TestCase):

    def test_basic_lrc_parsing(self):
        sample = """
        [ti:Sample Song]
        [ar:Sample Artist]
        [00:10.00] First line of song
        [00:15.50] Second line of song
        [00:25.00] Third line of song
        """
        parsed = parse_lrc(sample)
        self.assertEqual(len(parsed), 3)

        # Before any lyrics start
        self.assertIsNone(parsed.get_current_line(5.0))

        # At first line
        line1 = parsed.get_current_line(10.0)
        self.assertIsNotNone(line1)
        self.assertEqual(line1.text, "First line of song")

        # Between line 1 and 2
        line1_mid = parsed.get_current_line(12.0)
        self.assertEqual(line1_mid.text, "First line of song")

        # Line 2
        line2 = parsed.get_current_line(15.5)
        self.assertEqual(line2.text, "Second line of song")

    def test_multi_timestamp_line(self):
        sample = """
        [00:10.00][00:20.00] Repeated chorus line
        """
        parsed = parse_lrc(sample)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed.lines[0].timestamp, 10.0)
        self.assertEqual(parsed.lines[1].timestamp, 20.0)
        self.assertEqual(parsed.lines[0].text, "Repeated chorus line")
        self.assertEqual(parsed.lines[1].text, "Repeated chorus line")

    def test_line_progress_calculation(self):
        sample = """
        [00:00.00] Start
        [00:10.00] Next
        """
        parsed = parse_lrc(sample)
        # At start (0.0 sec) -> 0.0
        self.assertAlmostEqual(parsed.get_line_progress(0.0), 0.0, places=2)
        # At 5.0 sec -> 0.5
        self.assertAlmostEqual(parsed.get_line_progress(5.0), 0.5, places=2)
        # At 10.0 sec -> 0.0 for the new line
        self.assertAlmostEqual(parsed.get_line_progress(10.0), 0.0, places=2)

    def test_empty_and_corrupted_lrc(self):
        self.assertEqual(len(parse_lrc("")), 0)
        self.assertEqual(len(parse_lrc("Not an LRC format text")), 0)
        self.assertIsNone(parse_lrc("").get_current_line(10.0))


if __name__ == "__main__":
    unittest.main()
