---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED
phase: open
date: 2026-09-29
tags: [investigation, root-cause, corpus, world, cognition]
---

# TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED

## Title
Classification pass over the 4 never-seeded-precondition tickets (`camp`, `demographic_cohort_cycle`,
`CapabilityContext.region_data`/`enemy_data`, per-enemy-kind danger tracking)

## Status
OPEN

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
  compiled or procedurally-generated world today ever seeds `population_cohorts`." State explicitly
  which of the following is true, with evidence: (a) the premise is stale/already resolved by the
  08-31 fix (a candidate for the epic's AC-7 "resists classification" / already-fixed outcome,
  rather than a forced `DEFECT`/`CONDITION`); (b) the seeding code runs but no corpus world module
  actually declares a `PopulationSpec` targeting any real region, so `region_declared_population`
  is empty in practice — a genuine `CONDITION` (world-content gap), distinct from "never seeded" as
  a code-level claim; or (c) something else entirely. Do not assume either without checking a real
  compiled world's output.
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
- [ ] Each of the 4 covered tickets carries exactly one verdict from `DEFECT` / `CONDITION` /
      `UNDECLARED` / `MISLABEL`, **or** is recorded as a fifth "resists all four verdicts" outcome
      per the epic's AC-7 — never forced into the nearest bucket.
- [ ] Every verdict cites evidence per the epic's bar: a named zero-caller grep, a content fact (what
      a real compiled/procgen corpus world's composition does or does not contain), or tick
      arithmetic. A verdict supported only by re-reading the code, without checking real compiled
      output or content, is not accepted.
- [ ] `CAMP-STATE-NEVER-SEEDED` and `DEMOGRAPHIC-COHORT-CYCLE`'s verdicts explicitly reconcile
      against `TCK-20260831-POPULATION-COHORT-SEEDING`'s already-shipped compile-time seeding code
      (`src/worldbuilding/compiler.py`), stating clearly whether the "never seeded" premise still
      holds against a real compiled world, is stale, or points to an upstream content gap.
- [ ] Any `CONDITION` verdict among the 4 is split into corpus-run-length vs. world-content, each
      with a named owner, per the epic's AC-6.
- [ ] Each verdict is recorded in its own covered ticket's body, and this pass's findings are
      reflected in the epic's classification document under `docs/plans/`.
- [ ] `registries/mechanisms.yaml` is confirmed byte-for-byte unchanged (empty `git diff`) at
      completion.
- [ ] No `src/`, `tests/`, or content change lands as part of this ticket.

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

## Related Code Areas
- `src/core/state.py` (`CampState`)
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, `_seed_population_cohorts()`,
  `region_declared_population` — where the camp/cohort reconciliation evidence lives)
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
  Criteria) so it cannot be silently skipped.
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

## Test Summary

## Files Changed

## Completion Summary
