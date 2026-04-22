from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict
from src_v2.core.enums import ReasonCode

@dataclass(frozen=True, slots=True)
class ActionReason:
    """Structured reason for an action proposal or intent update."""
    code: ReasonCode
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_rejection: bool = False
    
    def __str__(self) -> str:
        base = self.code.value.replace("_", " ").title()
        if self.is_rejection:
            return f"REJECTED: {base}"
        return base

    def __repr__(self) -> str:
        return f"Reason({self.code.value}, {self.metadata})"
