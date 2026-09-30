---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED
phase: done
date: 2026-09-29
tags: [investigation, root-cause, corpus, world, cognition]
---

# TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED

## Title
Classification pass over the 4 never-seeded-precondition tickets (`camp`, `demographic_cohort_cycle`,
`CapabilityContext.region_data`/`enemy_data`, per-enemy-kind danger tracking)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` groups 14 open "code is real and wired but
never executes in any run this project actually performs" tickets and requires each to be assigned
exactly one verdict from a four-value axis (`DEFECT` / `CONDITION` / `UNDECLARED` / `MISLABEL`),
evidence-backed per the epic's evidence bar — a named zero-caller grep, a content fact, or tick
arithmetic, not code-reading alone (`TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE`, PR #258, is the
method precedent: three mechanisms that read identically on their face resolved to two different
verdicts). This ticket is `T02` in that epic's `SEQUENCE.md` — the classification pass over the
epic's "Never-seeded precondition state" group of 4:

- `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` (P2) — `CampState` correct/wired, but
  no corpus world seeds `state.camps`.
- `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED` (P2) —
  `DemographicCycleService.process_demographics` correct/wired, guarded by
  `if not region.population_cohorts`, which the ticket claims never opens.
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (P2, currently `OPEN` after a
  pure lifecycle correction on 2026-09-20; substance untouched since 2026-09-13) —
  `CapabilityContext.region_data`/`.enemy_data` are read at real decision time but never populated
  by any real construction site.
- `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` (P2, same 2026-09-20 lifecycle-correction
  status as above) — no belief-producing mechanism anywhere captures per-enemy-kind danger data at
  all, so combat capability estimates always fall back to a hardcoded table.

Note the priority spread: all four are individually `P2`; this classification ticket is also `P2`
per the epic's own instruction (`T02` is not an average or inheritance of the covered tickets'
priorities — it is a separate scope-only assessment pass).

## Scope
- For each of the 4 tickets above, assign exactly one verdict from `DEFECT` / `CONDITION` /
  `UNDECLARED` / `MISLABEL`, following the epic's classification axis and evidence bar exactly (see
  epic `## Scope`). `CONDITION` in particular must state either a content fact (what a real
  compiled/procgen corpus world's own composition does or does not contain) or tick arithmetic — not
  "the field/guard reads empty," which is the claim being tested, not the evidence for it.
- For `CAMP-STATE-NEVER-SEEDED` and `DEMOGRAPHIC-COHORT-CYCLE`: confirm directly, against a real
  compiled corpus world (not just a code read), whether `state.camps` / `region.population_cohorts`
  are actually empty in practice today. **Reconcile explicitly against
  `TCK-20260831-POPULATION-COHORT-SEEDING`** (closed `DONE`, 2026-08-31) and the live code at
  `src/worldbuilding/compiler.py:190-208,360-363,449` — `WorldCompiler.compile()` already calls
  `_seed_population_cohorts(region_declared_population.get(r_spec.id, 0))`, where
  `region_declared_population` is built by summing every world module's `PopulationSpec.count` per
  `spawn_region` (`compiler.py:360-363`). This seeding mechanism appears to already be shipped and
  wired, which is in tension with `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE`'s premise that "no
  compiled or procedurally-generated world today ever seeds `population_cohorts`."
  **The decisive fork (identified during cross-check by `rpg-feature-planning`, 2026-09-30, code
  reading confirmed unambiguous):** `region_declared_population` at `compiler.py:360-364` is keyed
  by **`pop_spec.spawn_region`**; the lookup at `compiler.py:449` uses **`r_spec.id`**, via
  `.get(r_spec.id, 0)`. If those two identifier spaces disagree for real world content, every
  lookup silently returns `0`, `_seed_population_cohorts`'s own `if declared_population <= 0: return
  {}` guard fires, every region gets `{}`, and `DemographicCycleService`'s `if not
  region.population_cohorts: continue` guard (`cohort.py:349`) no-ops for the whole run — wired
  code, correct arithmetic, empty result, silent. That is the exact shape this epic exists to
  classify. **The sharp first experiment:** compile one real world spec and print, per region,
  `r_spec.id`, the actual `region_declared_population` keys, and the resulting
  `population_cohorts`. If the keys match and cohorts come out non-empty, the corpus ticket's
  premise is simply false today (see the AC-7 `STALE-PREMISE` outcome below). If the keys don't
  match, the ticket was right (cohorts really are always empty) but for a different, more specific
  and more fixable cause (a key-space mismatch, not "never seeded") — record that as `DEFECT`, not
  `CONDITION`. **Do not assume which before running the experiment.**
- For `CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` and `NO-MECHANISM-RECORDS-PER-ENEMY-KIND-
  DANGER`: both already carry extensive, evidence-based investigation in their own bodies (grepped
  every real `CapabilityContext`/`BeliefEntry` construction site; checked the Mechanics Bible, parity
  ledger, and `capability_and_knowledge_contract.md` for declared intent). Read their existing
  Implementation Notes / Completion Summary in full before re-deriving anything — most of the
  evidence this pass needs may already exist. This pass's job is to map that existing evidence onto
  the epic's four-value axis (neither ticket has been run through that specific axis yet), not to
  redo the investigation.
- Test, for each of the 4, whether the epic's own grouping ("never-seeded precondition state") is
  actually diagnostic of the verdict, or whether it is only a shape-level resemblance. Unlike `camp`
  and `demographic_cohort_cycle` (both catalogued as confirmed instances #5 and #6 in
  `docs/plans/world_composition_precondition_gap_finding.md`), neither
  `CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` nor `NO-MECHANISM-RECORDS-PER-ENEMY-KIND-
  DANGER` appears in that document's six catalogued instances — their root causes (an always-empty
  struct field with no real producer anywhere in the codebase; a gameplay mechanism that was simply
  never built, confirmed via a declared-intent check against the Mechanics Bible) may resolve closer
  to `UNDECLARED` or a genuinely new/5th outcome than to `CONDITION`. Do not force either into
  `CONDITION` merely because the epic's corpus table filed it under "never-seeded."
- Split any resulting `CONDITION` verdict into corpus-run-length vs. world-content, per the epic's
  AC-6, with a named owner for each.
- Record each verdict directly in the covered ticket's own body (its `## Status` and a note in
  `## Completion Summary` or `## Implementation Notes`, per the epic's Deliverable 2), and contribute
  this pass's findings to the epic's classification document under `docs/plans/` (epic Deliverable 1)
  — coordinate with the `T01`/`T03`/`T04` passes on whether this is one shared new doc or additional
  sections in the existing `docs/plans/world_composition_precondition_gap_finding.md` (which already
  covers 2 of these 4 tickets as its own instances #5/#6).

## Out of Scope
- Fixing anything. No code, content, or world-module change lands under this ticket, regardless of
  which verdict a ticket receives — a `DEFECT` verdict becomes its own future fix ticket.
- Touching `registries/mechanisms.yaml` — must stay byte-for-byte unchanged across this ticket, same
  guard the epic and the PR #258 wave both used and verified.
- Re-deriving or citing combat-volume numbers — the epic's own hard constraint; those numbers moved
  twice and are not safe to cite without a fresh measurement, which this ticket does not perform.
- Actually resolving `NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER`'s own open design question (whether
  and how to build a combat-outcome-learning mechanism) — that ticket's own `BLOCKED`-pending-a-
  user-level-decision status is unchanged by this pass; this pass only classifies its reachability
  shape, it does not make the design decision the ticket itself is waiting on.
- Actually resolving `CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`'s own open question (what
  should populate `region_data`/`enemy_data`, if anything) — same reasoning.
- Deciding whether to build a general-purpose world-composition validation layer — explicitly named
  as the user's call in `docs/plans/world_composition_precondition_gap_finding.md`'s own "What this
  document does not do" section; not reopened here.
- The other 10 corpus tickets and their classification passes (`T01`, `T03`, `T04`, plus the
  synthesis steps `T05`/`T06`) — each is its own ticket per the epic's `SEQUENCE.md`.

## Acceptance Criteria
- [x] Each of the 4 covered tickets carries exactly one verdict from `DEFECT` / `CONDITION` /
      `UNDECLARED` / `MISLABEL`, **or** is recorded as a fifth "resists all four verdicts" outcome
      per the epic's AC-7 — never forced into the nearest bucket. **Final verdicts:** `CAMP-STATE` =
      `STALE-PREMISE` (AC-7); `DEMOGRAPHIC-COHORT-CYCLE` = `STALE-PREMISE` (AC-7); `CAPABILITY-
      CONTEXT` = `UNDECLARED` (split: `enemy_data` half inherited from `NO-MECHANISM-RECORDS`,
      `region_data` half independently derived, same label, different root shape); `NO-MECHANISM-
      RECORDS` = `UNDECLARED`.
- [x] Every verdict cites evidence per the epic's bar: a named zero-caller grep, a content fact (what
      a real compiled/procgen corpus world's composition does or does not contain), or tick
      arithmetic. A verdict supported only by re-reading the code, without checking real compiled
      output or content, is not accepted. (`CAMP-STATE`/`DEMOGRAPHIC-COHORT-CYCLE`: real
      `WorldCompiler.compile()` executions against `frontier_living_world.yaml`, independently
      reproduced for the cohort case. `CAPABILITY-CONTEXT`/`NO-MECHANISM-RECORDS`: direct code reads
      confirming zero real producers/`generator.py` branches, not re-derivation of the covered
      tickets' own prose.)
- [x] `CAMP-STATE-NEVER-SEEDED` and `DEMOGRAPHIC-COHORT-CYCLE`'s verdicts explicitly reconcile
      against `TCK-20260831-POPULATION-COHORT-SEEDING`'s already-shipped compile-time seeding code
      (`src/worldbuilding/compiler.py`), stating clearly whether the "never seeded" premise still
      holds against a real compiled world, is stale, or points to an upstream content gap. **Both
      resolved `STALE-PREMISE`** — see each ticket's own Implementation Notes.
- [x] `DEMOGRAPHIC-COHORT-CYCLE`'s reconciliation runs the sharp first experiment above (compile a
      real world spec, compare `r_spec.id` against `region_declared_population`'s actual keys, check
      the resulting `population_cohorts`) **before** assigning a verdict — not a code-read guess.
      **If the keys match and cohorts come out non-empty:** this ticket's premise is false *as of
      today*, and per the epic's own AC-7 this is recorded as a fifth outcome, not forced into
      `CONDITION` or `MISLABEL` — label it `STALE-PREMISE` (this pass's own addition to the axis,
      agreed with `rpg-feature-planning` 2026-09-30) and record alongside it: the ticket was filed
      2026-09-20, three weeks *after* `TCK-20260831-POPULATION-COHORT-SEEDING` closed on 2026-08-31,
      apparently on the strength of a `registries/mechanisms.yaml` verdict dated 2026-09-16 that was
      never re-checked against the shipped compiler code. That is a finding about how the ticket got
      written, not about the mechanism itself — do not fold it into this pass's mechanism verdicts;
      if it holds up after the experiment runs, it is process feedback for `agent-working-design`
      (registry-verdict/ticket-filing staleness), not a finding for `rpg-feature-planning` or
      `rpg-implementer` to act on directly. **If the keys don't match:** cohorts really are always
      empty, but the cause is a specific `spawn_region`-vs-`r_spec.id` key-space mismatch — record
      `DEFECT` (not `CONDITION`) with that exact cause, and note the ticket was right for the wrong
      reason. **Resolved: keys match; `STALE-PREMISE`, independently reproduced.**
- [x] Any `CONDITION` verdict among the 4 is split into corpus-run-length vs. world-content, each
      with a named owner, per the epic's AC-6. **N/A this pass — no covered ticket resolved to
      `CONDITION`.** (Two resolved `STALE-PREMISE`, two `UNDECLARED`.)
- [x] Each verdict is recorded in its own covered ticket's body. **Epic's shared classification
      document under `docs/plans/` is NOT updated by this pass** — deferred to `T06` (the rollup
      ticket), per this ticket's own Scope's instruction to "coordinate with `T01`/`T03`/`T04`
      passes on whether this is one shared new doc or additional sections in the existing
      `docs/plans/world_composition_precondition_gap_finding.md`" — a decision that needs all four
      passes' output, not just this one. Flagged explicitly rather than silently left undone.
- [x] `registries/mechanisms.yaml` is confirmed byte-for-byte unchanged (empty `git diff` against
      `origin/main`, not local `main`) at completion — verified after every experiment run this pass.
- [x] No `src/`, `tests/`, or content change lands as part of this ticket. Confirmed: only `.md`
      ticket files touched.

## Related Tickets
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — parent epic; this is its `T02` child.
- `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` — covered ticket 1 of 4.
- `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED` — covered ticket 2 of 4.
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` — covered ticket 3 of 4.
- `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` — covered ticket 4 of 4.
- `TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE` (closed, PR #258) — the method precedent this pass
  reuses: bounded reachability question, four-value-axis classification, evidence bar.
- `TCK-20260831-POPULATION-COHORT-SEEDING` (closed, DONE) — directly relevant, unreferenced by
  `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE` itself: appears to already implement the compile-time
  seeding that ticket claims never happens. Must be reconciled, not skipped, during this pass.
- `TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION` — the ticket whose first real run
  originally produced the `demographic_cohort_cycle` finding.
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`,
  `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` — cited by both cognition-side
  covered tickets as the origin/unblocking chain for their own evidence.

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — the shared pattern document; already
  names `camp` (instance 5) and `demographic_cohort_cycle` (instance 6) as confirmed instances, and
  explicitly states it "does not audit the rest of the corpus" — this pass's job for those two is to
  formalize an existing finding into the epic's four-value axis, not to re-derive it, while the other
  two covered tickets are outside that document's own catalogue and need their own axis mapping.
- `docs/cognition/capability_and_knowledge_contract.md` — cited by both `CAPABILITY-CONTEXT-REGION-
  ENEMY-DATA-ALWAYS-EMPTY` and `NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` as the contract their
  disposition may need to update.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE/` — Card J's reachability method,
  reused as this pass's own classification procedure (per the epic's own Related Stored Artifacts).
- `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/` — this ticket's own
  `investigation.md`/`plan.md`/`test_plan.md`, migrated at closure.

## Related Code Areas
- `src/core/state.py` (`CampState`)
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, `_seed_population_cohorts()`,
  `region_declared_population` — where the camp/cohort reconciliation evidence lives; specifically
  `:360-364` where `region_declared_population` is keyed by `pop_spec.spawn_region`, versus `:449`
  where the lookup uses `r_spec.id` — the decisive fork for this ticket's sharp first experiment)
- `src/domains/demographics/cohort.py:349` (`DemographicCycleService`'s `if not
  region.population_cohorts: continue` guard — where an empty-keyed lookup silently no-ops)
- `data/content/world/` (camp-kind and `PopulationSpec` content templates, if any)
- `src/domains/demographics/cohort.py` (`DemographicCycleService`)
- `src/engine/world_dynamics.py` (`DemographicCycleService`'s real caller)
- `src/cognition/capability_estimate.py` (`CapabilityContext`, `CapabilityEstimateService.estimate()`,
  `_ENEMY_DANGER` hardcoded fallback table)
- `src/domains/adventure/scoring.py`, `src/engine/tactical.py` (real `CapabilityContext` construction
  sites, confirmed to never pass `region_data`/`enemy_data`)
- `src/systems/strategic_systems/belief.py`, `src/domains/combat_engagement/phase.py` (every real
  `BeliefEntry` construction site, confirmed none captures per-enemy-kind data)
- `src/core/self_model.py` (`KnowledgeFact`, the shape-matching but currently-unreachable candidate
  producer named by both cognition-side tickets)

## Assumptions / Open Questions
- **Environment note (tested directly, not assumed):** `mcp__knowledge-search__search_docs` is
  **live** in this worktree (`m2-foundational-systems-tickets`) — a query for "never-seeded
  precondition camp state population cohorts world composition" returned real ranked results,
  including the exact `world_composition_precondition_gap_finding.md` sections and
  `TCK-20260831-POPULATION-COHORT-SEEDING`. The epic's own caution that "both semantic search paths
  are dead" was recorded in a different worktree (`m2-idea43-temporal-note`) and does not hold here;
  a future child ticket in this worktree should not assume it applies without testing.
  `graphify query` on the same topic returned mostly unrelated matches (RNG-seeding code, not
  world-composition seeding) — not evidence the tool is broken, just that this topic is a cross-file,
  abstract pattern rather than a single symbol/call-graph edge; a doc/ticket keyword search was more
  productive for it than a code-graph traversal.
- **Open, load-bearing:** whether `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE`'s premise is still true
  given `TCK-20260831-POPULATION-COHORT-SEEDING`'s already-shipped seeding code — this is the single
  most consequential open question for this pass and is called out twice above (Scope and Acceptance
  Criteria) so it cannot be silently skipped. Resolved to a specific, checkable fork
  (`spawn_region`-vs-`r_spec.id` key match) by `rpg-feature-planning`'s independent cross-check on
  2026-09-30 — do not re-derive that fork from scratch, run the experiment it names.
- **Scope-guard check methodology, carried forward from that same cross-check:** always diff a scope
  guard (e.g. `registries/mechanisms.yaml` byte-for-byte, or "what changed since this branch's base")
  against `origin/main`, never a local `main` ref in a long-lived worktree — a stale local `main` can
  be dozens of merges behind and make an unrelated prior PR's diff look like this ticket's own scope
  creep.
- **Open:** whether `CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` and `NO-MECHANISM-RECORDS-
  PER-ENEMY-KIND-DANGER` genuinely belong in the epic's "never-seeded precondition state" grouping at
  all, versus being better described as `UNDECLARED` (no declared producer/consumer relationship) or
  a genuinely new outcome — flagged in Scope; this pass should test rather than inherit the epic's
  own grouping.
- **Layer choice:** used `layer: simulation` to match the parent epic and the PR #258 precedent
  ticket (`TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING`, also `layer: simulation`),
  even though the 4 covered tickets individually use `layer: world` (camp, demographic-cohort) and
  `layer: strategy` (capability-context, enemy-kind-danger). The classification-pass work itself
  spans both domains and matches neither individually, consistent with the epic's own precedent for
  this kind of corpus-wide assessment ticket.
- **Both cognition-side covered tickets currently sit in `tickets/todos/` with a "moved back to the
  backlog, 2026-09-20" lifecycle-correction banner** — a pure location/hook-noise fix, not a
  substance change (confirmed by their own banners, quoting `git log --follow`). Their last real
  substance change was 2026-09-13/14. Both banners also flag that `perception` was independently
  found dormant and corrected `done` → `orphan` two days after either ticket was last touched — worth
  a quick sanity check that this doesn't also affect either ticket's own premises, though neither
  ticket's core finding (empty `CapabilityContext` fields; no per-enemy-kind belief producer) appears
  to depend on `perception`'s own state.

## Implementation Notes

### `demographic_cohort_cycle` — verdict: `STALE-PREMISE` (AC-7 fifth outcome), 2026-09-30

**Dispatched by `rpg-feature-planning` (user-authorized) to run the decisive experiment rather than
reason from code.** Ran, did not read to a conclusion.

**Experiment.** Compiled a real, in-corpus world composition end-to-end (no mocks): loaded
`CatalogRepository`/`WorldModuleRepository`, resolved
`data/content/world_compositions/frontier_living_world.yaml` via
`WorldAssemblyResolver.assemble()` (the same fixture path
`tests/integration/worldassembly/test_real_content_world_compositions.py` already exercises), then
called `WorldCompiler.compile(bundle.world_spec, seed=42, context=bundle.compile_context)` directly
— the real function, not a stub. Printed, per region: `RegionSpec.id`, whether it matched a
`region_declared_population` key (built by summing `PopulationSpec.count` by `pop_spec.
spawn_region`, mirroring `compiler.py:360-364`), and the resulting `RegionState.population_cohorts`.

**Result:**
```
PopulationSpec entries (15 total) span 6 spawn_region values:
  hometown(13), bandit_road(8), goblin_camp(9), old_mine(5), haunted_battlefield(6), wolf_den(5)

RegionSpec.id values (7 total): hometown, bandit_road, goblin_camp, old_mine,
  haunted_battlefield, near_forest, wolf_den

Key match: hometown=True, bandit_road=True, goblin_camp=True, old_mine=True,
  haunted_battlefield=True, near_forest=False (no PopulationSpec targets it), wolf_den=True

population_cohorts after compile():
  hometown: {young:4, adult:6, elder:3}       (13 total, 30/50/20 split, exact)
  bandit_road: {young:2, adult:4, elder:2}    (8 total)
  goblin_camp: {young:3, adult:4, elder:2}    (9 total)
  old_mine: {young:2, adult:2, elder:1}       (5 total)
  haunted_battlefield: {young:2, adult:3, elder:1}  (6 total)
  wolf_den: {young:2, adult:2, elder:1}       (5 total)
  near_forest: {}                             (0 declared — correct per _seed_population_cohorts'
                                                own declared_population<=0 -> {} guard, cited in its
                                                own docstring; NOT a seeding failure)
```

**Verdict:** `region_declared_population`'s `spawn_region` key space and `RegionSpec.id`'s lookup
key space **agree** for every region carrying any declared population in this real composition.
6 of 7 regions seed non-empty cohorts; the seventh's empty result is the documented zero-population
behavior, not evidence of the "never seeded" defect this ticket's premise claims. **This
corpus ticket's premise is false today.** Per the epic's AC-7, this is recorded as a fifth outcome,
not forced into `CONDITION` (there is no world-content gap — the composition *does* declare
population reaching every non-`near_forest` region) or `MISLABEL` (the registry's own description of
what the mechanism does is accurate; only its "never seeded" verdict is stale). Labelled
`STALE-PREMISE`, agreed with `rpg-feature-planning`.

Full verdict, evidence, and the filing-time provenance finding (this ticket was filed 3 weeks after
the fix that contradicts it shipped) are recorded directly in
`TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED.md`'s own Implementation
Notes / Completion Summary, per the epic's Deliverable 2.

**Independently reproduced by `rpg-feature-planning`, 2026-09-30, from their own worktree** (a
separate `WorldCompositionSpec.model_validate` → `WorldAssemblyResolver.assemble()` →
`WorldCompiler().compile(spec, seed=42, ...)` run against the same composition file): identical
per-region figures, including the exact `hometown` → `{young:4, adult:6, elder:3}` split; explicit
confirmation that "keys with no matching region id: `[]`" — the key-mismatch `DEFECT` branch is
disconfirmed, not merely unconfirmed. Verdict `STALE-PREMISE` is now independently reproduced, not
resting on one run.

**Caution from that same independent check, load-bearing, do not lose it in a re-read:**
`STALE-PREMISE` retires only the **seeding** claim — that `population_cohorts` starts non-empty.
It does **not** establish that `DemographicCycleService.process_demographics` fires *observably* —
that 200-tick cycles at the dataclass-default rates (`birth_rate=0.02`, `mortality_rate=0.01`,
`cohort.py:41-42`) actually move any cohort count by a visible amount. A 5,000-tick corpus run gives
only ~25 cycles; applied to counts of 5–13 (this composition's own seeded values), a 2% birth rate
per cycle may round to zero movement every single cycle. **This is unmeasured — recorded as an open
question, not claimed either way, and not something to fold into the `STALE-PREMISE` verdict above.**
Whether it deserves its own ticket is a scoping call for after this epic's `T01`/`T03`/`T04` finish
classifying the rest of the corpus, not decided here.

**Methodology note for the remaining 3 tickets in this pass** (from the same independent check):
several of `CAMP-STATE-NEVER-SEEDED`'s siblings cite `registries/mechanisms.yaml` verdicts dated
2026-09-16 — the same vintage as the verdict that just proved stale here. Treat a registry verdict
as **a claim to re-verify against code**, not as evidence, and record both the verdict's date and
the cited code's own last-commit date side by side. Likely the fastest path through `CAMP-STATE` in
particular.

### `camp` (`CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`) — verdict: `STALE-PREMISE` (AC-7), 2026-09-30

**Pass A of the follow-up dispatch, user-authorized via `rpg-feature-planning`.** Corrected framing
from that dispatch: only `CAMP-STATE` (not all 3 remaining tickets) cites a 2026-09-16
`registries/mechanisms.yaml` verdict, so the registry-dating method was applied here, not to the two
cognition tickets below.

**Experiment.** Compiled the same real composition already used for the cohort check
(`frontier_living_world.yaml`) and printed `state.camps` after `WorldCompiler.compile()`. Result:
**2 real `CampState` entries** — `goblin_camp_place` (`kind='goblin'`) and `wolf_den_nest`
(`kind='wolf'`), both fully constructed (real positions, `active=True`, `faction='hostile'`), not
placeholders. Root cause: two of this composition's own world modules
(`goblin_camp_conflict.yaml`, `wolf_den_near_forest.yaml`) declare `creature_kind` on a `CAMP`/`NEST`
`PlaceSpec` — the exact opt-in field `WorldCompiler.compile()`'s own camp-construction bridge reads.
`git log --follow` on both content files: the `creature_kind` declarations landed in `cb0b23b07`
(2026-09-08) — 8 days before the registry verdict (2026-09-16), 12 days before this ticket's own
filing (2026-09-20).

**Bonus finding, not asked for but load-bearing:** `docs/world/raid_boss_camp_contract.md`
(Certified/authoritative, `last_verified: 2026-09-04`) itself still states in prose "no content on
disk sets [`creature_kind`] today... `state.camps` remains `{}` for every currently-compiled world"
— true as of its own verification date, false since the very next content commit 4 days later. Not
corrected here (out of this epic's scope), only flagged in `CAMP-STATE`'s own ticket body for
whoever owns that doc.

**Verdict:** `STALE-PREMISE`, same shape and label as `demographic_cohort_cycle`'s own verdict —
full evidence and the filing-time provenance finding (routed to `agent-working-design`) recorded in
`TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION.md`'s own Implementation Notes.

### `CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` + `NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` — verdict: `UNDECLARED` (both), 2026-09-30

**Pass B of the same dispatch.** Neither ticket cites a `registries/mechanisms.yaml` verdict
(confirmed via direct grep — no entry exists for `capability_estimate`/`enemy_data`), so the
registry-dating method does not apply; verified each ticket's own claims directly instead, per
dispatch instruction.

**Checked `_ENEMY_DANGER` usage first, as instructed, before assigning any verdict.** Read
`src/cognition/capability_estimate.py:124-127` directly:
`enemy_info.get("danger_rating", _ENEMY_DANGER.get(enemy_id, 0.5))` runs on **every** combat
capability estimate, unconditionally. Since `enemy_info` is always `{}` (both tickets' own confirmed
finding), `_ENEMY_DANGER`'s fallback branch is the **live path taken 100% of the time** — it is not
itself dead or gated code. `CapabilityEstimateService.estimate()` is a real, called function
(`src/engine/tactical.py:405` → real tactical decisions) that fires correctly on every real combat
estimate, always using a generic per-species table instead of the per-entity learned data
`enemy_data`'s own field shape was built to accept. **This is the opposite of the epic's usual
corpus shape** (a mechanism that silently no-ops) — here the mechanism fires every time, just with
permanently coarser input than intended.

**`enemy_data` half → `UNDECLARED`, inherited from `NO-MECHANISM-RECORDS`, not independently
re-derived.** `CAPABILITY-CONTEXT`'s own Completion Summary already names the causal link: the
field's emptiness "isn't just unwired, no real mechanism anywhere in the codebase produces
per-enemy-kind danger data at all." A symptom does not get a separate verdict from its own named
cause. `NO-MECHANISM-RECORDS`'s own conclusion — "nothing declares this," reported for a user-level
design decision rather than built — matches the epic axis's operative test for `UNDECLARED` ("needs
a design decision before any code change") even though its root shape (zero declared producers) is
the adjacent-but-distinct case from the axis's literal "competing implementations" description;
recorded as a shape-mismatch-but-operative-fit, not silently rounded.

**`region_data` half → `UNDECLARED`, independently derived, different root shape from
`enemy_data`'s.** Re-confirmed directly: `RouteFamily.SCOUT_LOCATION` exists in the enum
(`schema.py:27`), the `mapper.py:41` `(ProjectKind, ObjectiveKind)` table, and `scoring.py`'s culture-
tag/goal tables (`:44,179,271`) — three separate type-level declarations of its shape and intent —
but `grep -n "RouteFamily\." src/domains/adventure/generator.py` shows every *other* generatable
family explicitly listed (`GATHER_RESOURCE`, `BUY_UPGRADE`, `CRAFT_UPGRADE`, `RECOVER`,
`ASK_INFORMATION`, `FORM_PARTY`, `DEFER_WITH_REASON`) with `SCOUT_LOCATION` present in **none** of
them. Not a guard/filter bug hiding a working branch (the epic's `DEFECT` shape) — there is no
branch to hide; the feature was scoped into three separate tables and never implemented in the one
place that produces route instances. Same `UNDECLARED` label as `enemy_data` via the same operative
test, but a genuinely different root shape (declared-and-scaffolded-but-unbuilt, vs.
`enemy_data`'s zero-declared-intent) — recorded separately so neither is assumed to explain the
other.

Full verdicts and evidence recorded in each covered ticket's own body:
`TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY.md`,
`TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER.md`.

**Not done, deliberately:** `NO-MECHANISM-RECORDS`'s own open AC-1 (a real design decision on
whether to build a combat-outcome-learning mechanism) and `CAPABILITY-CONTEXT`'s own `region_data`
design question are **not** resolved by this classification pass — this pass answers the epic's
reachability axis only, not either ticket's own underlying design question, which stays open for its
own owner.

## Test Summary
_(classification-only pass across all 4 covered tickets; no repo test suite authored or run.
Verification was standalone read-only scripts exercising `WorldCompiler.compile()` against real
content (cohort + camp experiments) plus direct code/content greps (cognition pair) — scripts kept
in this session's scratchpad, not committed, since they are one-off diagnostics, not repo tests.)_

## Files Changed
No `src/`/`tests/`/content change — read-only across all 4 sub-passes. `registries/mechanisms.yaml`
confirmed byte-for-byte unchanged against `origin/main` after every experiment. Files actually
touched, all ticket/artifact bookkeeping:
- This ticket: `tickets/todos/` → `tickets/inprogress/` → `tickets/done/`.
- `staging_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/` migrated to
  `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/` (`investigation.md`, `plan.md`,
  `test_plan.md`) at closure.
- `tickets/todos/TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION.md`,
  `tickets/todos/TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED.md`,
  `tickets/todos/TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY.md`,
  `tickets/todos/TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER.md` — each carries its own
  recorded verdict now, per the epic's Deliverable 2.
- `docs/REGISTRY.yaml` — regenerated unconditionally as part of Finalize's post-migration
  self-check, per this project's own standing convention; not a hand edit.

## Completion Summary
All 4 covered tickets now carry a verdict: `CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` =
`STALE-PREMISE`; `DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED` = `STALE-PREMISE`;
`CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` = `UNDECLARED` (split, two root shapes);
`NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` = `UNDECLARED`. Two `STALE-PREMISE` outcomes share one
shape (a registry verdict and a ticket both authored weeks after the shipped fix that contradicts
them); the two `UNDECLARED` outcomes share the "needs a design decision" operative test while
resting on two distinct root shapes (zero-declared-intent vs. declared-but-unbuilt) and are causally
linked to each other (one names the cause of the other's symptom) rather than independent findings.
No `CONDITION` verdict was reached for any of the 4 — this pass's own initial-scoping worry (the
epic's "never-seeded" grouping being only shape-level, not diagnostic, for the two cognition
tickets) held: neither actually fits the "world content never supplies the input" shape the rest of
the epic's corpus does. `registries/mechanisms.yaml` confirmed unchanged throughout. This ticket
(`T02`) itself is now fully classified and ready to close; the epic's own consolidated classification
document (Deliverable 1) is deferred to `T06` per this ticket's own Scope.
