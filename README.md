# Persistent Priority Queue

A persistent priority queue implemented in Python using binary heaps and
file-based JSON persistence.

This project was developed as part of the Saralweb Software Development
Engineer (SDE) assignment.

## Features

The implementation supports all required operations:

- `insert`
- `extract_min`
- `extract_max`
- `peek`
- `update`
- `delete`
- `is_empty`

The queue state is persisted to a JSON file, so data remains available after
the application is restarted.

## Implementation

The implementation uses:

- A min-heap for minimum-priority extraction.
- A max-heap for maximum-priority extraction.
- A dictionary as the authoritative item store.
- Version numbers for lazy removal of stale heap entries.
- JSON file storage for persistence.
- Atomic file replacement to reduce the risk of corrupted state.

Each item has:

- A unique ID
- A numeric priority
- An optional value

Example:

```python
from module import PersistentPriorityQueue

queue = PersistentPriorityQueue("queue.json")

queue.insert("task1", 10, "Normal task")
queue.insert("task2", 1, "Urgent task")
queue.insert("task3", 20, "Low priority task")

print(queue.peek())
# ('task2', 1, 'Urgent task')

print(queue.extract_min())
# ('task2', 1, 'Urgent task')

print(queue.extract_max())
# ('task3', 20, 'Low priority task')

queue.update("task1", 2, "Updated task")

queue.delete("task1")

print(queue.is_empty())
