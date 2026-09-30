import random
import unittest

from research.core import Research


class SlotsTest(unittest.TestCase):
    def test_rejects_over_slots(self):
        book = Research(slots=2)
        results = [book.start("r-%d" % i, 5000, 0) for i in range(3)]
        self.assertEqual(results, [True, True, False])
        self.assertEqual(book.running(), 2)

    def test_rejected_start_does_not_occupy_slot(self):
        book = Research(slots=1)
        self.assertTrue(book.start("r-1", 5000, 0))
        self.assertFalse(book.start("r-2", 5000, 0))
        self.assertEqual(book.running(), 1)
        self.assertFalse(book.start("r-2", 5000, 0))
        self.assertEqual(book.running(), 1)

    def test_freed_slot_can_be_used(self):
        book = Research(slots=1)
        book.start("r-1", 5000, 0)
        self.assertFalse(book.start("r-2", 1000, 0))
        self.assertEqual(book.advance(5000), 1)
        self.assertTrue(book.start("r-2", 1000, 5000))
        self.assertEqual(book.running(), 1)


class TimeCompletionTest(unittest.TestCase):
    def test_completes_by_real_time(self):
        book = Research(slots=2)
        book.start("r-1", 5000, 0)
        self.assertEqual(book.advance(4999), 0)
        self.assertEqual(book.running(), 1)
        self.assertEqual(book.advance(5000), 1)
        self.assertEqual(book.running(), 0)

    def test_independent_of_advance_call_count(self):
        book = Research(slots=2)
        book.start("r-1", 5000, 0)
        for now in (1000, 2000, 3000, 4000):
            self.assertEqual(book.advance(now), 0)
        self.assertEqual(book.advance(4999), 0)
        self.assertEqual(book.advance(6000), 1)

    def test_uses_own_start_time(self):
        book = Research(slots=2)
        book.start("r-1", 5000, 1000)
        self.assertEqual(book.advance(5999), 0)
        self.assertEqual(book.advance(6000), 1)


class IdempotencyTest(unittest.TestCase):
    def test_duplicate_submit_returns_false(self):
        book = Research(slots=2)
        self.assertTrue(book.start("r-1", 5000, 0))
        self.assertFalse(book.start("r-1", 9999, 100))
        self.assertEqual(book.running(), 1)

    def test_duplicate_submit_does_not_reset_progress(self):
        book = Research(slots=2)
        book.start("r-1", 5000, 0)
        self.assertEqual(book.advance(4000), 0)
        self.assertFalse(book.start("r-1", 99999, 4000))
        self.assertEqual(book.advance(5000), 1)
        self.assertEqual(book.running(), 0)

    def test_resubmit_after_completion_rejected(self):
        book = Research(slots=2)
        book.start("r-1", 1000, 0)
        self.assertEqual(book.advance(1000), 1)
        self.assertFalse(book.start("r-1", 1000, 1000))
        self.assertEqual(book.running(), 0)
        self.assertEqual(len(book.done), 1)


class InvariantTest(unittest.TestCase):
    def test_done_set_is_monotonic_and_slots_hold(self):
        rnd = random.Random(1234)
        book = Research(slots=3)
        now = 0
        done_count = 0
        for _ in range(2000):
            now += rnd.randrange(0, 500)
            if rnd.random() < 0.7:
                book.start("r-%d" % rnd.randrange(10), rnd.randrange(1, 4000), now)
            else:
                book.advance(now)
            self.assertLessEqual(book.running(), book.slots)
            self.assertGreaterEqual(len(book.done), done_count)
            done_count = len(book.done)


class QueryCostTest(unittest.TestCase):
    def test_running_is_o1_and_does_not_scan(self):
        book = Research(slots=100000)
        for i in range(3000):
            book.start("r-%d" % i, 5000, 0)
        for _ in range(3000):
            self.assertEqual(book.running(), 3000)
        self.assertLessEqual(book.scanned_count(), 3000)


class ReferenceResearch:
    """参考实现：并行位 + 按真实时间完成 + 幂等提交，用最直白的全表写法。"""

    def __init__(self, slots):
        self.slots = slots
        self.active = {}
        self.done = set()

    def start(self, project_id, cost_ms, now_ms):
        if project_id in self.active or project_id in self.done:
            return False
        if len(self.active) >= self.slots:
            return False
        self.active[project_id] = (now_ms, cost_ms)
        return True

    def advance(self, now_ms):
        for project_id in [p for p, (s, c) in self.active.items()
                           if now_ms - s >= c]:
            del self.active[project_id]
            self.done.add(project_id)
        return len(self.done)

    def running(self):
        return len(self.active)


class DifferentialTest(unittest.TestCase):
    def test_matches_reference_on_random_sequences(self):
        rnd = random.Random(20261001)
        for _ in range(200):
            slots = rnd.randrange(1, 6)
            actual = Research(slots=slots)
            reference = ReferenceResearch(slots)
            now = 0
            pool = ["p-%d" % i for i in range(rnd.randrange(1, 12))]
            for _ in range(rnd.randrange(50, 150)):
                now += rnd.randrange(0, 300)
                pid = rnd.choice(pool)
                if rnd.random() < 0.6:
                    cost = rnd.randrange(1, 5000)
                    got = actual.start(pid, cost, now)
                    want = reference.start(pid, cost, now)
                    self.assertEqual(got, want)
                else:
                    self.assertEqual(actual.advance(now), reference.advance(now))
                self.assertEqual(actual.running(), reference.running())
                self.assertEqual(actual.done, reference.done)


if __name__ == "__main__":
    unittest.main()
