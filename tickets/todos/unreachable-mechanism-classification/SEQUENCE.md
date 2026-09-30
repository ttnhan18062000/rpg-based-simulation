# Implementation Sequence — unreachable-mechanism-classification

`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` is the epic-tier parent and is not
implemented directly — it groups and sequences the six candidate children below. Per the epic's own
scope-only rule and this session's planner/implementer role split, the epic ticket named these
children but did not create them; T01-T04 were created by this (`rpg-implementer`) session as
`TCK-20260929-UNREACHABLE-CLASSIFY-{ZERO-CALLER,NEVER-SEEDED,DEAD-GUARD,WAVE-CONFIRM}` respectively
(flat in `tickets/todos/`, matching this repo's epic-folder precedent — the epic's own folder holds
only the epic ticket + this file). T05/T06 remain uncreated, blocked on their prereqs below.

## Order

1. `T01` = `TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER` — Classification pass over 3 of the 4
   zero-caller / dead-constant tickets (`TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT`,
   `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS`,
   `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS`). `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-
   NEVER-FIRES` is cited but excluded from classification here — its DEFECT verdict is T04's to
   record. No unmet prereq. **`DONE`, closed to `tickets/done/`, 2026-09-30:** `CALAMITY-RANDOM-CHANCE` = fifth outcome `NO-MECHANISM` (AC-7), `REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN` = `UNDECLARED` (live `TownResolutionSystem` duplicate), `PROFILE-API-PAYLOAD` = `DEFECT` (executed).
2. `T02` = `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED` — Classification pass over the 4
   never-seeded-precondition tickets (`TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`,
   `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED`,
   `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`,
   `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER`). No unmet prereq. **`DONE`, closed to
   `tickets/done/`, 2026-09-30.** All 4 covered tickets carry a verdict:
   `CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` = `STALE-PREMISE`; `DEMOGRAPHIC-COHORT-CYCLE-
   POPULATION-COHORTS-NEVER-SEEDED` = `STALE-PREMISE`; `CAPABILITY-CONTEXT-REGION-ENEMY-DATA-
   ALWAYS-EMPTY` = `UNDECLARED` (split, two root shapes); `NO-MECHANISM-RECORDS-PER-ENEMY-KIND-
   DANGER` = `UNDECLARED`. No `CONDITION` verdict reached for any of the 4 — see `T02`'s own
   Completion Summary. The demographic-cohort premise-vs-shipped-code tension noted at scoping time
   (below) resolved to `STALE-PREMISE`, independently reproduced by `rpg-feature-planning`; the
   `camp` ticket turned out to share the exact same shape once checked. Full evidence:
   `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/`.
   **Open finding surfaced at scoping time, since resolved:** the demographic-cohort ticket's
   premise ("no world ever seeds `population_cohorts`") may already be contradicted by
   `TCK-20260831-POPULATION-COHORT-SEEDING` (done, 2026-08-31), which appears to add exactly this
   seeding logic at `src/worldbuilding/compiler.py:190-208,360-363,449`. T02 itself must reconcile
   this — either the corpus ticket is stale, or the seeding code is wired but no real world module
   declares a `PopulationSpec` that reaches it (a content `CONDITION`, not a code defect). Written
   into T02's own Scope/AC/Assumptions as a required step.
3. `T03` = `TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD` — Classification pass over the 3
   dead-guard/filter tickets (`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`,
   `TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`,
   `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`). No unmet prereq.
   **`DONE`, closed to `tickets/done/`, 2026-09-30:** `REGIONAL-INFLUENCE-SHIFT` = `DEFECT`, `REGION-DANGER-SEEN` = `DEFECT`, `COGNITION-CAPACITY-ENFORCEMENT` = `UNDECLARED`. Unblocks `T05`.
4. `T04` = `TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM` — Confirm the 2 wave-assessed verdicts
   (`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` = record, do not re-investigate;
   `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` = record, do
   not re-investigate) plus the 1 remaining scale/content ticket
   (`TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE`, boss-gate half only). No
   unmet prereq. **`DONE`, closed to `tickets/done/`, 2026-09-30:** `CALAMITY-INTENSITY` = `DEFECT` and `LAIR-REGION-TRAUMA` = `CONDITION` (world-content), both recorded from PR #258; `COMBAT-GATE` boss-gate half = `CONDITION` (corpus run length; first `world_boss` tick 2101 with the posture flag ON and OFF). Note:
   `CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` appears in both T01's corpus group (by shape) and T04's
   scope (by wave-assessment status) — T04 owns its actual disposition (recording the DEFECT verdict
   from PR #258); T01 covers it only as a corpus-grouping entry, not a duplicate classification pass.
5. `T05` = `TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY` — **`DONE`, closed to `tickets/done/`, 2026-09-30:** `PERCEPTION-UPDATE-PHASE` = `UNDECLARED` confirmed; the decision needs a human and is not made. Original scoping: Perception-authority design decision (`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`,
   strongly pre-indicated `UNDECLARED`; confirm, don't re-derive). **Prereq: `T03`** — the epic scopes
   this as an `UNDECLARED` case only after the dead-guard pass in T03 has run, since T03's tickets
   share the strategic-cognition code area this decision touches.
6. `T06` = `TCK-20260930-UNREACHABLE-CLASSIFY-ROLLUP` — **`DONE`, closed to `tickets/done/`, 2026-09-30:** the shared document is `docs/plans/unreachable_mechanism_classification.md`. Original scoping: Ranked fix order for the `DEFECT` subset + corpus-run-length-vs-world-content owner split
   for the `CONDITION` subset. **Prereq: `T01`–`T04`** — cannot rank or split before every ticket in
   those four passes carries a verdict.

## Why This Order Matters

**T01–T04 classify; nothing before them is blocked on anything.** They can run in any order relative
to each other, including in parallel, since each covers a disjoint ticket group (T04's overlap with
T01 on `CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` is a citation, not a re-classification — see the T04
note above). **T05 and T06 are synthesis/decision steps that need T01–T04's answers to exist first**,
so they are sequenced last, matching the epic's own prereq table.

## One thing this epic explicitly does not do

**It does not assume a shared root cause across T01–T04's tickets.** The wave that motivated this
epic (`TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE`, PR #258) tested that hypothesis directly and
disconfirmed it — `regional_trauma`'s cause (spatial isolation) and
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`'s cause (a death-outcome-kind filter missing
`DEFEAT`) are different in kind. Any child ticket under T01–T04 that believes it has found a shared
cause across its own group must prove it with evidence (a grep result, a content fact, or tick
arithmetic), not assume it from the corpus grouping alone.

**It does not touch `registries/mechanisms.yaml`.** The epic's own scope guard applies to every
child: that file must stay byte-for-byte unchanged across the whole epic, same as the wave's own
guard. `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` owns that registry's
`implemented_by` residue and is adjacent, not merged into, this epic.

## Epic status

All six children are done and the 14 corpus tickets carry verdicts (`docs/plans/unreachable_mechanism_classification.md`). **The epic ticket itself has not been closed**: epic-tier closure (staging artifacts, working-log row, moving this folder to `tickets/done/`) was left for the planner, since the corpus tickets it classifies remain open by design and landing the batch is the user's call.
