import unittest

from research.core import Research


class StartTest(unittest.TestCase):
    def test_start_returns_true(self):
        self.assertTrue(Research().start("r-1", 5000, 0))

    def test_running_counts_project(self):
        book = Research()
        book.start("r-1", 5000, 0)
        self.assertEqual(book.running(), 1)


class AdvanceTest(unittest.TestCase):
    def test_advance_returns_done_count(self):
        book = Research()
        self.assertEqual(book.advance(0), 0)

    def test_scanned_starts_at_zero(self):
        self.assertEqual(Research().scanned_count(), 0)


if __name__ == "__main__":
    unittest.main()
