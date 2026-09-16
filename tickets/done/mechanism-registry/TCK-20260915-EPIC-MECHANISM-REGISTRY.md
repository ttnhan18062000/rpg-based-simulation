---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-EPIC-MECHANISM-REGISTRY
phase: done
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-EPIC-MECHANISM-REGISTRY

## Title
Mechanism Registry — one generated source for mechanism state, dependency, and verification, so the
brainstorm artifacts render from data instead of five hand-maintained surfaces

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The RPG brainstorm corpus records findings well and cannot answer aggregate questions — *what is
wrong, what should we harden, what is the priority, how do we know* — because no mechanism's state is
written down once. Three artifacts each maintain their own mechanism-state vocabulary by hand
(`rpg_feature_atlas.html`, `simulation_capabilities.html`, `rpg_simulation_wiring_map.html`), and
they already disagree: the atlas carries `orphan` (12 cards) and `gated` (7) — the
built-but-never-runs distinction this arc established — while the wiring map and capabilities page
each derive their own colouring/tier by hand, independently.

**Corrected 2026-09-16 by `TCK-20260915-ARTIFACT-STATE-CONVERGENCE`**: an earlier version of this
paragraph claimed *five* artifacts record mechanism state, including
`simulation_design_taxonomy.html` and `design_merit_scorecard.html`. That was wrong — those two
track genuinely different, independently-correct axes (a simulation-engine architecture-pattern
catalogue and design-idea merit scoring, respectively, neither keyed by mechanism id), found by
checking rather than assuming, after the original claim was itself reached by grepping the taxonomy
for a couple of guessed vocabulary words rather than reading what it actually tracks. See
`docs/plans/mechanism_registry_initiative.md` Finding 1 for the full correction and its own
methodology note.

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
4. **`TCK-20260915-ARTIFACT-STATE-CONVERGENCE`** — the three mechanism-domain artifacts (atlas,
   capabilities, wiring map) read `state` and `verified` from the registry, their hand-maintained
   duplicates removed; the two other artifacts (taxonomy, scorecard) are assessed and confirmed to
   track a genuinely different axis, recorded rather than converged.

## Out of Scope
- **Gap 2 (state-is-prose) as its own ticket.** It dissolves into child 2: the overloaded badge texts
  (`"Built correctly, OFF by default"`, `"Proven mechanic, narrow trigger"`) are verification
  statements in a build-status field, and migrate once the field exists.
- **New badge classes.** Six is enough. Expanding a status vocabulary to carry meaning belonging in
  another field is the same failure mode the atlas's own 147 overloaded badge texts already show.
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
- `docs/brainstorm/*.html` — the three mechanism-domain consuming artifacts (atlas, capabilities,
  wiring map); taxonomy and scorecard read for assessment only, not converged
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
Per child ticket. Combined suite across all four children: 135 tests in
`tests/unit/tools/ tests/unit/engine/test_capability_registry.py`, all passing, re-verified with
`graphify-out/` genuinely moved aside and restored at every child's own closure.

## Files Changed
None directly (epic) — see each child ticket's own Files Changed.

## Completion Summary
DONE. All four children closed: Foundation, Verification-Axis, Priority-Derivation,
Artifact-State-Convergence. The registry is the single generated source for mechanism `state`,
`layer`, `depends_on`, and `verified`; three real artifacts (atlas, capabilities, wiring map) render
from it; two (taxonomy, scorecard) are confirmed independent axes, not converged.

**What the registry measured about the artifacts it replaced** — real, quantified drift, not
hypothetical justification for building it:
- 2 stale atlas badges (a `gap` badge on real, tested code; a citation to a path `TCK-20260824`
  had already deleted).
- 4 of 24 mapped wiring-map nodes wrong — **17% drift** in one hand-maintained diagram, including
  `combat_engagement` still reading "GATED OFF by default" a day after it went live by default.
- 1 registry seeding error (`camp`) — found by this epic's own systematic cross-check, now the
  project's first real `contradicted` verdict (`state: done`, code correct and wired, but never
  observed working in any world).
- 1 wrong claim in the epic's own scoping document (`mechanism_registry_initiative.md`'s Finding 1)
  — "five artifacts record mechanism state" was really three; taxonomy and scorecard track
  genuinely different axes. Found the same way as the others: checking instead of assuming.

**What it established about the simulation itself:**
- 75 mechanisms seeded, corrected to 75 after catching an investigator subagent's own miscount
  (73) early in Foundation.
- 26 mechanisms are hubs (transitive dependents > 0); 49 are leaves (nothing depends on them,
  transitively).
- 7 of 75 have a recorded verification verdict as of this epic's close (up from 6 when the
  verification axis itself was built, +1 for `camp`'s own `contradicted` verdict found in this
  last child); **68 of 75 remain unverified**, rendered explicitly as such rather than omitted.
  Exactly **1 mechanism has runtime verification** (`combat_engagement`, via a real scenario run) —
  every other verified entry is `code_trace` (static, proves structure, not effect).

**The conclusion worth stating plainly**: every layer of this work produced a real, measured drift
error — the artifacts the registry was built to replace, the registry's own initial seed, and the
scoping document that justified building it in the first place. Each was authored carefully, by
people (and agents) actively checking their own work, and each was still wrong until an
independent, later check caught it. That is the strongest available evidence the underlying
problem — five (now three) independently hand-maintained surfaces drifting apart — is structural,
not a matter of anyone's individual care. It is the argument for this registry existing at all, not
just a retrospective justification.

**The cost, recorded honestly alongside the benefit, per peer review**: consolidating five surfaces
into one removes disagreement as an accidental safety signal. `commitment_betrayal`'s own
cross-doc disagreement (wiring map vs. atlas) was findable specifically *because* two independent
documents disagreed about it — that accidental safety is gone once there is only one source. The
verification axis (the 68-unverified, 1-runtime-verified figures above) is this epic's own
deliberate replacement for that accidental safety, not an incidental side effect — it is what now
has to carry the weight that document disagreement used to carry for free.

One follow-up filed, not folded in: `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT` —
re-read all 73 mechanism-mapped atlas cards' full descriptions (not just badges) for the same class
of caveat that produced `camp`'s own `contradicted` verdict, since `camp`'s own seeding read the
badge/title and missed a caveat sitting in the description. Explicitly the natural first real
producer for the verification axis at scale.
