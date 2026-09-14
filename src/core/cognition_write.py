"""
src/core/cognition_write.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD

`EntityUpdate.merge()`'s own `cognition_bundle_set` field (src/core/updates.py) is a whole-object
REPLACE, not a per-subfield merge. Any phase that builds a new `CognitionModel` from an entity's
tick-START snapshot (`entity.cognition`) instead of reading through whatever an earlier phase this
same tick already staged will silently discard that earlier write the moment both phases touch the
same entity in the same tick -- no error, just vanished data (the real bug this ticket investigates;
see staging_artifacts/TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD/investigation.md
for the full writer enumeration and the structural-options evaluation).

`read_through_cognition()` is the single, sanctioned way to obtain the correct base `CognitionModel`
to build a new one on top of. Every real writer (src/domains/memory/phase.py,
src/domains/combat_engagement/phase.py, src/domains/emotion/habit_phase.py,
src/engine/pipeline_phases/hardening.py, src/systems/lifecycle_systems/lifecycle.py,
src/strategy/role_model_phase.py, src/engine/pipeline_phases/movement.py) calls this instead of
reading `entity.cognition` directly, in priority order: this call's own already-staged write, then
progressively earlier same-tick writes, then the tick-start snapshot as the final fallback.

Deliberately takes already-looked-up `Optional[EntityUpdate]` values, not dicts + entity ids: each
caller's own accumulator shape differs (a single flat `dict(update.entity_updates)`, or -- as in
CombatEngagementPhase.apply()'s own per-actor loop -- two separate accumulators, its own local
`entity_updates` plus the incoming `tick_update` from earlier phases). Making the caller do its own
`.get(entity_id)` keeps this helper agnostic to that shape instead of guessing it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.cognition import CognitionModel
    from src.core.updates import EntityUpdate


def read_through_cognition(
    fallback_cognition: "CognitionModel",
    *candidate_updates: Optional["EntityUpdate"],
) -> "CognitionModel":
    """
    Return the first `cognition_bundle_set` found among `candidate_updates`, in the order given
    (most-recent/most-local first), falling back to `fallback_cognition` (normally the entity's
    tick-start `entity.cognition`) if none of them have staged a cognition write yet.
    """
    for candidate in candidate_updates:
        if candidate is not None and candidate.cognition_bundle_set is not None:
            return candidate.cognition_bundle_set
    return fallback_cognition
