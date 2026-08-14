# Implementation Sequence — simq-observability-push-migration-phase2

Epic: `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Continues
`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC` (Phase 1, DONE — COMBAT/ECONOMY/FACTION)
by migrating everything else `event_extractor.py` still constructs via post-tick diffing, plus a
standing performance regression gate. **Strict sequential order for the build → validate → cutover
skeleton (1 → 7 → 8); children 2-6 are independent of each other and may be reordered or
parallelized relative to one another, but all must land before child 7.**

## Field-level readiness audit (computed this session, evidence for every child's Scope)

Computed by diffing `event_shapers.py`'s already-migrated `event_type` set against
`event_type_coverage.md`'s full 84-event scored list: **51 event types remain on the diffing
path.** Direct reads of `src/core/updates.py` confirmed typed update-record fields already exist
for the overwhelming majority — `event_extractor.py` simply never adopted them (predates the
apply-layer-shaper architecture). Full per-event grouping:

| Group | Events | Typed record confirmed | Child |
|---|---|---|---|
| Strategy (AGENCY+COGNITION+INFORMATION) | `route_selected`, `action_executed`, `route_family_first_use`, `defer_with_reason`, `self_model_updated`, `belief_assimilated`, `belief_updated`, `route_new_query`, `lead_certainty_changed`, `lead_certainty_updated`, `belief_stale`, `decision_diverged_by_belief`, `decision_divergence_detected`, `cooperation_event` | `EntityUpdate.property_updates` (already a direct, non-diffing read for most of these — confirmed `event_extractor.py:295-380`), `StrategicUpdate.leads_add_or_update`/`current_project_id_set`/`concerns_add_or_update` | 2 |
| Progression | `xp_granted`, `level_up`, `skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`, `progression_conversion_applied`, `progression_plateau_detected` | `IdentityUpdate.evolution_points_delta`/`evolution_level_set`/`learned_skills`/`traits_add`/`breakthroughs_add`/`unspent_ap_delta`/`_set` — confirmed `src/core/updates.py:220-243`, an exact 1:1 field match for every event except `progression_plateau_detected` (cross-tick derived, shaper-local state) | 3 |
| World dynamics (+ demographic + narrative co-fires) | `demographic_birth`, `demographic_mortality`, `ecology_cycle_completed`, `spawn_cadence_fired`, `threat_evolved`, `building_sabotaged`, `region_ownership_changed`, `region_transformed`, `region_trauma_delta`, `calamity_spawned`, `boss_spawned`, `raid_party_spawned`, `narrative_milestone`, `world_emergence_event` | `WorldUpdate.trauma_delta`/`owner_faction_id_set`/`kind_set`, `StateUpdate.entities_add`/`entities_remove`, `building_updates`, `last_calamity_tick_set` — confirmed `src/core/updates.py:745-768`, `event_extractor.py:889-1030` | 4 |
| Social | `social_memory_created`, `reputation_delta`, `group_joined`, `group_expelled`, `contract_offer_created`, `contract_offer_accepted`, `contract_completed`, `contract_lapsed`, `contract_expired_offer`, `contract_milestone_completed` | `SocialUpdate.trust_delta`/`reputation_set`/`betrayal_increment`, `StrategicUpdate.contracts_add_or_update` — confirmed `src/core/updates.py:274-299`; `group_joined`/`group_expelled`'s exact field genuinely unconfirmed, resolve in this child's own Investigate | 5 |
| Deferred, needs new instrumentation | `resource_node_depleted`, `resource_node_regenerated`, `node_recharged` (no typed per-node record — same gap Phase 1 already found for ECONOMY), `conservation_law_verified` (meta/derived, same reason Phase 1 deferred it), `faction_extinct` (needs entity-census tracking, same as Phase 1's finding) | None yet — this child builds it | 6 |

That's 14 + 7 + 14 + 10 = 45 events across children 2-5, plus 5 in child 6 = 50. The 51st,
`demographic_mortality`, is grouped into child 4 (confirmed push-ready via `entities_remove`,
correcting Phase 1's own premature deferral of it).

## Order

1. **`TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE`** (standard, P1) — **DONE.** Extended
   `tests/perf/test_simq_isolation_overhead.py` (had zero knowledge of `ENABLE_PUSH_EVENT_SHAPERS`
   before this ticket) with 2 new `@pytest.mark.slow` tests, varying the flag explicitly under the
   `inprocess` SimQ mode. Locked a 25% overhead band from 2 real, convergence-checked measurement
   runs (measured actual overhead: -3.75% and -2.35% — the shaper path measured *faster*, not
   slower, at this scale). No new CI/Makefile wiring needed — confirmed the file's existing tests
   were already reached only via `.github/workflows/test.yml`'s broad `pytest tests/ -m "slow or
   extra_slow"` sweep, which automatically covers the 2 new tests too. Children 2-6 now have a
   real, committed baseline to be measured against as they land.
2. **`TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY`** (standard) — **DONE.** AGENCY+COGNITION+
   INFORMATION+`cooperation_event` shaper (14 events), SHADOW mode. Found and fixed 2 real bugs
   via real-kernel verification: (1) registering directly into `SHAPER_REGISTRY` double-fires
   since `ENABLE_PUSH_EVENT_SHAPERS` already defaults `ON` — fixed with a new, separately-
   defaulted-OFF `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag + `PHASE2_SHAPER_REGISTRY` (**all
   subsequent Phase 2 shaper children must use this same registry/flag, not `SHAPER_REGISTRY`**);
   (2) missing `reset_run_state()` for new per-run dedup caches. Also confirmed a `_current_leads()`
   reconstruction pattern (prior_state full snapshot + this-tick delta fields) makes even
   materialized-state-*looking* events push-ready without new instrumentation, extending beyond
   Phase 1's simpler direct-field-read cases — reuse this pattern for similar cases in children
   3-5 before concluding something needs deferral. `STRAT-247`, `SOC-239`.
3. **`TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION`** (standard) — **DONE.** PROGRESSION shaper
   (7 events), SHADOW mode. Found and fixed the SAME class of bug as Child 2's `belief_stale`
   (`progression_plateau_detected` needed any-update gating, not identity-update gating) — this
   is now confirmed a *recurring* pattern, not a one-off; **children 4-5 should explicitly check
   any cross-tick/derived event for this exact gap before assuming direct-field reads are
   sufficient**. Also found and fixed a cross-shaper test-isolation gap (2nd shaper joining
   `PHASE2_SHAPER_REGISTRY` broke Child 2's own mock fixtures) — **children 4-5's own registry-
   level tests need the same defensive inertness for their new fields.** `PROG-117`.
4. **`TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS`** (standard) — **DONE.** WORLD dynamics +
   demographic + NARRATIVE co-fire shaper (14 events), SHADOW mode. Closed Phase 1's
   `demographic_mortality` deferral. No cross-tick derived events in this domain, so no
   any-update-gating bug this time (checked explicitly, confirmed not applicable) — this pattern
   is domain-dependent, not universal. `WORLD-115`, `INFRA-324` updated.
5. **`TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL`** (standard) — **DONE.** SOCIAL shaper (10
   events), SHADOW mode. Resolved the epic's one previously-unconfirmed field (`group_id_set`'s
   `-1` sentinel for leaving a group). Found and fixed a real `contract_expired_offer`
   double-firing bug — two independent mutation functions producing overlapping signals for the
   same contract in the same tick, invisible to the old extractor's single-materialized-view
   design. `SOC-240`.
6. **`TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION`** (standard) — **DONE.** Closed Phase 1's
   3 remaining named deferrals. Resource-node events needed **no new instrumentation after all** —
   corrected the earlier audit's mistaken assumption by tracing the real mutation site to
   `StateUpdate.node_updates`/`ResourceNodeUpdate.charges_delta`, already existing.
   `faction_extinct` implemented via full-population reconstruction, faithfully reproducing a
   real, found-but-deliberately-not-fixed dead HP-check bug in the old extractor.
   `conservation_law_verified` implemented as a genuine cross-shaper aggregation step in
   `run_shadow_shapers()` itself. `TOWN-190`, `FAC-013` updated in place. **All 5 shaper-build
   children (2-6) are now DONE.**
7. **`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2`** (standard, **P0**) — **DONE, GO verdict.**
   6-world x 500-tick event-stream comparison: 5/6 exact parity for all ~50 event types across all
   5 domains; 1/6 (`urban_political`, 2 extra CPU-intensive flags) showed 6 mismatches, root-caused
   via differential repro to the pre-existing, already-documented `INFRA-273` mechanism, not a
   shaper defect. Extended child 1's perf gate for the complete registry: -0.35% overhead.
8. **`TCK-20260806-PUSH-CUTOVER-PHASE2`** (standard, P1) — **DONE.** The irreversible step. Flag-
   gated mutual exclusion (same pattern Phase 1 proved out), every one of Phase 2's ~50 events
   individually flag-gated with one genuine complication found (`world_emergence_event`/
   `narrative_milestone` co-located with Phase 1's own guard). Found and fixed a real, previously-
   undetected bug via real-kernel verification: `run_shadow_shapers()`'s own separate, stale
   default caused a total blackout under the real post-cutover default state (`INFRA-326`). Full
   corpus re-run showed 37/69 `test_grade_regression.py` failures (up from Phase 1's 32/69),
   root-caused via decisive differential-repro (flag forced OFF vs ON) as the same pre-existing
   `INFRA-273` mechanism now visible on more pillars, not a regression — same discipline Phase 1's
   cutover established, cross-referenced not re-derived. `grade_anchors.json` left unrecalibrated.
   **All 8 children of this epic are now DONE.**

## Deferred / out-of-scope events (explicitly tracked, not silently dropped)

- **`quest_event`** (quest_started/completed/failed) — confirmed this session via raw JSONL
  inspection to already come from `quest_system`, a separate live-emission source, not
  `event_extractor.py`. Out of this epic's scope by definition (see epic ticket's Out of Scope).
- **Campaign/scenario-gated events** — `event_type_coverage.md` §4 P0-A Blocked, no calibration
  scenario exercises them; not migrated.
- **`camp_constructed`** — no engine path exists at all (`event_type_coverage.md` §3.9); not an
  observability question.

## Notes

- Unlike Phase 1 (strictly sequential, one domain proving the pattern before the next), Phase 2's
  children 2-6 are independent of each other in principle — each reads different typed update
  records, no child's shaper depends on another's output. They may run in any order or in
  parallel, but **all** must land before child 7, and child 1 (perf gate) should land before any
  of them so their own perf impact is measured against a real baseline as they're added, not
  discovered retroactively.
- If child 7 finds a real divergence tracing to a design flaw in children 2-6, the correct response
  is reopening the responsible child, not patching around it in child 7 or 8 — same rule Phase 1's
  own `SEQUENCE.md` established, carried forward here.
- Once all 8 land, the epic ticket itself closes with a full completion summary and
  `docs/audits/D20_simq_quality_status_review.md` is updated.
