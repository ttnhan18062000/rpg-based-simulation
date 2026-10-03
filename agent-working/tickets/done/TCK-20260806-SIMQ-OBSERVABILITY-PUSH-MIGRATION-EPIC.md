---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC
phase: done
date: 2026-08-06
tags: [observability, engine, combat, simulation-quality, performance]
---

# TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC

## Title
Epic: Migrate COMBAT/ECONOMY/FACTION event emission from post-tick diffing to apply-layer
push-based emission, carefully gated

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P0

## Request Summary
`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE` (DONE, 2026-08-06) investigated whether
the engine's entire observability pipeline — currently built on post-tick snapshot diffing via
`EventExtractor.extract()`, called once per tick from `kernel.py:909` — should instead emit events
at the authoritative apply layer, where every typed update record is already being walked exactly
once to mutate state. All three originally-feared blockers (replay determinism, "Zero Simulation
Impact," performance measurability) resolved to non-issues on direct evidence. Coverage audit found
COMBAT, ECONOMY, and FACTION already read typed, causally-tagged update records today
(`CombatUpdate.outcome_kind`, `ResourceTransferIntent.source_kind`,
`FactionUpdate.diplomatic_relations_set`) — push-ready with zero new instrumentation.
PROGRESSION's quest detection is genuinely diff-only and needs new instrumentation first (Phase 2,
deliberately not yet scoped). Recommendation: build Phase 1 (COMBAT/ECONOMY/FACTION), phased,
SHADOW-mode rollout before any cutover.

This is now the user's explicitly stated top priority, with an explicit instruction to check the
migration carefully. This touches the engine's hottest path (`ApplyPath.apply_generation()`, called
every tick) — a mistake here is not a documentation typo, it's a live simulation-correctness or
performance regression. This epic replaces the single flat implementation ticket originally filed
(`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-EMISSION-PHASE1-COMBAT-ECONOMY-FACTION`, now removed and
superseded by this epic's decomposition — see Related Tickets) with a properly gated sequence: pilot
on one domain first, prove the pattern, only then repeat it for the other two, then a dedicated
pre-cutover validation gate (shadow-mode comparison + performance re-measurement) that must pass
before the final, most-irreversible step — removing the old diffing code and switching the live
event stream to the new path.

## Scope
Break down into 5 child tickets, sequenced so each is individually small and independently
verifiable, with a hard validation gate before the irreversible cutover step:

1. **`TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`** (hotfix, already fully
   scoped, moved into this epic's folder) — fix the confirmed `event_extractor.py` bug (missing
   `outcome_kind` check) in the *current* diffing path first, so shadow-mode comparison in step 4
   has a correct baseline to compare the new path against, not a known-buggy one.
2. **`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`** (standard) — build the shaper-registry mechanism
   itself (mirroring `QualityHub.SCORER_REGISTRY`'s proven shape) and implement it for COMBAT only,
   as the pilot domain. Wired under `FeatureMode.SHADOW` — constructs events but does not yet
   deliver them live. Proves the pattern end-to-end on the domain with the most active
   investigation history this session before repeating it elsewhere.
3. **`TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION`** (standard) — extend the now-proven registry with
   ECONOMY and FACTION shapers, still SHADOW-mode only.
4. **`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`** (standard) — the mandatory pre-cutover gate: run
   the full calibration corpus with SHADOW mode active, compare every shaper-produced event against
   the (now-fixed, per step 1) diff-based extractor's output for all 3 domains, investigate and
   resolve any divergence found (do not assume the new path is correct by default). Separately,
   re-run `tests/perf/test_simq_isolation_overhead.py`'s existing harness and confirm the locked
   regression-guard thresholds still hold with the shadow path active. **Cutover (step 5) does not
   proceed until this ticket is DONE.**
5. **`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`** (standard) — the irreversible step: remove
   COMBAT/ECONOMY/FACTION handling from `event_extractor.py`'s diffing pass, wire shaper output to
   the live queue, recalibrate `grade_anchors.json` for any scenario whose grades shift, update
   `docs/parity_ledger/` entries and `quality_scoring_contract.md` if event shape changed
   observably.

Each child ticket runs its own full `implement-ticket.js` pipeline (Investigate → Plan → Review →
Implement → Architecture-Verify → Test → Parity → Verify → Finalize) — this epic ticket itself does
not implement anything directly, per the epic tier's Scope-only pipeline.

## Out of Scope
- Phase 2 (PROGRESSION's quest detection, demographic/XP domains) — needs new typed-record
  instrumentation first; not scoped by this epic, tracked separately once Phase 1's own findings
  (particularly step 4's validation) inform what Phase 2 actually needs.
- Any change to scoring rules, deltas, or grade calculation logic — this epic is purely about how
  events reach the queue, not how they're scored once there.
- Removing `EventExtractor` entirely — it remains responsible for every domain this epic doesn't
  touch (quest, demographic, XP/level, etc.).
- `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s own scoring-rule design work — that ticket
  remains blocked on this epic's completion (specifically step 5), tracked in its own file.

## Acceptance Criteria
- [x] All 5 child tickets filed to `tickets/todos/simq-observability-push-migration/`, with
      `SEQUENCE.md` establishing the strict build → validate → cutover order
- [x] Step 1 (hazard fix) lands before step 4 (shadow validation) begins
- [x] Step 2 (COMBAT pilot) proves the registry pattern before step 3 repeats it
- [x] Step 4 (shadow validation + perf) is DONE, with any divergence found investigated and
      resolved, before step 5 (cutover) begins — this ordering is not optional (step 4 found and
      drove the fix for 2 real bugs by reopening step 2, per `SEQUENCE.md`'s own rule)
- [x] Step 5 completes: old diffing code live-path replaced for the 3 domains (flag-gated, not
      deleted — a deliberate, documented deviation, see step 5's own investigation.md), live queue
      fed by the new path, parity ledger updated. `grade_anchors.json` was **deliberately left
      unrecalibrated** — a second deliberate, documented deviation: step 5's mandatory full-corpus
      run found 32 grade-regression failures, root-caused via a flag-on/flag-off differential
      repro to the pre-existing, already-tracked `INFRA-273` tick-budget-watchdog mechanism, not
      to a genuine event-shape or behavior change from this migration. Recalibrating the anchors
      would have masked that pre-existing issue under this migration's commit, which this repo's
      gate-integrity rule specifically prohibits ("do not recalibrate reflexively to make it
      pass" — step 5's own AC).
- [x] `docs/audits/D20_simq_quality_status_review.md` updated with the epic's outcome once complete
- [x] `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s blocking-dependency note updated to
      reference this epic (done)

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE (DONE — the investigation this epic
  implements)
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-EMISSION-PHASE1-COMBAT-ECONOMY-FACTION (**superseded and
  removed** — replaced by this epic's 5-ticket decomposition, per the user's explicit request for
  multiple tickets under an epic with careful checking; no implementation had started on it)
- TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX (child ticket 1, moved into this
  epic's folder)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (blocked on this epic's completion)
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (DONE — grandparent investigation that
  found the original hazard-misclassification bug)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §3 (Performance Contract), §4.8
  (`QualityHub.SCORER_REGISTRY` — the pattern the new shaper registry mirrors), §5 COMBAT/ECONOMY/
  FACTION
- `docs/performance/simq_isolation_overhead.md` (existing measurement harness/thresholds to reuse)
- `docs/audits/D20_simq_quality_status_review.md` Finding 10, Finding 11

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE/` (parent investigation)
- `stored_artifacts/TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY/` (grandparent
  investigation)

## Related Code Areas
- `src/engine/apply.py` (`ApplyPath.apply_generation` — the new emission point)
- `src/observability/event_extractor.py` (the diffing code being partially replaced)
- `src/observability/queue.py`, `src/observability/events.py`
- `src/domains/optimization/feature_flags.py` (`FeatureMode.SHADOW`)
- `src/simulation_quality/quality_hub.py` (`SCORER_REGISTRY` — the pattern being mirrored)
- `tests/perf/test_simq_isolation_overhead.py`

## Assumptions / Open Questions
- Whether any divergence found in step 4's shadow comparison will require revisiting step 2/3's
  shaper design is unknown until that step actually runs — child tickets are sequenced so this is
  possible without having already committed to cutover.

## Implementation Notes
(epic — no direct implementation; child tickets carry implementation, see each child's own
Implementation Notes / investigation.md)

## Test Summary
(epic — no direct implementation; aggregate: 798/798 `tests/unit/observability/` pass as of the
final child; full 79-scenario `make simq-full-audit-full` run performed as the mandatory cutover
gate, 32 grade-regression failures found and root-caused to pre-existing `INFRA-273`, not this
epic's code — see child 5's Test Summary and investigation.md)

## Files Changed
(epic — no direct implementation; see each child ticket's own Files Changed. Net new: 
`src/observability/event_shapers.py`, `tests/unit/observability/test_event_shapers.py`,
`tests/unit/observability/test_event_shapers_economy_faction.py`. Modified across children:
`src/observability/event_extractor.py`, `src/engine/kernel.py`,
`src/domains/optimization/feature_flags.py`, `tools/calibrate_simq.py`, 4 parity ledger files,
`quality_scoring_contract.md`, `current_state.md`, `extension_points.md`, `feature_flags.md`,
`D20_simq_quality_status_review.md`.)

## Completion Summary
All 5 child tickets are DONE, in strict sequential order per `SEQUENCE.md`:

1. `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` — fixed the pre-existing
   diffing-path bug that would have poisoned the shadow-comparison baseline.
2. `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT` — built the shaper registry, piloted on COMBAT under
   SHADOW mode; reopened once when child 4's real-corpus comparison found 2 genuine bugs
   (`entity_killed` hazard false-positive, missing volumization rule) — fixed in place, per the
   epic's own "reopen, don't patch around it" rule.
3. `TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION` — extended the registry to ECONOMY and FACTION,
   still SHADOW-mode.
4. `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF` — the mandatory pre-cutover gate: 130/131 real-corpus
   active ticks matched the old extractor exactly post-fix, 0 payload-value mismatches, no
   measurable performance overhead. GO verdict.
5. `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` — cut live delivery over for all 3 domains.
   Flag-gated (not deleted) for a real rollback path; `entity_killed`/`hero_death_unrecorded`
   narrowed (not removed) to preserve non-shaper-owned kill causes exactly. The mandatory
   full-corpus verification step surfaced 32 grade-regression failures; root-caused via a decisive
   flag-on/flag-off differential repro to the pre-existing, already-tracked `INFRA-273`
   tick-budget-watchdog mechanism, not to this migration — `grade_anchors.json` deliberately left
   untouched rather than recalibrated to mask an unrelated issue.

**Full event-coverage accounting, per the epic's governing instruction ("make sure the new push is
not missing any existing defined event, if it cannot be implemented in the current design, defer
it not skip it")**: of the 21 COMBAT/ECONOMY/FACTION-adjacent events audited, 18 are now migrated
and live; 3 are explicitly deferred with documented reasons (`demographic_mortality` — broader
despawn scope than combat; 5 ECONOMY events + `faction_extinct` needing new typed-record
instrumentation not yet built) plus 2 confirmed pre-existing dead code
(`combat_resolved`/`attrition_threshold_crossed`, never emitted anywhere, disclosed not a migration
target). None silently dropped — every deferral is named, reasoned, and carried forward into
`SEQUENCE.md`'s "Deferred events" section for Phase 2 to pick up.

Two real bugs were found and fixed before cutover (not after, and not by the corpus-run gate that
would have caught them too late) via the epic's own mandatory shadow-validation step. One
pre-existing, unrelated infrastructure issue (`INFRA-273`) was surfaced and characterized more
completely by this epic's own closing verification, without being misattributed to this migration
or silently papered over via anchor recalibration. Phase 2 (quest/demographic/XP domains) remains
deliberately unscoped, to be informed by what Phase 1 actually revealed rather than a guess made in
advance.
