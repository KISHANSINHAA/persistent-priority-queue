import tempfile
import unittest
from pathlib import Path

from module import PersistentPriorityQueue


class TestPersistentPriorityQueue(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "queue.json"
        self.queue = PersistentPriorityQueue(self.storage)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_insert_and_peek(self):
        self.queue.insert("task1", 10, "Low priority task")
        self.queue.insert("task2", 1, "Urgent task")
        self.queue.insert("task3", 5, "Normal task")

        self.assertEqual(
            self.queue.peek(),
            ("task2", 1, "Urgent task"),
        )

    def test_extract_min(self):
        self.queue.insert("a", 30)
        self.queue.insert("b", 10)
        self.queue.insert("c", 20)

        self.assertEqual(
            self.queue.extract_min(),
            ("b", 10, None),
        )

        self.assertEqual(len(self.queue), 2)

    def test_extract_max(self):
        self.queue.insert("a", 30)
        self.queue.insert("b", 10)
        self.queue.insert("c", 20)

        self.assertEqual(
            self.queue.extract_max(),
            ("a", 30, None),
        )

        self.assertEqual(len(self.queue), 2)

    def test_update(self):
        self.queue.insert("task1", 10, "Task")

        self.queue.update(
            "task1",
            2,
            "Updated task",
        )

        self.assertEqual(
            self.queue.peek(),
            ("task1", 2, "Updated task"),
        )

    def test_delete(self):
        self.queue.insert("task1", 10)
        self.queue.insert("task2", 20)

        self.queue.delete("task1")

        self.assertEqual(len(self.queue), 1)
        self.assertEqual(
            self.queue.peek(),
            ("task2", 20, None),
        )

    def test_is_empty(self):
        self.assertTrue(self.queue.is_empty())

        self.queue.insert("task1", 1)

        self.assertFalse(self.queue.is_empty())

        self.queue.delete("task1")

        self.assertTrue(self.queue.is_empty())

    def test_persistence(self):
        self.queue.insert("task1", 10, "Persistent task")
        self.queue.insert("task2", 5, "Urgent task")

        # Create a new queue using the same storage file.
        restored_queue = PersistentPriorityQueue(self.storage)

        self.assertEqual(len(restored_queue), 2)

        self.assertEqual(
            restored_queue.peek(),
            ("task2", 5, "Urgent task"),
        )

    def test_update_persists(self):
        self.queue.insert("task1", 10, "Original")

        self.queue.update(
            "task1",
            1,
            "Updated",
        )

        restored_queue = PersistentPriorityQueue(self.storage)

        self.assertEqual(
            restored_queue.peek(),
            ("task1", 1, "Updated"),
        )

    def test_delete_missing_item(self):
        with self.assertRaises(KeyError):
            self.queue.delete("missing")

    def test_update_missing_item(self):
        with self.assertRaises(KeyError):
            self.queue.update("missing", 10)

    def test_duplicate_insert(self):
        self.queue.insert("task1", 10)

        with self.assertRaises(ValueError):
            self.queue.insert("task1", 20)

    def test_extract_empty_queue(self):
        with self.assertRaises(IndexError):
            self.queue.extract_min()

        with self.assertRaises(IndexError):
            self.queue.extract_max()

    def test_negative_priorities(self):
        self.queue.insert("a", -10)
        self.queue.insert("b", 5)
        self.queue.insert("c", -20)

        self.assertEqual(
            self.queue.extract_min(),
            ("c", -20, None),
        )

        self.assertEqual(
            self.queue.extract_max(),
            ("b", 5, None),
        )


if __name__ == "__main__":
    unittest.main()
