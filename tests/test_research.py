import random
import unittest

from research.core import Research


class SlotsTest(unittest.TestCase):
    def test_start_over_capacity_returns_false(self):
        book = Research(slots=2)
        self.assertTrue(book.start("r-1", 5000, 0))
        self.assertTrue(book.start("r-2", 5000, 0))
        self.assertFalse(book.start("r-3", 5000, 0))
        self.assertEqual(book.running(), 2)

    def test_freed_slot_can_be_used(self):
        book = Research(slots=1)
        self.assertTrue(book.start("r-1", 5000, 0))
        self.assertFalse(book.start("r-2", 5000, 1000))
        book.advance(5000)
        self.assertEqual(book.running(), 0)
        self.assertTrue(book.start("r-2", 5000, 5000))
        self.assertEqual(book.running(), 1)

    def test_running_never_exceeds_slots_throughout(self):
        book = Research(slots=3)
        for i in range(20):
            book.start("r-%d" % i, 3000, 0)
            self.assertLessEqual(book.running(), 3)
        self.assertEqual(book.running(), 3)


class RealTimeCompletionTest(unittest.TestCase):
    def test_completes_by_elapsed_time_not_call_count(self):
        book = Research(slots=2)
        book.start("r-1", 5000, 0)
        self.assertEqual(book.advance(1000), 0)
        self.assertEqual(book.advance(6000), 1)
        self.assertIn("r-1", book.done)
        self.assertEqual(book.running(), 0)

    def test_exact_boundary_completes(self):
        book = Research(slots=2)
        book.start("r-1", 5000, 1000)
        self.assertEqual(book.advance(5999), 0)
        self.assertEqual(book.advance(6000), 1)

    def test_extra_advance_calls_do_not_hurry_completion(self):
        book = Research(slots=2)
        book.start("r-1", 10000, 0)
        for now in (1, 2, 3, 4, 5):
            self.assertEqual(book.advance(now), 0)
        self.assertEqual(book.running(), 1)
        self.assertEqual(book.advance(10000), 1)

    def test_done_set_only_grows(self):
        book = Research(slots=2)
        book.start("r-1", 1000, 0)
        book.start("r-2", 2000, 0)
        book.advance(1500)
        done_before = set(book.done)
        book.advance(900)
        self.assertTrue(done_before.issubset(book.done))
        book.advance(3000)
        self.assertEqual(book.done, {"r-1", "r-2"})


class IdempotentStartTest(unittest.TestCase):
    def test_duplicate_submit_returns_false(self):
        book = Research(slots=2)
        self.assertTrue(book.start("r-1", 5000, 0))
        self.assertFalse(book.start("r-1", 5000, 10))
        self.assertEqual(book.running(), 1)

    def test_duplicate_does_not_reset_start_time(self):
        book = Research(slots=2)
        book.start("r-1", 5000, 0)
        book.start("r-1", 5000, 4000)
        self.assertEqual(book.advance(5000), 1)

    def test_duplicate_after_completion_stays_done(self):
        book = Research(slots=2)
        book.start("r-1", 1000, 0)
        book.advance(1000)
        self.assertFalse(book.start("r-1", 1000, 2000))
        self.assertEqual(book.running(), 0)
        self.assertEqual(book.done, {"r-1"})


class QueryCostTest(unittest.TestCase):
    def test_running_query_is_constant_scan_cost(self):
        book = Research(slots=100000)
        for i in range(3000):
            book.start("r-%d" % i, 5000, 0)
        before = book.scanned_count()
        for _ in range(3000):
            book.running()
        self.assertEqual(book.scanned_count() - before, 3000)

    def test_scan_cost_does_not_grow_with_active_count(self):
        measured = {}
        for active in (1, 10, 100, 1000):
            book = Research(slots=100000)
            for i in range(active):
                book.start("r-%d" % i, 5000, 0)
            before = book.scanned_count()
            for _ in range(100):
                book.running()
            measured[active] = book.scanned_count() - before
        self.assertEqual(set(measured.values()), {100})

    def test_large_scale_amortized_constant(self):
        book = Research(slots=200000)
        for i in range(200000):
            self.assertTrue(book.start("r-%d" % i, 1000000, 0))
        before = book.scanned_count()
        for _ in range(100000):
            self.assertEqual(book.running(), 200000)
        self.assertEqual(book.scanned_count() - before, 100000)


class DeterminismTest(unittest.TestCase):
    def test_same_sequence_same_results(self):
        def run():
            book = Research(slots=2)
            trace = []
            trace.append(book.start("r-1", 5000, 0))
            trace.append(book.start("r-1", 5000, 1))
            trace.append(book.start("r-2", 1000, 0))
            trace.append(book.start("r-3", 1000, 0))
            trace.append(book.advance(1000))
            trace.append(book.running())
            trace.append(book.start("r-3", 1000, 1000))
            trace.append(book.advance(6000))
            trace.append(book.running())
            return trace, set(book.done)

        first_trace, first_done = run()
        second_trace, second_done = run()
        self.assertEqual(first_trace, second_trace)
        self.assertEqual(first_done, second_done)


class ReferenceBook:
    """参考实现：并行位 + 按真实时间完成 + 幂等提交。"""

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
        for project_id, (start_ms, cost_ms) in list(self.active.items()):
            if now_ms - start_ms >= cost_ms:
                del self.active[project_id]
                self.done.add(project_id)
        return len(self.done)

    def running(self):
        return len(self.active)


class ReferenceEquivalenceTest(unittest.TestCase):
    def test_random_sequences_match_reference(self):
        rng = random.Random(226)
        for _ in range(200):
            slots = rng.randint(1, 5)
            actual = Research(slots=slots)
            reference = ReferenceBook(slots)
            now = 0
            pool = ["p-%d" % i for i in range(rng.randint(1, 12))]
            for _ in range(rng.randint(1, 60)):
                if rng.random() < 0.6:
                    project_id = rng.choice(pool)
                    cost_ms = rng.randint(1, 10)
                    now = rng.randint(now, now + 3)
                    self.assertEqual(
                        actual.start(project_id, cost_ms, now),
                        reference.start(project_id, cost_ms, now),
                    )
                else:
                    now = rng.randint(now, now + 5)
                    self.assertEqual(actual.advance(now), reference.advance(now))
                self.assertEqual(actual.running(), reference.running())
                self.assertLessEqual(actual.running(), slots)
                self.assertEqual(actual.done, reference.done)


if __name__ == "__main__":
    unittest.main()
