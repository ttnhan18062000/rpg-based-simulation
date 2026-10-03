---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION
phase: open
date: 2026-10-02
tags: [architecture, documentation, simulation-quality]
---

# TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION

## Title
Epic: complete the semantic foundation to the bound owner decision 7 sets — registry bindings first,
then the rule map sliced by mechanism cluster, with a yield checkpoint that can stop it

## Status
EPIC_SCOPED

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
Owner decision 7 (2026-10-02, `docs/plans/systemic_world/owner_decision_memo.md` row 7) gates RPG
feature, balance and dormant-path parity work on a bounded semantic-foundation milestone. This epic
tracks that milestone. It implements no code directly.

**Row 7 is the only copy of the definitions of "hard RPG bug" and "complete" — this epic does not
restate them, and neither should its children.** Read row 7 first. The approved sequence is the work
order in `docs/plans/systemic_world/roadmap.md` §8 (owner, 2026-10-02); this epic covers its items
5, 6 and 7 only. Items 1-4 are the hard-bug queue and are tracked by their own tickets.

The scope bound exists because classifying all 172 catalog Rules was measured to be low-yield, not
unaffordable. Evidence, from this session's own measurement of the two finished slices:

| slice | Rules classified | defect tickets filed |
|---|---|---|
| M1 Territory (`TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE`) | 4 | **2** |
| M4 Combat/Conflict (`TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW`) | 10 | **0** |

Neither slice touched `src/`. Of the 14 resulting rows, **6 explicitly re-cite another row's
evidence**, so the 14 rows rest on 8 distinct derivations. 18 rule→mechanism edges cover **7 of 104**
mechanisms, and the 14 edge-bearing Rules are exactly the 14 classified ones.

## Scope
1. **Child A — world-definition split, FIRST.** `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`,
   with `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` merged **toward the older ticket**.
   It goes first because every later probe and rule-map slice gathers evidence by running worlds, and a
   world id that resolves to different module sets by entry point makes that evidence incomparable.
2. **Child B — registry bindings (row 7 (b)), BEFORE the rule map.** Each of the 25 core-tier modules
   `mechanism_registry_completeness_check` reports unbound is either bound via `implemented_by` or
   recorded as an exclusion with a reason. Includes registering `PerceptionGate`
   (`src/world/perception/gate.py`) as its own mechanism per owner decision 8 row 8, and the
   `MOTIVATION-DOCTRINE` entry retire/rename — both of those registry entries are drafted by
   `world-rule-catalog-design`, which owns `registries/mechanisms.yaml` content.
3. **Children C… — the rule map (row 7 (a)), sliced by MECHANISM CLUSTER**, 3-5 mechanisms per
   standard-tier ticket. For every mechanism carrying `implemented_by`, each catalog Rule that
   constrains it is classified in `registries/rule_classifications.yaml` with a
   `rule_mechanism_edges.yaml` edge behind the verdict, **or** the mechanism is recorded as constrained
   by no catalog Rule.
4. **Yield checkpoint after the first two rule-map slices.** Report defects found per mechanism. **If
   both slices read zero, re-scope before continuing** — this is a real stop condition, not a
   formality. See Assumptions.
5. Every child runs through the formal `implement-ticket` pipeline, per row 7 (c), so its cost is
   measured.

## Out of Scope
- Restating row 7's or row 8's definitions anywhere. One fact, one place.
- Classifying Rules that constrain no live mechanism. They stay unclassified and an absent edge still
  means `UNKNOWN` — a permanent, expected state per SCP `architecture.md` §7, never coerced to
  `MISSING`.
- The completeness check's **wider tier** (74 unbound mechanism-shaped classes, 21 cross-package
  referenced). Deliberately outside the definition because the tool reports that number as "a floor,
  not a ceiling", and a completion definition containing an unbounded set is unfalsifiable. It stays a
  tracked advisory.
- Ending SCP Stage D. This epic is a bounded milestone *inside* the continuing mapping; the mapping is
  expected to stay majority-`UNKNOWN` indefinitely. See the annotated non-goal in
  `docs/plans/simulation_semantic_control_plane/rollout_plan.md`.
- Feature implementation planning of any kind, which is what row 7 gates. Feature *design* in the
  catalog and roadmap may continue alongside.
- The hard-bug queue (work-order items 1-4), including the two bounded probes.

## Acceptance Criteria
- [ ] Child A has landed and a world id resolves to one module set regardless of entry point.
- [ ] Row 7 (b) holds: all 25 core-tier modules bound or excluded-with-reason, and
      `mechanism_registry_completeness_check` reports zero undispositioned core-tier modules.
- [ ] Row 7 (a) holds over every mechanism carrying `implemented_by`, by the definition in Scope 3.
- [ ] `tools/semantic_control_plane/registry.py` validates all three registries at each child's close.
- [ ] The yield checkpoint ran after the second rule-map slice and its numbers are recorded in this
      epic — **including if they were zero and the epic was re-scoped as a result.**
- [ ] Each child has a pipeline run record, so the programme's own cost is measurable. A
      hand-orchestrated close cannot carry wall-clock or tool-call cost by design, which is why row 7
      (c) exists.

## Related Tickets
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — child A (the older, owning ticket)
- `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` — to be merged into child A, not run separately
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — BLOCKED; decision 8 answered its design
  question, and registering `PerceptionGate` is child B's
- `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` — only its registry
  retire/rename remains; child B
- `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` (done) — M0-M4, the predecessor whose yield this epic's
  bound is derived from
- `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`, `TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT`
  — foundation-adjacent, not children; sequence after the above

## Related Docs
- `docs/plans/systemic_world/owner_decision_memo.md` — **rows 7 and 8, the only copy of the
  definitions**
- `docs/plans/systemic_world/roadmap.md` §8 — the approved work order
- `docs/plans/simulation_semantic_control_plane/architecture.md` §7 — `UNKNOWN` semantics, the
  172 × 93 framing
- `docs/plans/simulation_semantic_control_plane/rollout_plan.md` — Stage D, and the non-goal decision 7
  partly supersedes

## Related Stored Artifacts
- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/` — the one slice with usable cost
  telemetry (12 agents, 3169 s, ≥458 tool calls for 4 Rules; a floor, since 3 of 12 agents logged no
  tool rows)
- `stored_artifacts/TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW/` — 10 Rules, **no usable cost
  telemetry** (hand-closed, so `duration_s: 0` and zero tool rows, by design)

## Related Code Areas
- `registries/mechanisms.yaml`, `registries/rule_classifications.yaml`,
  `registries/rule_mechanism_edges.yaml`, `registries/mechanism_causal_edges.yaml` (0 rows, a
  documented correct outcome, not a gap)
- `tools/mechanism_registry/mechanism_registry_completeness_check.py` (needs `PYTHONPATH=.`)
- `tools/semantic_control_plane/registry.py` — the validator
- `docs/world_rules/` — the 172 catalog Rules

## Assumptions / Open Questions
- **Mechanism-anchoring narrows the scope but does not by itself fix the measured yield taper.** This
  is the epic's own main risk and it is stated here deliberately: run to completion without the Scope 4
  checkpoint and the programme has swapped "classify all 172 Rules" for a smaller but equally
  unfalsifiable commitment. The checkpoint is the control.
- Slicing by mechanism cluster rather than Rule family is an inference from the M1/M4 structure, not a
  measured result. M4 produced 10 Rules across seven families on 5 distinct derivations because they
  clustered onto `tactical_decision` and `combat_engagement` — i.e. the 1.75x paperwork multiplier
  appeared *because* slices were Rule-indexed while the evidence was mechanism-indexed. Worth
  re-testing at the first slice: if a mechanism-clustered slice still produces mostly re-citations, the
  inference was wrong.
- "93 mechanisms with `implemented_by`" is the count at decision time. Child B **changes it** — that is
  why (b) precedes (a). The target is the set as it stands when (a) starts, not 93 as a frozen number.
- Of the 25 core-tier modules, the tool says they are "not yet checkable, NOT asserted to be gaps", so
  an unknown fraction resolve to exclusions rather than bindings. Child B is therefore cheaper than 25
  bindings, by an amount nobody has measured.
- Whether a "classified, no code needed" child can reach `DONE` is **an open process question, not
  rhetorical**: `done_checker`'s `migration_complete` requires `plan.md`/`investigation.md`/
  `test_plan.md` in `stored_artifacts/`, and `## Status` offers no superseded-style value. It already
  blocked `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` from closing. Children that
  classify Rules without changing code may hit it. Owned by `agent-working-design`, not filed yet —
  waiting for a second instance so it arrives with evidence rather than one anecdote.

## Implementation Notes
_(epic — not implemented directly; children carry implementation)_

## Test Summary
_(epic — children carry their own tests)_

## Files Changed
_(epic — no direct changes)_

## Completion Summary
_(not started)_
