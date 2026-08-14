---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality, progression]
---

# TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION

## Title
Build `ProgressionShaper` — XP/level/skill/trait/AP event emission moved to apply-layer push

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 3 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Migrates PROGRESSION's 7
event types from `event_extractor.py`'s diffing (`event_extractor.py:266-282`, `:773-831`) to a
new `ProgressionShaper`, under `FeatureMode.SHADOW`.

**Important correction to this epic's own parent architecture investigation
(`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE`)**: that investigation's coverage audit
characterized "PROGRESSION (quest)" as diff-only and flagged "raw XP/level detection also read as
diff-based on a quick pass, same category as quest" as an unconfirmed hedge. Direct confirmation
this session (`src/core/updates.py:220-243`) found this was **wrong for XP/level/skill/trait/AP**
— `IdentityUpdate` already has exactly the right typed fields:

| Event | `IdentityUpdate` field |
|---|---|
| `xp_granted` | `evolution_points_delta: int` |
| `level_up` | `evolution_level_set: Optional[int]` |
| `skill_unlocked` | `learned_skills: list[str]` (this-tick add list, not full snapshot) |
| `trait_expressed` | `traits_add: list[str]` |
| `pillar_trait_unlocked` | `breakthroughs_add: list[str]` |
| `progression_conversion_applied` | `unspent_ap_delta: int` / `unspent_ap_set: Optional[int]` |

Only `progression_plateau_detected` ("XP unchanged for > 50 ticks", `event_extractor.py:816-831`)
is genuinely cross-tick derived — solvable with shaper-local per-run state (the same
`last_xp_change_tick: Dict[eid, int]` pattern already used elsewhere, e.g.
`EventExtractor._seen_routing_families`), not new instrumentation.

The "quest" part of the original hedge (project/quest *status transition* detection) is genuinely
real but is **not** part of this ticket — confirmed this session that `quest_event`
(quest_started/completed/failed) is emitted by a wholly separate `quest_system` source, not
`event_extractor.py`'s diffing pass at all (see the epic's own Out of Scope).

## Scope
1. **Investigate first**: confirm `IdentityUpdate`'s 6 fields above are populated at the point
   `ApplyPath.apply_generation()` processes `update.entity_updates[eid].identity`, matching exactly
   what `event_extractor.py`'s current diff-based code observes (payload shape: e.g. `xp_granted`'s
   payload is `{"amount": xp_delta}` — confirm `evolution_points_delta` is the same integer value,
   not a pre-clamped or differently-scaled one).
2. Add `ProgressionShaper` to `src/observability/event_shapers.py` implementing all 7 events.
3. Register under `FeatureMode.SHADOW`.
4. Add unit tests per event (fire + non-fire cases), including `progression_plateau_detected`'s
   cross-tick state-tracking behavior explicitly (first plateau tick, reset on new XP, no
   double-fire within one run — mirror `CombatShaper`'s existing dedup-set test patterns).
5. Verify via real kernel run — confirm non-zero `xp_granted`/`level_up` output matches
   `event_type_coverage.md`'s noted 0-calibration-hit baseline is explained (are these genuinely
   rare in short calibration runs, or does SHADOW-mode output reveal they should be firing more
   than the old extractor showed? Investigate and report, don't assume either explanation).
6. Update `docs/parity_ledger/progression.yaml` with a new entry per CLAUDE.md's parity rule.
7. Cross-check `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s own scope (new
   capability-trend/life-arc-coherence scoring rules, `tickets/todos/simq-pillar-lifecycle-depth/`)
   for overlap — that ticket reads existing `ScoringContext` state and is orthogonal to this
   ticket's event-emission relocation, but confirm no double-work before implementing.

## Out of Scope
- `quest_event`/quest-project status transitions — separate `quest_system` source, not this
  ticket's scope (see epic's Out of Scope).
- New PROGRESSION scoring rules — `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s scope,
  not this ticket's.
- Delivering live — SHADOW only, cutover is child 8.

## Acceptance Criteria
- [x] `investigation.md` confirms each of the 6 direct-field events' exact `IdentityUpdate` field
      mapping with file:line citations
- [x] `progression_plateau_detected`'s shaper-local state design documented and tested explicitly
      — including a real gating bug found and fixed (any-update vs identity-update)
- [x] `ProgressionShaper` implements all 7 events, registered in `PHASE2_SHAPER_REGISTRY` under
      the shared `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag (same deviation as Child 2, for the same
      reason)
- [x] Unit tests cover every event's fire condition + non-firing case (18 tests)
- [x] Real kernel run confirms correctly-shaped SHADOW output; the surprising initial 0-hit finding
      (ON mode) was investigated, root-caused (any-update gating bug), and fixed — not assumed
      correct
- [x] `docs/parity_ledger/progression.yaml` updated (`PROG-117`)
- [x] Scoped pytest run passes — 986 passed, 6 skipped, 3 deselected

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (sibling, new scoring rules — cross-check for
  overlap, not blocked by or blocking this ticket)
- TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT (DONE — Phase 1's pilot, the pattern this repeats)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` §1.1, §3.6
- `docs/parity_ledger/progression.yaml`
- `docs/mechanics/attribute_progression_contract.md` (Lifecycle section — confirms
  `IdentityUpdate(evolution_points_delta=...)` is the documented emission mechanism for XP grants)

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION/`
during implementation.

## Related Code Areas
- `src/observability/event_shapers.py`
- `src/observability/event_extractor.py` (lines 266-282, 773-831)
- `src/core/updates.py` (`IdentityUpdate`)

## Assumptions / Open Questions
- Whether `xp_granted`/`level_up`'s currently-0 calibration_hits (per `event_type_coverage.md`) is
  archetype-correct rarity or a latent extractor gap is genuinely open — this ticket's Investigate
  phase should surface real evidence either way, not assume.

## Implementation Notes
- Confirmed 6 of 7 events read `IdentityUpdate` fields directly (`evolution_points_delta`,
  `evolution_level_set`, `learned_skills`, `traits_add`, `breakthroughs_add`, `unspent_ap_delta`),
  including tracing `learned_skills`'s construction site (`src/engine/evolution.py:122-125`) to
  confirm it's a per-tick accumulator, not a full snapshot — its naming (no `_add` suffix, unlike
  `traits_add`/`breakthroughs_add`) didn't make this obvious from the field name alone.
- **Real bug found and fixed via real-kernel verification**: `progression_plateau_detected`
  initially only ran when `EntityUpdate.identity` was non-`None`, narrower than the old
  extractor's `dirty_entity_ids`-gated check (any update this tick, using the entity's always-
  present `IdentityComponent`). A real run showed `event_shapers=0` vs `event_extractor=32` for
  identical 500-tick data — root-caused and fixed by decoupling the plateau check from the
  `id_upd is not None` gate the other 6 events correctly use. Post-fix: exact 32/32 parity.
- **Found and fixed a cross-shaper test-isolation issue**: adding `ProgressionShaper` to
  `PHASE2_SHAPER_REGISTRY` broke Child 2's own registry-level tests (their mock entity updates
  never set `.identity`, defaulting to an auto-`MagicMock` that `ProgressionShaper` then tried to
  read real fields from). Fixed by adding `.identity = None` to `test_event_shapers_strategy.py`'s
  `_entity_update()` helper.
- Resolved the ticket's own open question: `xp_granted`/`level_up`'s 0 calibration_hits baseline
  is consistent across both the old extractor and the new shaper on the same real corpus run
  (neither fired for either), not a latent gap specific to either pipeline — archetype/scenario
  rarity, not an extraction bug.

## Test Summary
- `pytest tests/unit/observability/test_event_shapers_progression.py -q`: 18 passed (new).
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  986 passed, 6 skipped, 3 deselected (was 968/6/3 after Child 2 — +18 matches exactly).
- Real kernel run (`dungeon_crawl_seed42_500t`): `event_extractor=32, event_shapers=32` for
  `progression_plateau_detected` under `ON` mode (exact parity, post-fix); `SHADOW` mode confirmed
  0 delivered.

## Files Changed
- `src/observability/event_shapers.py` — `ProgressionShaper`, registered in
  `PHASE2_SHAPER_REGISTRY["progression"]`.
- `src/engine/kernel.py` — `ProgressionShaper.reset_run_state()` wired into `__init__`.
- `tests/unit/observability/test_event_shapers_progression.py` (new, 18 tests).
- `tests/unit/observability/test_event_shapers_strategy.py` — fixed cross-shaper test isolation
  (`.identity = None` added to the mock helper).
- `docs/parity_ledger/progression.yaml` (`PROG-117`).

## Completion Summary
Built `ProgressionShaper` covering all 7 PROGRESSION events with zero new instrumentation — 6 via
direct `IdentityUpdate` field reads, 1 (`progression_plateau_detected`) via shaper-local cross-tick
state. Getting to a correct implementation required finding and fixing 2 real bugs via real,
non-mocked kernel verification rather than trusting the design on paper: an any-update-vs-identity-
update gating gap (same category of bug as Child 2's `belief_stale` fix, confirming this is a
recurring pattern worth checking explicitly in remaining Phase 2 children), and a cross-shaper
test-isolation issue exposed by having 2 shapers in the same registry for the first time. Also
resolved this ticket's own open question about `xp_granted`/`level_up`'s 0-hit baseline with real
evidence rather than leaving it open. SHADOW-only, as scoped; cutover is a separate, later ticket.
