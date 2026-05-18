from __future__ import annotations

from enum import IntEnum, auto
from collections import deque
from typing import Generic, TypeVar, List, Optional, Sequence


T = TypeVar("T")


class OverflowPolicy(IntEnum):
    """
    Explicit policies for handling long-lived collection growth.
    """
    REJECT = auto()         # Fail/Raise error when full
    EVICT_OLDEST = auto()   # Ring-buffer behavior (drop head)
    TRUNCATE_NEWEST = auto()# Drop incoming item
    COMPACT = auto()        # Summarize (caller defined)


class RetentionError(Exception):
    """Raised when a REJECT policy is violated."""
    pass


class BoundedBuffer(Generic[T]):
    """
    A generic bounded container for long-lived runtime data.
    Enforces a hard capacity and explicit overflow policy.
    """

    def __init__(
        self, 
        capacity: int, 
        policy: OverflowPolicy = OverflowPolicy.REJECT
    ):
        if capacity <= 0:
            raise ValueError("Capacity must be positive.")
        
        self._capacity = capacity
        self._policy = policy
        self._items: deque[T] = deque()

    def append(self, item: T) -> bool:
        """
        Add an item to the buffer.
        Returns: True if item was kept, False if dropped/truncated.
        Raises: RetentionError if policy is REJECT and buffer is full.
        """
        if len(self._items) >= self._capacity:
            if self._policy == OverflowPolicy.REJECT:
                raise RetentionError(f"Buffer full (capacity {self._capacity})")
            
            if self._policy == OverflowPolicy.TRUNCATE_NEWEST:
                return False
            
            if self._policy == OverflowPolicy.EVICT_OLDEST:
                self._items.popleft()
                # Continue to append below
            
            if self._policy == OverflowPolicy.COMPACT:
                # COMPACT must be handled by the owner or a subclass.
                # For basic BoundedBuffer, we treat it as REJECT if not overridden.
                raise NotImplementedError("COMPACT policy requires subclass implementation.")

        self._items.append(item)
        return True

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def policy(self) -> OverflowPolicy:
        return self._policy

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        return self._items[index]

    def to_list(self) -> List[T]:
        """Convert to a standard list for non-authoritative consumption."""
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
