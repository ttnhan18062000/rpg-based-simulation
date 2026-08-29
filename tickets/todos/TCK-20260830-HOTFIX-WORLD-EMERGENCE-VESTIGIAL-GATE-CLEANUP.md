---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260830-HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP
phase: open
date: 2026-08-30
tags: [feature-flags]
---

# TCK-20260830-HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP

## Title
Remove Vestigial Second Gate in `WorldEmergencePhase.execute()`

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Filed from `TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION`'s investigation. That ticket found
`WorldEmergencePhase.execute()` (`src/domains/world_emergence/phase.py:34-39`) contains a second,
independent gate on top of the real pipeline-level `ENABLE_WORLD_EMERGENCE` feature flag that
decides whether the phase is even invoked (`src/engine/pipeline.py:290`):

```python
flag = getattr(state, "world_emergence_enabled", True)
if hasattr(state, "periodic_due_ticks") and "world_emergence_disabled" in state.periodic_due_ticks:
    flag = False
if not flag:
    return update, WorldEmergenceResult()
```

`AuthoritativeState` does not define a real `world_emergence_enabled` attribute (the `getattr`
always falls back to its `True` default in every real production path), and the
`periodic_due_ticks` branch keys off an undocumented magic string
(`"world_emergence_disabled"`) with no writer anywhere in `src/` — only
`tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py:11` sets it, by
manually constructing `AuthoritativeState(..., periodic_due_ticks={"world_emergence_disabled"})`.
This violates the project's Durable State Rule ("Do not store durable meaning in `reason`
strings, free-form `metadata`, comments, or temporary local variables") — `periodic_due_ticks` is
being used as an undocumented free-form sentinel channel for a second, shadow feature-gate
that duplicates (and could silently diverge from) the real flag.

Currently low-risk (permissive default, no live writer), but a latent footgun: if any future code
ever legitimately populates `periodic_due_ticks` with this string for an unrelated reason, or a
typo'd condition elsewhere matches it, `WorldEmergencePhase` would silently no-op outside the
actual, auditable `ENABLE_WORLD_EMERGENCE` flag control point.

## Scope
- Remove the `world_emergence_enabled`/`periodic_due_ticks["world_emergence_disabled"]` gate from
  `WorldEmergencePhase.execute()`; the pipeline-level `ENABLE_WORLD_EMERGENCE` flag check at the
  call site (`src/engine/pipeline.py:290`) is the sole authoritative gate.
- Update or remove `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py`'s
  test that exercises this vestigial path — confirm what it's actually asserting first; if it has
  independent value testing something else, keep it but stop relying on the removed gate.

## Out of Scope
- `ENABLE_WORLD_EMERGENCE`'s own default (out of scope, tracked separately by the filing ticket).
- Any other `AuthoritativeState`/`periodic_due_ticks` usage outside this one gate.

## Acceptance Criteria
- `WorldEmergencePhase.execute()` no longer reads `world_emergence_enabled` or
  `periodic_due_ticks["world_emergence_disabled"]`.
- All existing `tests/unit/domains/world_emergence/` and
  `tests/integration/domains/world_emergence/` tests still pass (updated as needed for the
  removed gate, not weakened).
- No production code path is affected in practice (the gate was already permissive/dead), so no
  behavior-change divergence entry is expected — confirm this during implementation before
  closing.

## Related Tickets
- TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION (filing ticket, disclosed this finding)

## Related Docs
- CLAUDE.md (Durable State Rule)

## Related Code Areas
- src/domains/world_emergence/phase.py
- tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py

## Assumptions / Open Questions
None yet — to be surfaced during implementation if the test in question has value beyond
exercising the vestigial gate.

## Implementation Notes
(Not yet implemented — filed and deferred, per session's "verify follow-up tickets, then SimQ" sequencing.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
