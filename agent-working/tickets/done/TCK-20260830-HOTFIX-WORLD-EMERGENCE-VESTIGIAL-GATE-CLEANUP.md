---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260830-HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP
phase: done
date: 2026-08-30
tags: [feature-flags]
---

# TCK-20260830-HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP

## Title
Remove Vestigial Second Gate in `WorldEmergencePhase.execute()`

## Status
DONE

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
- [x] `WorldEmergencePhase.execute()` no longer reads `world_emergence_enabled` or
  `periodic_due_ticks["world_emergence_disabled"]`.
- [x] All existing `tests/unit/domains/world_emergence/` and
  `tests/integration/domains/world_emergence/` tests still pass (updated as needed for the
  removed gate, not weakened).
- [x] No production code path is affected in practice (the gate was already permissive/dead), so no
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
Removed the vestigial second gate from `WorldEmergencePhase.execute()`
(`src/domains/world_emergence/phase.py`): the `flag = getattr(state, "world_emergence_enabled",
True)` / `periodic_due_ticks["world_emergence_disabled"]` block and its `if not flag: return
update, WorldEmergenceResult()` early-return were deleted outright, leaving `execute()` starting
directly at `t_start = time.perf_counter_ns()`. No replacement gate was added — the sole
authoritative gate remains the `ENABLE_WORLD_EMERGENCE` flag check at the `run_phase(...)` call
site in `src/engine/pipeline.py:311`, which is unmodified and untouched by this ticket.

Verification performed before removal (per AC): grepped `world_emergence_enabled` and
`world_emergence_disabled` across `src/` and `tests/` — the only occurrences anywhere in the repo
were the vestigial block itself (`phase.py`) and the one test that manually constructed the
sentinel (`test_phase8_world_emergence_phase.py:11`). No other `src/` code path ever sets
`state.world_emergence_enabled` or writes `"world_emergence_disabled"` into
`periodic_due_ticks`, so `getattr(..., True)` always resolved to `True` in every real production
path and the `periodic_due_ticks` branch was dead code outside that one test. Confirmed the gate
was fully dead/permissive — assumption held, no STOP condition triggered.

Test disposition: `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py`
had two tests. `test_phase_respects_feature_flag` (the one named in Related Code Areas) existed
solely to prove the vestigial gate no-ops the phase — its only assertion
(`len(result.pressures) == 0`) was incidental (empty `entities`/default `regions` would also
yield zero pressures with no gate at all), and it added no coverage beyond the removed gate
itself, so it was removed rather than rewritten (no independent value to preserve).
`test_phase_outputs_world_signals_not_direct_entity_action` (the other test in that file) does not
reference the gate and was left untouched.

Grepped the full `tests/unit/domains/world_emergence/` and
`tests/integration/domains/world_emergence/` trees plus a repo-wide grep for
`world_emergence_enabled` / `world_emergence_disabled` / `periodic_due_ticks` in that directory —
no other test depends on this gate.

## Test Summary
Ran with the project venv (`.venv/bin/python3`, required — bare `python3` lacks `pydantic` and
fails at `tests/conftest.py` import):
- `tests/unit/domains/world_emergence/` + `tests/integration/domains/world_emergence/` — 35
  passed (was 36 before the one vestigial test was removed).
- `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/integration/domains/test_fused_loop.py`,
  `tests/integration/perf/test_phase10_graceful_degradation.py`,
  `tests/architecture/test_world_capability_layer_flag_inert.py` (all tests referencing
  `ENABLE_WORLD_EMERGENCE`) — 62 passed. Confirms the real pipeline-level flag gate is unaffected.

## Files Changed
- `src/domains/world_emergence/phase.py` — removed the vestigial `world_emergence_enabled` /
  `periodic_due_ticks["world_emergence_disabled"]` gate from `WorldEmergencePhase.execute()`.
- `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py` — removed
  `test_phase_respects_feature_flag`, the sole test whose entire premise was the removed gate.
- `docs/parity_ledger/world_dynamics.yaml` — added entry `WORLD-117` documenting that
  `WorldEmergencePhase.execute()` (Phase 8) is now gated solely by the `ENABLE_WORLD_EMERGENCE`
  flag at its `pipeline.py:311` call site, and recording that the removed internal gate never
  diverged from the real flag in production.
- `tickets/inprogress/TCK-20260830-HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP.md` — this file
  (Status, Implementation Notes, Test Summary, Files Changed, Completion Summary, AC checkboxes).

## Completion Summary
Removed the dead second feature-gate (`world_emergence_enabled` getattr fallback plus the
`periodic_due_ticks["world_emergence_disabled"]` magic-string sentinel) from
`WorldEmergencePhase.execute()`, leaving `ENABLE_WORLD_EMERGENCE` at the `pipeline.py:311`
`run_phase(...)` call site as the sole authoritative gate for Phase 8. Verified no `src/` code
path ever set the removed attribute or sentinel in production, so the removal has no live
production behavior effect. Removed the one integration test whose only purpose was exercising
the vestigial gate; the other test in that file and all `ENABLE_WORLD_EMERGENCE`-referencing tests
elsewhere in the repo (97 tests total across both scoped runs) pass unchanged.
