from __future__ import annotations
from src.core.work import WorkClass

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
