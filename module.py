"""Persistent priority queue with min/max extraction."""

from __future__ import annotations

import heapq
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class PersistentPriorityQueue:
    """Priority queue persisted to a JSON file.

    Each item has a unique string ID, numeric priority, and optional value.
    Two binary heaps provide efficient min/max access. A dictionary is the
    authoritative store, while heap entries use versions for lazy deletion.
    """

    def __init__(
        self,
        storage_path: str | os.PathLike[str] = "priority_queue.json",
    ) -> None:
        self.storage_path = Path(storage_path)
        self._items: dict[str, dict[str, Any]] = {}
        self._min_heap: list[tuple[float, int, str, int]] = []
        self._max_heap: list[tuple[float, int, str, int]] = []
        self._sequence = 0
        self._load()

    def insert(
        self,
        item_id: str,
        priority: float,
        value: Any = None,
    ) -> None:
        """Insert a new item."""
        self._validate_id(item_id)
        self._validate_priority(priority)

        if item_id in self._items:
            raise ValueError(f"Item '{item_id}' already exists")

        priority = self._normalize_priority(priority)
        version = 1
        sequence = self._sequence

        self._items[item_id] = {
            "priority": priority,
            "value": value,
            "version": version,
            "sequence": sequence,
        }

        self._push(item_id, priority, version, sequence)
        self._sequence += 1
        self._persist()

    def extract_min(self) -> tuple[str, float, Any]:
        """Remove and return the item with minimum priority."""
        item_id = self._peek_valid(self._min_heap)
        result = self._result(item_id)

        del self._items[item_id]
        heapq.heappop(self._min_heap)
        self._persist()

        return result

    def extract_max(self) -> tuple[str, float, Any]:
        """Remove and return the item with maximum priority."""
        item_id = self._peek_valid(self._max_heap)
        result = self._result(item_id)

        del self._items[item_id]
        heapq.heappop(self._max_heap)
        self._persist()

        return result

    def peek(self) -> tuple[str, float, Any]:
        """Return the minimum-priority item without removing it."""
        return self._result(self._peek_valid(self._min_heap))

    def update(
        self,
        item_id: str,
        priority: float,
        value: Any = None,
    ) -> None:
        """Update an existing item's priority and value."""
        self._validate_id(item_id)
        self._validate_priority(priority)

        if item_id not in self._items:
            raise KeyError(f"Item '{item_id}' does not exist")

        priority = self._normalize_priority(priority)
        version = self._items[item_id]["version"] + 1
        sequence = self._sequence

        self._items[item_id] = {
            "priority": priority,
            "value": value,
            "version": version,
            "sequence": sequence,
        }

        self._push(item_id, priority, version, sequence)
        self._sequence += 1
        self._persist()

    def delete(self, item_id: str) -> None:
        """Delete an item by ID."""
        self._validate_id(item_id)

        if item_id not in self._items:
            raise KeyError(f"Item '{item_id}' does not exist")

        del self._items[item_id]
        self._persist()

    def is_empty(self) -> bool:
        """Return True when the queue contains no active items."""
        return not self._items

    def __len__(self) -> int:
        return len(self._items)

    def _push(
        self,
        item_id: str,
        priority: float,
        version: int,
        sequence: int,
    ) -> None:
        heapq.heappush(
            self._min_heap,
            (priority, sequence, item_id, version),
        )

        heapq.heappush(
            self._max_heap,
            (-priority, sequence, item_id, version),
        )

    def _peek_valid(
        self,
        heap: list[tuple[float, int, str, int]],
    ) -> str:
        while heap:
            _, _, item_id, version = heap[0]

            item = self._items.get(item_id)

            if item is not None and item["version"] == version:
                return item_id

            heapq.heappop(heap)

        raise IndexError("Priority queue is empty")

    def _result(self, item_id: str) -> tuple[str, float, Any]:
        item = self._items[item_id]

        return (
            item_id,
            item["priority"],
            item["value"],
        )

    @staticmethod
    def _validate_id(item_id: str) -> None:
        if not isinstance(item_id, str):
            raise TypeError("item_id must be a string")

        if not item_id:
            raise ValueError("item_id cannot be empty")

    @staticmethod
    def _validate_priority(priority: float) -> None:
        if isinstance(priority, bool):
            raise ValueError("priority must be an int or float")

        if not isinstance(priority, (int, float)):
            raise ValueError("priority must be an int or float")

    @staticmethod
    def _normalize_priority(priority: float) -> float | int:
        if isinstance(priority, float) and priority.is_integer():
            return int(priority)

        return priority

    def _load(self) -> None:
        """Load queue state from disk."""
        if not self.storage_path.exists():
            return

        try:
            with self.storage_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Unable to load queue state: {exc}"
            ) from exc

        self._items = data.get("items", {})
        self._sequence = int(data.get("sequence", 0))

        for item_id, item in self._items.items():
            self._push(
                item_id,
                item["priority"],
                item["version"],
                item["sequence"],
            )

    def _persist(self) -> None:
        """Persist queue state atomically."""
        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "sequence": self._sequence,
            "items": self._items,
        }

        fd, temporary_path = tempfile.mkstemp(
            prefix=f".{self.storage_path.name}.",
            suffix=".tmp",
            dir=self.storage_path.parent,
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    payload,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

                file.flush()
                os.fsync(file.fileno())

            os.replace(
                temporary_path,
                self.storage_path,
            )

        except Exception:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass

            raise


# Optional shorter alias.
PriorityQueue = PersistentPriorityQueue
