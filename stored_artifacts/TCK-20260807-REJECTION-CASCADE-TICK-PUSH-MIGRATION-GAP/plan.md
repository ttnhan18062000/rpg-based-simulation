---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# Plan: TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP

Implemented as one combined change with the sibling ticket (`TCK-20260807-COMMITMENT-ABANDONED-
PUSH-MIGRATION-GAP`).

## Steps

1. `src/observability/event_shapers.py`:
   - Import `ProjectStatus` (`src.core.strategic`), `AbandonmentEvaluator`/`AbandonmentCategory`
     (`src.domains.commitment.abandonment`), `_MAX_CONSECUTIVE_REJECTIONS`
     (`src.systems.strategic_systems.intelligence`).
   - Add `AgencyShaper` class with `.shape()` covering both `commitment_abandoned` (via
     `_current_projects()` reuse) and `rejection_cascade_tick` (pure `update`-derived aggregate,
     byte-identical logic to `event_extractor.py`'s own version).
   - Add `AGENCY_SHAPER_REGISTRY = {"agency": [AgencyShaper()]}`.
   - Add an Agency-mode gating block inside `run_shadow_shapers()`, mirroring the Quest block's
     structure exactly (own `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag).
2. `src/observability/event_extractor.py`:
   - Add `_push_shapers_agency_active` flag read.
   - Gate the `commitment_abandoned` branch and the `rejection_cascade_tick` block (both) behind
     `not _push_shapers_agency_active`.
3. `src/domains/optimization/feature_flags.py`: add `ENABLE_PUSH_EVENT_SHAPERS_AGENCY`, default
   `ON`.
4. Tests: new `tests/unit/observability/test_event_shapers_agency.py` — registry wiring, 4-way
   flag gating, independence from `ENABLE_PUSH_EVENT_SHAPERS_QUEST`, direct `AgencyShaper.shape()`
   behavior for both events (16 tests total). `tests/unit/config/test_phase10_feature_flags.py`:
   add the new flag to `_DELIBERATE_ON_DEFAULT_FLAGS`.
5. Real-kernel-adjacent verification for both events independently (confirmed the initial
   `rejection_cascade_tick` verification attempt undercounted — 10 rejections, below the real
   `_MAX_CONSECUTIVE_REJECTIONS=20` threshold — corrected and re-verified with 25).
6. Docs: `docs/parity_ledger/infrastructure.yaml` (new `INFRA-327`, covering both events);
   `docs/guides/feature_flags.md` (new flag row, 15→16 count updates throughout).
7. Run scoped tests, doc-staleness check, parity cross-reference, Verify static precheck,
   Finalize (both tickets).

## Acceptance criteria map

| Original AC | Disposition |
|---|---|
| investigation.md confirms aggregate logic + chosen shaper placement | Done — grouped with commitment_abandoned into one AgencyShaper, own flag |
| Shaper implemented, event_extractor.py's block gated | Done |
| Real-kernel-adjacent verification: no double-fire | Done — corrected an initial under-threshold test mistake before landing |
| Relevant parity ledger entry updated | Done — INFRA-327 (shared) |
| Scoped pytest passes | Done |
