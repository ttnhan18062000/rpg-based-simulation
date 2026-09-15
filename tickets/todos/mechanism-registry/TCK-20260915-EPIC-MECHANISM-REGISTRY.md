---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-EPIC-MECHANISM-REGISTRY
phase: open
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-EPIC-MECHANISM-REGISTRY

## Title
Mechanism Registry — one generated source for mechanism state, dependency, and verification, so the
brainstorm artifacts render from data instead of five hand-maintained surfaces

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The RPG brainstorm corpus records findings well and cannot answer aggregate questions — *what is
wrong, what should we harden, what is the priority, how do we know* — because no mechanism's state is
written down once. Five artifacts each maintain their own state vocabulary by hand
(`rpg_feature_atlas.html`, `simulation_design_taxonomy.html`, `simulation_capabilities.html`,
`rpg_simulation_wiring_map.html`, `design_merit_scorecard.html`), and they already disagree: the
atlas carries `orphan` (12 cards) and `gated` (7) — the built-but-never-runs distinction this arc
established — while the taxonomy has no vocabulary for it at all, so all 50 of its rows read as at
least partly working.

Four gaps were raised together. One dissolves into another, so this epic delivers **one registry and
four child tickets**, not four parallel features. Full investigation, measurements, and rejected
alternatives: `docs/plans/mechanism_registry_initiative.md`.

Scope was set by investigation, not assumption. Three things were checked and changed the plan:

- **The generated-index pattern already exists** — `docs/brainstorm/idea_index.json`, built by
  `tools/generate_brainstorm_idea_index.py` via `make brainstorm-idea-index`. Follow it rather than
  inventing a parallel mechanism. It is keyed by *design idea* (68 proposals); this registry is keyed
  by *mechanism* (implemented reality) — different node sets, so a sibling file, not an extension.
- **The chart half is ~70% pre-built** — the wiring map already has three mermaid flowcharts with
  subgraph lanes and a `classDef live`/`classDef bug` state vocabulary. Charting is a generation
  problem, not a design problem.
- **Two planned features were cancelled by evidence.** All 19 atlas file citations resolve on
  `origin/main`, so no link checker is warranted; and the execution census is *binary branch
  coverage*, so it cannot supply execution frequency (frequency became a layer attribute instead).

## Scope
Four child tickets, in `SEQUENCE.md` order:

1. **`TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`** — the YAML registry, its schema, the validator
   (ids resolve, graph acyclic, layers declared, states in-vocabulary), the `make` target, and the
   initial seed of real mechanisms. Everything else depends on this.
2. **`TCK-20260915-MECHANISM-VERIFICATION-AXIS`** — the `verified` block (instrument, verdict, date,
   note), one row per mechanism, plus the rule that an unverified mechanism renders visibly rather
   than being omitted.
3. **`TCK-20260915-MECHANISM-PRIORITY-DERIVATION`** — derived priority (layer rank × computed
   dependent-count) and per-view mermaid generation, replacing the wiring map's hand-authored charts.
4. **`TCK-20260915-ARTIFACT-STATE-CONVERGENCE`** — the five artifacts read `state` and `verified`
   from the registry; their hand-maintained duplicates are removed.

## Out of Scope
- **Gap 2 (state-is-prose) as its own ticket.** It dissolves into child 2: the overloaded badge texts
  (`"Built correctly, OFF by default"`, `"Proven mechanic, narrow trigger"`) are verification
  statements in a build-status field, and migrate once the field exists.
- **New badge classes.** Six is enough. Expanding a status vocabulary to carry meaning belonging in
  another field is how the taxonomy reached 50 uniformly-healthy-looking rows.
- **Merging artifact prose.** Only `state` and `verified` converge; each page keeps its own writing.
- **A citation/link checker** — measured as unnecessary.
- **Auto-derived dependency edges** — graphify is a validator, not a generator, at 35k nodes.
- **Blocking on the execution census.** All four children stand alone; the census adds an
  exercised/never-exercised flag once PR #205 lands.

## Acceptance Criteria
1. A single registry file is the only hand-authored source of mechanism `state`, `layer`,
   `depends_on`, and `verified`.
2. Dependent-count and priority are computed, never stored.
3. The validator fails the build on an unresolvable `depends_on`, a cycle, an undeclared layer, or an
   out-of-vocabulary state.
4. Every mechanism appears in the verification view, including those with no verdict, shown as
   `unverified`.
5. No artifact retains an independent hand-maintained copy of mechanism state.
6. Charts are generated per view; no all-mechanisms diagram is produced.

## Related Tickets
- `TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX` — the generated-index precedent this follows
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` — open, unrelated to this epic

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` — investigation, measurements, rejected alternatives
- `docs/plans/mechanic_verification_scenarios_proposal.md` — the verification axis's main producer
- `docs/plans/simulation_execution_census_initiative.md` — the branch-coverage instrument

## Related Stored Artifacts
- `stored_artifacts/TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX/` — generator shape and its own
  cross-document anchor-resolution findings

## Related Code Areas
- `tools/generate_brainstorm_idea_index.py` — the pattern to mirror
- `docs/brainstorm/*.html` — the five consuming artifacts
- `Makefile` — target registration alongside `brainstorm-idea-index`

## Assumptions / Open Questions
1. Whether `flowchart BT` lays subgraphs out as clean lanes — the wiring map uses `TB`/`TD`/`LR`, and
   it is unknown whether `BT` was avoided deliberately.
2. How existing mermaid blocks render (client-side script vs committed images).
3. The real mechanism count once seeded. The 30–50 estimate is unverified; nearer 100 makes per-view
   slicing more important, not less.
4. Whether the atlas's 139 cards map cleanly onto mechanism ids, or many-to-one with a remainder.

## Implementation Notes
Epic tier — scope only, no direct implementation. Children carry their own plans.

## Test Summary
Per child ticket.

## Files Changed
None (epic).

## Completion Summary
Open.
