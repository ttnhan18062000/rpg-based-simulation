---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM
phase: open
date: 2026-09-29
tags: [investigation, root-cause, corpus, world, simulation-quality]
---

# TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM

## Title
Confirm the 2 wave-assessed verdicts + the 1 remaining scale/content ticket

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`T04` of `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`'s six-child sequence
(`SEQUENCE.md` item 4). Covers three tickets, but they are **not three open classification
questions** — only one is:

1. `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — verdict **already established** as
   `DEFECT` by `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` (PR #258, merge commit
   `35806b1ed`), J1. `apply_calamity_consequences()` has zero real callers anywhere in `src/`
   (`grep -rn "apply_calamity_consequences" src/` returns only its own definition and one unrelated
   comment in `src/world/displacement.py`). This ticket's job is to **record** that verdict + its
   evidence into the target ticket's own body, citing PR #258 — not re-derive it.
2. `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — verdict **already established** as
   `CONDITION` by the same wave, J2: `moon_cave` is spatially isolated (`grid_bounds` ~30 units from
   the nearest populated region in `generated_frontier_3_42`) from every hostile faction, confirmed
   on a fresh 5000-tick `Kernel.tick_once()` run (`moon_cave.trauma_score == 0.0` for the full run).
   Same "record + cite PR #258, don't re-derive" rule.
3. `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` — **not** part of the
   wave; needs a real classification pass against the epic's four-value axis, with evidence per the
   epic's evidence bar (a named zero-caller grep, a content fact, or tick arithmetic — reading the
   code alone does not count). This ticket sits inside a **different** epic's own sequence too
   (`tickets/todos/progression-starvation-chain/SEQUENCE.md` item 3): that epic already records the
   ticket's faction-chain half as **resolved** (2026-09-17 addendum on
   `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`: the posture-veto gate has no measurable
   effect on cross-faction volume in the worlds tested, because their real combat runs through the
   incidental `resolve_multi_attack()` path, which the gate does not touch) and only its **boss-gate
   half** as open. This ticket's classification pass covers the boss-gate half only, matching that
   epic's own framing — it does not re-litigate the resolved faction-chain half.

## Scope
- **Item 1 (record only)**: edit `tickets/todos/TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES.md`'s
  own body to carry the `DEFECT` verdict, its evidence (zero-callers grep), and a citation of
  `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` / PR #258 (`35806b1ed`), per the
  epic's own AC-3. Do not touch `registries/mechanisms.yaml` — that entry's registry write is
  already routed to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` (see Out of Scope).
- **Item 2 (record only)**: same treatment for
  `tickets/todos/TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES.md` — `CONDITION` verdict,
  spatial-isolation evidence, PR #258 citation. Note the wave's own assessment already found this
  ticket's registry label (`state: done`, `verified.verdict: contradicted`) accurate as-is — no
  registry correction is implied for this item.
- **Item 3 (real classification)**: a bounded reachability pass on
  `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE`'s **boss-gate half only**
  — does the posture-veto gate's real, measured attack-volume cut
  (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`) further starve the
  world-boss maturity gate's trauma-accumulation trigger
  (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s own already-thin trigger rate) past
  practical unreachability? Assign one of the epic's four verdicts (`DEFECT` / `CONDITION` /
  `UNDECLARED` / `MISLABEL`) or, if none fits, the fifth `RESISTS_ALL_FOUR` outcome per epic AC-7 —
  with evidence (a fresh measurement or tick arithmetic, not a re-read of the code) — and record it
  in that ticket's own body.
- Any combat-volume figure item 3 cites must be **re-measured live**, not cited from memory or from
  either predecessor ticket's own numbers — see Out of Scope and the epic's own hard constraint.
- Test the semantic-search tooling in this worktree as part of the mandatory context scan and state
  what was actually observed (see Assumptions / Open Questions) — do not assume the epic's own
  environment note (written from a different worktree) still applies here.

## Out of Scope
- **Fixing anything.** No code change lands under this ticket for any of the three items — items 1
  and 2 are ticket-body edits only, item 3 is a classification pass only.
- **Touching `registries/mechanisms.yaml`.** Byte-for-byte unchanged across this ticket, matching
  the epic's own scope guard (epic AC-4) and the wave's own guard. Item 1's `DEFECT` verdict is a
  recommendation only, already routed to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`,
  which owns that registry entry's `state` reconciliation — do not write it here.
- **Re-deriving or re-measuring items 1 and 2's own verdicts.** Both are already established by PR
  #258 with direct evidence (zero-callers grep for item 1; a fresh 5000-tick run for item 2). This
  ticket transcribes, it does not re-investigate.
- **Re-litigating the faction-chain half** of
  `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE`. That half is already
  resolved per `progression-starvation-chain/SEQUENCE.md` item 3 and
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own 2026-09-17 addendum — item 3's
  classification pass covers only the still-open boss-gate half.
- **Citing combat-volume numbers from memory.** Per the parent epic's hard constraint: these
  numbers moved twice already (`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`'s
  dispatch-discard finding, then `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`'s
  large drop, `crowded_frontier` −84.8%, `hero_guild_routing` −95.9%). Any reasoning about combat
  volume for item 3 must re-measure live, not cite either prior figure.
- **Reverting or weakening the posture-veto gate itself**
  (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`) as a "fix" — that gate is
  confirmed-correct behavior on its own merits and is not reopened by this ticket, matching the
  target ticket's own Scope guard.
- **T01's corpus-grouping citation of `CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`.** T01 lists that
  ticket by shape (zero-caller/dead-constant group) but does not classify it — this ticket owns the
  actual disposition. No coordination needed beyond what `SEQUENCE.md` already states; do not treat
  T01's listing as a competing classification.
- Any other corpus ticket in the epic's 14-ticket list — those belong to T01/T02/T03/T05.

## Acceptance Criteria
- **Maps to epic AC-1** (every corpus ticket carries exactly one verdict): items 1 and 2 each carry
  their already-established verdict (`DEFECT`, `CONDITION`) recorded in their own body; item 3
  carries exactly one verdict from the four-value axis (or the fifth `RESISTS_ALL_FOUR` outcome per
  epic AC-7) recorded in its own body.
- **Maps to epic AC-2** (every verdict cites evidence): item 1 cites the zero-callers grep result;
  item 2 cites the spatial-isolation measurement (region bounds + the fresh 5000-tick run); item 3
  cites either a fresh live measurement or tick/trigger-rate arithmetic — not code-reading alone.
- **Maps to epic AC-3, this ticket's own namesake AC** (the two wave-assessed tickets record the
  wave's existing verdict without re-investigation, and the classification doc cites PR #258 as the
  source): items 1 and 2's edits explicitly cite
  `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` and PR #258 (`35806b1ed`) as the
  verdict's source, and no fresh measurement is performed for either.
- **Maps to epic AC-7** (a ticket resisting all four verdicts is recorded as a fifth outcome, not
  forced into the nearest bucket): if item 3's boss-gate half does not cleanly fit `DEFECT` /
  `CONDITION` / `UNDECLARED` / `MISLABEL`, that is stated explicitly rather than forced.
- All three target tickets' own frontmatter remains otherwise valid
  (`python3 tools/validate_frontmatter.py <path>` passes) after the edits.

## Related Tickets
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — parent epic; this is its `T04` child.
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — item 1 (record only).
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — item 2 (record only).
- `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` — item 3 (real
  classification, boss-gate half only).
- `TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE` (closed, PR #258, merge commit `35806b1ed`) — source
  of items 1 and 2's already-established verdicts; specifically its child
  `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` (J1/J2).
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — owns item 3's other half (faction-chain,
  already resolved); its own `SEQUENCE.md` item 3 frames the boss-gate half as the only remaining
  open work on that ticket, matching this ticket's own scope split.
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — holds the 2026-09-17 addendum that
  resolved item 3's faction-chain half; cited, not reopened.
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (closed) — established the boss-gate's
  own pre-existing thin trigger rate; item 3's classification re-checks this under the posture-veto
  gate's new baseline.
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (closed) — created the attack
  volume reduction item 3 investigates the downstream effect of; not reopened.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` (open) — owns item 1's registry-side
  `DEFECT` write; this ticket only records the recommendation in the ticket body, does not write
  the registry.
- Sibling `T01` (not yet created as of this ticket's filing) will list
  `CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` in its own zero-caller/dead-constant corpus group by
  shape only — that is a grouping citation, not a competing classification; this ticket owns the
  actual disposition, per `unreachable-mechanism-classification/SEQUENCE.md`'s own T04 note.

## Related Docs
- `docs/mechanics/05_world_evolution.md` — calamity and regional-trauma laws (items 1, 2).
- `docs/mechanics/04_strategic_cognition.md` §13 — the posture-veto gate's own spec, cited by item
  3's target ticket as the behavior confirmed-correct and not reopened here.
- `docs/plans/deferred_tuning_decisions_register.md` (D-05) — cited by both item 1 and item 2's own
  target tickets as the register their eventual content-authoring fix candidates belong to.
- `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` — cited by item 3's target ticket;
  carries the cross-faction reachability investigation's own banner section.
- `docs/plans/world_composition_precondition_gap_finding.md` — the named pattern ("mechanics whose
  preconditions depend on unvalidated world composition") that items 1 and 2 both instantiate;
  directly supports the spatial-isolation/zero-composed-entity evidence being transcribed.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING/` — `investigation.md`,
  `plan.md`, `test_plan.md` for the wave that established items 1 and 2's verdicts.

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.apply_calamity_consequences()`,
  `CalamityPressurePropagator.propagate_seasonal()`) — item 1's evidence surface, read-only here.
- `src/engine/world_dynamics.py` (Death-triggered Trauma block, `CalamityService.process_world_dynamics()`)
  — item 2's evidence surface, and the trauma accrual item 3's boss-gate half depends on.
- `src/world/boss.py` (`BossService.check_for_boss_spawn()`, `BOSS_SPAWN_THRESHOLD`,
  `BOSS_SPAWN_TRAUMA_THRESHOLD`) — item 3's boss-gate mechanism.
- `src/domains/faction/diplomatic_state_machine.py`, `src/domains/faction/sentiment.py` — item 3's
  target ticket's own Related Code Areas for the (already-resolved, not reopened) faction-chain
  half; listed for completeness, not touched by this ticket's own scope.
- `tickets/todos/TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES.md`,
  `tickets/todos/TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES.md`,
  `tickets/todos/TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE.md` — the
  three ticket bodies this ticket edits.

## Assumptions / Open Questions
- **`layer: simulation`** was chosen to match the parent epic (`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`
  uses `layer: simulation`), confirmed registered via `python3 tools/layer_registry.py list`
  ("Simulation-quality scoring, calibration, and full-run behavior work"). The `world` layer is
  also registered and arguably closer to the two calamity/trauma items individually, but the
  ticket spans a world item (1, 2) and a combat item (3) under one classification-pass umbrella —
  `simulation` (matching the parent epic's own choice for the same reason) was preferred over
  forcing a single-subsystem layer onto a cross-cutting ticket.
- **`## Type: chore`** was chosen to match the parent epic's own Type, per the task's own guidance:
  items 1 and 2 are pure recording (no investigation, no repair), and item 3 is a classification
  pass rather than a code repair — none of the three items produces a behavior change, so `repair`
  (the type `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` used for the analogous
  wave assessment) was considered but not used, since that precedent ticket also proposed and
  landed four new regression-pinning tests, which this ticket's scope does not.
- **Environment note — semantic search tooling, tested directly in this worktree, not assumed from
  the epic's own note**: the epic's Assumptions section states both semantic-search paths were dead
  in the planning worktree (`m2-idea43-temporal-note`). Tested directly here
  (`m2-foundational-systems-tickets`, branch `unreachable-mechanism-classification`) during this
  ticket's own creation: `mcp__knowledge-search__search_docs` returned real, ranked results for a
  query on this exact topic (calamity/trauma/boss-gate reachability) — it is **live and working in
  this worktree**, contrary to the epic's own note, which was written from a different worktree.
  `graphify query` also ran successfully (returned a real, if topically noisy, traversal). Whoever
  picks up this ticket should rely on both tools directly rather than assume either is dead.
- **Open**: whether item 3's boss-gate half, once re-measured, comes out `CONDITION` (matching its
  sibling item 2's spatial/thin-trigger-rate shape) or something else is not pre-judged here — the
  epic's own disconfirmed shared-root-cause hypothesis means this must be checked, not assumed by
  analogy to item 2.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
