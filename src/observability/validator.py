"""
src/observability/validator.py
───────────────────────────────────────────────────────────────────────────────
DecisionTraceValidator for Phase 17.
"""

from __future__ import annotations
import logging
from src.observability.trace import DecisionTrace

logger = logging.getLogger(__name__)

class DecisionTraceValidator:
    """Validates the structural completeness of emitted DecisionTraces."""

    @staticmethod
    def validate(trace: DecisionTrace, mode: str = "STRICT") -> bool:
        if mode == "OFF":
            return True
            
        errors = []
        if not trace.decision_id:
            errors.append("missing_decision_id")
        if trace.selected_option is None and not trace.reason:
            errors.append("missing_selection_and_reason")
        if not trace.considered_options:
            errors.append("missing_considered_options")
            
        # Validate that selected option is in considered list
        if trace.selected_option:
            considered_names = {opt.name for opt in trace.considered_options}
            if trace.selected_option not in considered_names:
                errors.append("selected_option_not_in_considered_options")

        if errors:
            msg = f"DecisionTrace validation failed: {', '.join(errors)}"
            if mode == "STRICT":
                logger.error(msg)
                return False
            elif mode == "WARN":
                logger.warning(msg)
                
        return True
