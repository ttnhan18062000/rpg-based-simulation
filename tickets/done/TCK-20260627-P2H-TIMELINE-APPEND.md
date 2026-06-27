---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2H-TIMELINE-APPEND
phase: done
date: 2026-06-27
tags: [p2, timeline, event-emission, kernel, coupling, refactor]
---

# TCK-20260627-P2H-TIMELINE-APPEND

## Title
Move `entity.timeline.append()` at `kernel.py:804` into event emission layer

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P2

## Request Summary
`src/engine/kernel.py:804` contains a single direct `entity.timeline.append(event)` mutation outside the authoritative pipeline. This is a minor coupling violation; if timeline management grows, this becomes a maintenance risk. Source: D12 F5, Priority 6/15.

## Scope
- Move `entity.timeline.append(event)` at `kernel.py:804` into the event emission layer (e.g., through `ReplayManager.emit()` or an `EntityTimelineService`).
- The existing cooperation domain contract (`TCK-20260613-DOC-DOMAIN-CONTRACTS`) documented the `cooperation timeline.append()` pattern — this should be consistent with that.

## Out of Scope
- Other places where timeline is appended (check if any exist in domain code, out of scope here).
- Changing what event is appended.

## Acceptance Criteria
- [ ] `kernel.py:804` no longer contains `entity.timeline.append()` directly.
- [ ] The append goes through `ReplayManager.emit()`, `EntityTimelineService`, or an equivalent event emission path.
- [ ] All existing kernel and timeline tests pass.

## Related Tickets
- TCK-20260627-P2G-KERNEL-FACADE (complementary coupling cleanup — can be done in same sprint)

## Related Docs
- `docs/audits/D12_pattern_consistency.md` F5
- Domain contract docs in `docs/simulation/domains/` for the timeline pattern

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-DOMAIN-CONTRACTS/` — documented cooperation timeline.append() pattern

## Related Code Areas
- `src/engine/kernel.py:804` (primary change)
- `src/engine/replay.py` (or wherever `ReplayManager` lives — event emission path)

## Assumptions / Open Questions
- `ReplayManager.emit()` is the appropriate routing path — verify it handles timeline events.
- If `EntityTimelineService` doesn't exist, prefer extending `ReplayManager` rather than creating a new service.

## Implementation Notes
- Line 815 (shifted from original 804) contained the direct `entity.timeline.append(event)` inside a backwards-compat fallback block.
- Added `EntityTimelineStore.record_to_entity(event, entity)` in `src/observability/entity_timeline.py` — this is the authorised routing point for the legacy entity.timeline compatibility path.
- Replaced the direct `entity.timeline.append(event)` call in `kernel.py` with `self._entity_timeline_store.record_to_entity(event, entity)`. The `hasattr` guard is now inside the new method rather than at the call site.
- No change to what event is appended or when. Backward compatibility preserved.

## Test Summary
- Regression: `pytest tests/ -k "kernel or timeline" -m "not slow"`.
- Verify: `grep -n "timeline.append" src/engine/kernel.py` returns no results.

## Files Changed
- `src/engine/kernel.py` — replaced direct `entity.timeline.append(event)` with `self._entity_timeline_store.record_to_entity(event, entity)`
- `src/observability/entity_timeline.py` — added `EntityTimelineStore.record_to_entity(event, entity)` method
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-224

## Completion Summary
Added `EntityTimelineStore.record_to_entity(event, entity)` as the authorised emission point for the legacy `entity.timeline` compatibility path, and replaced the direct `entity.timeline.append(event)` call in `kernel.py` lines 811-815 with a call through that method. The `hasattr` guard is now encapsulated inside `record_to_entity`. 180 kernel and timeline tests pass. Parity ledger entry INFRA-224 added (status: verified, P2).
