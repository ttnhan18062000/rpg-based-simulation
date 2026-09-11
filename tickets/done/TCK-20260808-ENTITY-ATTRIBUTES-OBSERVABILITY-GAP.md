---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP
phase: done
date: 2026-08-08
tags: [observability, world]
---

# TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP

## Title
Entity base attribute changes (STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA) have zero observability events

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260808-ENTITY-EVENT-LEDGER`'s cross-reference (`docs/event_ledger/entity.yaml`
`ENTITY-008`) confirmed `AttributeUpdate` (the 9 base stats) has no corresponding observability
event anywhere — confirmed via `grep -n "\.attributes\.\|\.strength\b\|\.agility\b"
event_extractor.py`, zero matches. A raw stat increase or decrease (from training, aging, magical
effects, or any other source) produces no signal at all.

## Scope
1. **Investigate**: find every code path that actually mutates `AttributeUpdate`'s fields (grep
   `attributes_upd\|AttributeUpdate(` across `src/`) to understand what real gameplay events would
   drive this — is this purely a level-up-adjacent mechanic (already partially observed via
   `level_up`), or are there other, currently-invisible sources?
2. **Plan**: design an `attribute_changed` (or similarly-named) event, scoped to real deltas only
   (not zero-delta no-ops).
3. **Implement**: wire the emission, register in `event_type_coverage.md`, update the ledger.

## Out of Scope
- SimQ scorer wiring — separate decision.
- Sibling findings tracked in their own tickets.

## Acceptance Criteria
- [x] investigation.md identifies every real mutation source for `AttributeUpdate` (1 live,
      1 wired-but-no-AI-driver, 2 confirmed dead code)
- [x] New event wired; real `Kernel.tick_once()` verification attempted first (1500 real ticks on
      `sandbox_world`, confirmed the one live producer too rare to hit — no HERO entities, no
      non-hero leveled up in that window) — verified instead via this repo's own precedented
      hand-built-state pattern, matching the sibling vitals ticket's `wound_sustained` approach
- [x] `event_type_coverage.md` and `docs/event_ledger/entity.yaml` updated
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-EVENT-LEDGER (found this gap — DONE)
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP, TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP,
  TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP (sibling findings)

## Related Docs
- `docs/event_ledger/entity.yaml` (`ENTITY-008`)
- `docs/core/update_intents.md` (`AttributeUpdate` definition)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-ENTITY-EVENT-LEDGER/`

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/core/updates.py` (`AttributeUpdate`)

## Assumptions / Open Questions
- Whether attribute changes are currently even a live, exercised mechanic anywhere in the engine
  (vs. a defined-but-unused intent type) — not assumed; Investigate must confirm real mutation
  sources exist before designing an event for them.

## Implementation Notes
- **Subagent spawn cap reached this session** — Investigate/Plan/Implement/Document-Update/
  Parity/Verify performed directly, not via `Agent(subagent_type=...)` calls.
- **Mutation-source verification, not assumed from grep**: 4 `AttributeUpdate(` call sites found.
  Verified each for real reachability, matching this session's established discipline (a prior
  ticket found `WorldProceduralGenerator` and `PerfRegressionGate` both looked real from a single
  grep hit but were dead/unwired). Result: `src/engine/evolution.py`'s non-hero level-up path is
  LIVE (pipeline-wired via `pipeline.py`). `src/engine/domain/core_actions.py::execute_allocate_ap`
  is real, tested, action-router-wired — but has no live AI driver: the one real gap-resolution
  pipeline that could trigger it (`progression/gaps.py`'s `level_gap` →
  `progression/generator.py` → `progression/resolver.py`) resolves through a separate, cosmetic
  path that only decrements `unspent_ap` and never touches `AttributeUpdate`.
  `src/domains/demographics/cohort.py::compute_elder_attribute_update` and
  `src/actions/attributes.py::AllocateAttributeAction` are confirmed DEAD CODE — zero callers
  anywhere in `src/`, only referenced by their own unit tests.
- **Tangential finding, disclosed not fixed**: `cohort.py`'s own docstring claims attributes stay
  "within the 1–99 mechanic range enforced by the apply pipeline." The real apply site
  (`src/engine/patches.py:557-570`, `AttributePatch.apply`) clamps only an upper bound (`min(100,
  ...)`) — no lower-bound floor exists. Currently unreachable in practice since the only
  negative-delta producer is dead code; not fixed here (apply-pipeline correctness question, out
  of scope for an observability ticket).
- One new event, `attribute_changed`, added to `event_extractor.py`'s diff loop (same vitals
  block, same `_is_real_number` guard pattern as the sibling vitals ticket). Fires on any real
  delta across the 9 base attributes; payload carries only changed fields. Severity is
  direction-based (WARNING on any decline, INFO otherwise) — no existing numeric "significant
  attribute change" threshold exists anywhere in the repo to reuse (unlike
  `exhaustion_threshold`/`WoundState.severity` in the sibling ticket).
- **Real-verification attempted, confirmed unreachable within budget**: tried a real
  `Kernel.tick_once()` loop first (1500 ticks, `sandbox_world`, seed 42) — confirmed the world has
  zero HERO-role entities (8 WORKER/3 GUARD/7 CITIZEN, all `evolution_level == 1`) and none
  leveled up in that window. Non-hero leveling is real and pipeline-wired but too rare to hit in
  a unit-test budget. Fell back to this repo's own precedented hand-built-state pattern (real
  `AttributeComponent` objects, diffed through the real `EventExtractor.extract()` function
  directly) — same fallback class as `wound_sustained` in the sibling ticket.
- **Parity**: same 3 pre-existing P0 hits from `find_p0_intersection()` (COMB-295, TOWN-190,
  INFRA-326) re-confirmed unrelated (push-shaper cutover, different code region). Added `SUB-376`
  to `docs/parity_ledger/substrate.yaml` (same domain as SUB-375, entity-core state). Cross-
  reference gate PASS.

## Test Summary
- `tests/unit/observability/test_event_extractor_attributes.py` (new, 6/6 pass):
  `test_attribute_changed_fires_on_real_delta`,
  `test_attribute_changed_severity_negative_delta_is_warning`,
  `test_attribute_changed_severity_positive_only_is_info`,
  `test_attribute_changed_payload_only_includes_changed_fields`,
  `test_attribute_changed_suppressed_in_light_and_long_run_modes`, `test_no_event_on_zero_delta`.
- `tests/unit/observability/` full suite: 964 passed, 6 skipped, 0 failed (958 + 6 new, zero
  regressions).

## Files Changed
- `src/observability/event_extractor.py` — 1 new event emission block (`attribute_changed`)
- `tests/unit/observability/test_event_extractor_attributes.py` — new, 6 tests
- `docs/simulation_quality/event_type_coverage.md` — §5 new row, Summary counts (18→19)
- `docs/event_ledger/entity.yaml` — `ENTITY-008` flipped `silent`→`observed`
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-376`

## Completion Summary
Base attribute changes (STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA) went from zero observability
coverage to full-coverage, severity-tagged `attribute_changed` event emission. Investigation
found only 1 of 4 grep-hit `AttributeUpdate` producers is genuinely live (non-hero level-up);
1 more is real/tested/wired but has no live AI driver; 2 are confirmed dead code — each verified,
not assumed. A tangential apply-pipeline floor-clamp gap was found and disclosed, not fixed
(out of scope). Real-kernel verification was attempted first and confirmed unreachable within a
1500-tick budget, so verification fell back to this repo's own precedented hand-built-state
pattern. Classified `unscored_intentional`. Parity ledger updated with 1 new entry (`SUB-376`);
the same 3 pre-existing P0 entries flagged by the file-level scan were re-confirmed unrelated.
