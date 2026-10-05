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
1. **Child A — world-definition split, FIRST.** `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`.
   It goes first because every later probe and rule-map slice gathers evidence by running worlds, and a
   world id that resolves to different module sets by entry point makes that evidence incomparable.

   **Merge done, 2026-10-03.** `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` is folded into the
   older ticket and its file removed from `agent-working/tickets/todos/`; the surviving ticket carries
   its measurement-validity framing and three new ACs (6, 7, 8). Child A is now **one ticket, raised
   P2 → P1**, and is ready to dispatch. Three further gaps were found while merging and are in its
   Scope: live code **writes** into the directory being retired
   (`src/worldgeneration/generator.py:536`), `docs/guides/content_authoring.md` §4 still **teaches**
   that path, and an attribution both tickets carried was wrong — the ADR does not name the catalog
   path as the anomaly, so AC-8 **amends** the ADR rather than citing it.
2. **Child B — registry bindings (row 7 (b)), BEFORE the rule map.** Each of the 25 core-tier modules
   `mechanism_registry_completeness_check` reports unbound is either bound via `implemented_by` or
   recorded as an exclusion with a reason. Includes registering `PerceptionGate`
   (`src/world/perception/gate.py`) as its own mechanism per owner decision 8 row 8, and the
   `MOTIVATION-DOCTRINE` entry retire/rename — both of those registry entries are drafted by
   `world-rule-catalog-design`, which owns `registries/mechanisms.yaml` content.
3. **Child B2 — the "executes" vs "has an effect" instrument, ALONGSIDE child B and BEFORE the rule
   map.** `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP`, moved from parked feature
   into this foundation scope by the owner on **2026-10-03** (`roadmap.md` §8 work-order item 6
   addendum). **Sequencing was left to the planner; it is placed here, alongside (b) and before (a),
   2026-10-03.** The reason it cannot wait until after the rule map: a rule-map verdict that can only
   show a mechanism *runs* will record it as realised even when it changes no world state, so every
   slice taken before this instrument exists **overstates what is realised** and would need redoing.
   Three measured instances already exist, none of them inferred:
   - `FactionInfluenceService` — ~230 calls, **zero** ownership writes;
   - the region-owner `-1` sentinel path — reachable, **never reached**;
   - the world-clock raid — **12 of 12** raiders inert (memo row 9).

   `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` is a **fourth instance of the same
   shape** and is in the hard-bug queue, not this epic: `PANIC_RETREAT` fired 62–591 times per raider
   while parking every one of them outside the world. It is a usable validation case for this
   instrument, not a child of it.
4. **Children C… — the rule map (row 7 (a)), sliced by MECHANISM CLUSTER**, 3-5 mechanisms per
   standard-tier ticket. For every mechanism carrying `implemented_by`, each catalog Rule that
   constrains it is classified in `registries/rule_classifications.yaml` with a
   `rule_mechanism_edges.yaml` edge behind the verdict, **or** the mechanism is recorded as constrained
   by no catalog Rule.
5. **Yield checkpoint after the first two rule-map slices.** Report defects found per mechanism. **If
   both slices read zero, re-scope before continuing** — this is a real stop condition, not a
   formality. See Assumptions.
6. Every child runs through the formal `implement-ticket` pipeline, per row 7 (c), so its cost is
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
- [ ] Child B2's instrument exists and can distinguish "executes" from "has an effect" on at least the
      three measured instances in Scope 3, **before the first rule-map slice is taken.** A slice taken
      without it is not accepted as complete.
- [ ] Row 7 (a) holds over every mechanism carrying `implemented_by`, by the definition in Scope 4.
      Every verdict of "realised" rests on an effect, not only on a call count.
- [ ] `tools/semantic_control_plane/registry.py` validates all three registries at each child's close.
- [ ] The yield checkpoint ran after the second rule-map slice and its numbers are recorded in this
      epic — **including if they were zero and the epic was re-scoped as a result.**
- [ ] Each child has a pipeline run record, so the programme's own cost is measurable. A
      hand-orchestrated close cannot carry wall-clock or tool-call cost by design, which is why row 7
      (c) exists.

## Related Tickets
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — child A (the older, owning ticket)
- `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` — **merged into child A 2026-10-03 and removed
  from `todos/`;** git history holds it. Do not re-file
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — **child B2**, moved into this scope by
  the owner 2026-10-03; sequenced alongside child B, before any rule-map slice
- `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` — **not a child.** A fourth measured
  instance of the "executes without effect" shape, usable as a validation case for child B2's
  instrument. It belongs to the hard-bug queue and carries its own rule-owner ruling
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
- `agent-working/stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/` — the one slice with usable cost
  telemetry (12 agents, 3169 s, ≥458 tool calls for 4 Rules; a floor, since 3 of 12 agents logged no
  tool rows)
- `agent-working/stored_artifacts/TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW/` — 10 Rules, **no usable cost
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
- ~~Whether a "classified, no code needed" child can reach `DONE` is **an open process question**~~
  **RESOLVED — the mechanism already exists, 2026-10-03.** A child that classifies Rules without
  changing code closes with the **`## Disposition`** pair, not by fabricating staging artifacts:
  `## Disposition` holds one bare value of `STALE-PREMISE` / `NO-MECHANISM` / `DUPLICATE` /
  `SUPERSEDED` / `WONT-DO`, and `## Disposition Rationale` is prose that must cite a commit SHA, a
  `file:line`, or fenced run output. With both valid and no `src/` change attributed to the ticket,
  `done_checker_static.py`'s `migration_complete` passes without
  `plan.md`/`investigation.md`/`test_plan.md`.
  - Built by `TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES`. Enum at
    `tools/ticket_field_values.py:57`; waiver at
    `tools/gate_checks/done_checker_static.py:1071` (`_disposition_migration_result`); guide at
    `docs/guides/delivery_process.md:77`. `grep -A1 '^## Disposition$' agent-working/tickets/done/*.md`
    lists every existing use.
  - **The trap that made this look unresolved, worth knowing before repeating it:** `## Disposition`
    is a **separate body section, not a `## Status` value**, by design. Checking the `## Status` enum
    and finding no superseded-style value there says nothing about whether a retirement path exists.
    This epic's note asserted the gap on exactly that reasoning, and so did a 2026-10-03 session that
    deleted a duplicate ticket outright rather than closing it — corrected, and the ticket is now at
    `agent-working/tickets/done/TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS.md` as a
    `DUPLICATE` closure.
  - **Still to check, not assumed:** whether
    `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — recorded above as blocked from closing
    for this reason — can now close as a disposition. Its blocker was plausibly this same stale view,
    but that is untested.

## Implementation Notes
_(epic — not implemented directly; children carry implementation)_

## Test Summary
_(epic — children carry their own tests)_

## Files Changed
_(epic — no direct changes)_

## Completion Summary
_(not started)_
