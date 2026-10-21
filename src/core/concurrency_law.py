from __future__ import annotations
from typing import TYPE_CHECKING

from src.core.work import WorkClass

if TYPE_CHECKING:
    from src.core.worker_protocol import WorkerResult

class ConcurrencyLaw:
    """
    Law: Authoritative commit order must be explicit and frozen.
    M8 Law: Explicit mapping for work class priority.
    """
    
    # Priority Mapping (Lower is Earlier)
    # M8 Rule: Explicit, documented, and tested.
    CLASS_PRIORITY = {
        WorkClass.CRITICAL: 0,
        WorkClass.PERIODIC: 10,
        WorkClass.OPPORTUNISTIC: 20,
        WorkClass.DEFERRED: 30
    }
    
    @classmethod
    def get_class_priority(cls, work_class: WorkClass) -> int:
        """Get the authoritative priority for a work class."""
        return cls.CLASS_PRIORITY.get(work_class, 100) # Default to lowest priority

    @staticmethod
    def commit_key(result: "WorkerResult") -> tuple[int, int, int]:
        """The frozen commit key of a worker result: ``class_priority`` ascending (lower is earlier), then ``local_priority`` DESCENDING (higher is earlier), then ``entity_id`` ascending.
        ``Kernel._phase_resolution`` sorts by it. The direction of ``local_priority`` is the code's, ruled by rpg-planner on 2026-10-21 against ``bounded_concurrency_contract.md`` §3's old wording
        (TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH)."""
        return (result.class_priority, -result.local_priority, result.entity_id)
