"""Phase order validation for tools/agent_codex_runtime_shadow/.

Sequencing-only concern, deliberately separate from matrix.py's membership validators (imported
alongside it, never merged into it) — matches the anti-drift hazard against silent partial
validation: an input's phases must be exactly an in-order PREFIX of the supported matrix's phase
list. No reordering, no best-effort partial validation.
"""
from __future__ import annotations

from .errors import PhaseOrderViolationError
from .matrix import SupportedMatrix


def validate_phase_order(phase_names: list[str], matrix: SupportedMatrix) -> None:
    """Raises PhaseOrderViolationError unless `phase_names` is exactly a prefix, in order, of
    `matrix.phases`. E.g. [Scope, Plan, Investigate] and [Investigate, Scope] both reject;
    [Scope, Investigate] — a valid partial-but-in-order prefix — passes."""
    expected_prefix = matrix.phases[: len(phase_names)]
    if phase_names != expected_prefix:
        raise PhaseOrderViolationError(
            f"phase order {phase_names!r} is not an in-order prefix of the supported order "
            f"{matrix.phases!r}"
        )
