---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM
phase: open
date: 2026-09-17
tags: [architecture, documentation, schema]
---

# TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM

## Title
Introduce the tiers above `mechanism` — `system` derived from a declared root, `axis` as a declared
cross-cutting tag — so path-level questions become answerable

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The registry is a graph — 89 nodes, 65 declared edges, validated acyclic — and graphs support path
questions the current single-tier model cannot answer.

**The motivating question: "does combat work?"** No mechanism's verdict says. `combat_engagement` is
runtime-verified; `combat_resolution`, `tactical_decision`, `perception` and `trauma` are all
unverified. One node is green and the path is unknown. That question is asked constantly in planning
and is currently unanswerable from the registry.

Three tiers, each a different kind of thing:

| Tier | What it is | How membership is decided |
|---|---|---|
| **axis** | a dimension of play, roughly a game sub-genre — spatial, temporal, knowledge-belief | **declared tag**, overlapping, not derivable |
| **system** | a functional grouping — combat, progression, trade | **derived** from a declared root |
| **mechanism** | the existing registry node | already defined |

## Scope

### 1. `system` — declare a root, derive the members

```yaml
systems:
  - id: combat
    root: combat_resolution     # members = its transitive ancestors
```

One hand-authored line per system. Membership falls out of `depends_on`, so adding an edge updates
it for free. **Declared membership lists are forbidden** — that would be another hand-maintained
surface, the failure class the registry epic spent eleven tickets removing.

Overlap is expected and correct: `combat_resolution` belongs to both `combat` and `progression`,
because it feeds `xp_leveling`. That falls out of the graph rather than needing resolution.

### 2. `axis` — a declared, overlapping tag

An axis is **not a subgraph.** A spatial axis cuts across movement, perception, combat and region;
nothing in the dependency graph knows those share a dimension of play. So it is hand-declared, a
mechanism (or system) carries several, and there is no derivation to lean on.

**State that plainly at the point of definition**, because it means axes are the one tier with no
mechanical backing — systems derive from edges, mechanisms bind to code, axes rest on judgement
alone. That is acceptable when stated and dangerous when forgotten.

### 3. Rollups report counts, never a badge

A system shows *combat — 6 mechanisms, 1 verified, 0 runtime end-to-end*. **Never a single status.**

This is the ticket's most important constraint. A rolled-up badge reading "combat: partial" would
conceal that 5 of 6 members are unverified — and the verification axis exists precisely so that
unverified renders visibly rather than being summarised away. A summary badge would rebuild the
atlas's failure one tier higher.

### 4. Wiring — what this reuses, feeds, and completes

This tier must not arrive as standalone machinery. Every part of it attaches to something already
built or already queued.

**Reuses (build almost nothing new):**

- **System derivation is a function that already exists.**
  `tools/mechanism_registry/generate_mechanism_priority_view.py` already implements ancestors-of
  traversal for its chart views. A system's membership *is* that traversal from a declared root —
  call it, do not reimplement it.
- **Rollup counting is the verification view's existing logic**, grouped by system instead of by
  evidence class. Not new machinery.
- **The generated HTML page and markdown views** gain a section, produced by the same generators via
  the same `--target` flag. No new publishing path.

**Feeds (makes queued work better targeted):**

- **`TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`** — currently "bind more of the
  remaining 63" with no ordering. A system rollup turns that into *"combat: 2 of 6 bound"*, so
  coverage can be driven to completeness on the systems that answer real questions rather than
  spread thin across all 89.
- **The "verify next" ranking** becomes filterable: *what should I verify next in combat?* — a
  question actually asked in planning, answerable for free once membership derives.
- **`TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION`** — a changed file can be reported
  against the systems it belongs to, not just the mechanism, which is the granularity a reviewer
  reasons at.

**Completes (this is the point):**

The change taxonomy in `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` classifies
proposals at the **mechanism** tier — Introduce, Extend, Wire, Tune, Split, Retire, Interpose. But
real proposals arrive at the **axis** tier ("introduce a spatial axis"). Without the middle tier
there is no route from one to the other.

With all three, a proposal decomposes:

```
axis proposal  →  which systems it touches  →  per-mechanism changes, each classified
```

That is the answer to the original question — *given an idea write-up, how many mechanisms does it
introduce, extend, or merely tune?* The tiers supply the decomposition; the taxonomy supplies the
classification; the registry diff makes the claim checkable after it lands.

## Out of Scope
- **Declared membership lists for systems.** Root plus derivation only.
- **Deriving axes.** Not possible from the dependency graph; do not fake it with heuristics.
- **A fourth tier.** Three is what the evidence supports.
- **Retrofitting every mechanism into a system or axis.** Start with the systems that answer real
  questions; unassigned mechanisms are a visible gap, not an error.

## Acceptance Criteria
1. `system` membership is derived from a declared root; no membership list exists in the schema.
2. A system rollup reports member counts by verification state and never a single aggregate status.
3. `axis` is declared, may overlap, and its lack of mechanical backing is stated where it is defined.
4. At least one real system (`combat` suggested) answers the motivating question end to end.
5. A mechanism belonging to no system or axis renders as unassigned rather than being omitted — same
   rule as `unverified`.

## Related Tickets
- `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` — **blocks this.** See Assumptions.
- `TCK-20260917-EPIC-MECHANISM-VERIFICATION`
- `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md`
- `docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md` and the
  social-relationship, legacy-memory and temporal axis proposals — existing axis-level design docs,
  which this tier would connect to the registry

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/generate_mechanism_priority_view.py` — already implements ancestors-of
  traversal, which is the derivation a system needs

## Assumptions / Open Questions
1. **Blocked on the identity rules.** Node boundaries are still accidental — inherited from atlas
   cards and directory structure, with no stated rule for what one mechanism is. A tier built on
   accidental boundaries propagates the accident and makes it harder to see. Do not start this until
   `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` has landed.
2. **The base layer is thin** — 26 of 89 bound to code, 14 with any verdict, 2 runtime-verified.
   Abstraction above a thin layer tends to obscure the thinness rather than expose it, which is why
   AC #2 forbids summary badges.
3. Whether a system's root should be a single mechanism or allow several is unresolved. `combat`
   works from one root; `economy` may not.
4. Whether axes attach to mechanisms or to systems is unresolved. Attaching to systems is fewer
   declarations; attaching to mechanisms is more precise. Decide with a real case.
5. **A real limitation of derived membership, found 2026-09-17 while resolving
   `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`.** The `combat` system's own worked
   example (§1: `root: combat_resolution`, members = transitive ancestors via `depends_on`) derives
   membership from the *declared* graph — `tactical_decision → combat_resolution` is a real,
   declared edge. But direct instrumentation found real combat in three corpus worlds runs
   overwhelmingly through `movement`'s own opportunity-attack mechanic
   (`CombatResolutionSystem.resolve_multi_attack()`, 181-2177 calls per 1000 ticks), not through
   `tactical_decision`'s own decision-driven path (0-2 calls) — even though `movement` is also
   already a declared `depends_on` edge of `combat_resolution`. **A derived system's membership is
   only as true as its declared edges say, and a declared edge does not say how much real traffic
   flows through it.** `combat`'s own rollup (AC #2's per-mechanism-state counts) would correctly
   show `tactical_decision` as unverified/dormant if `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-
   CHANGE-TAXONOMY`'s own registry updates land first — but the system tier itself has no way to
   surface *which declared edge dominates in practice*, which is exactly the kind of fact this
   investigation's own registry updates had to record as prose on `combat_resolution`'s `verified`
   block, not as anything the graph structure itself exposes. Record this as a stated limitation
   when this ticket is built, not discovered again later: derived membership answers "is this part
   of the system," never "is this how the system actually gets used."

## Implementation Notes

### Naming — decided with evidence, recorded so it is not relitigated

`system` was chosen over `cluster` and `circuit` after checking the repository rather than assuming:

- **`cluster` — rejected.** 70 occurrences in `src/` alone, and it names a real concept: statistical
  clustering in `observability/mining/patterns.py` (`domain_clusters`, anomalies segregated by
  category), anomaly triage, chronicle grouping. A **semantic** collision.
- **`circuit` — rejected.** `short-circuit` in `engine/phase_graph.py`'s dirty-set logic, plus
  circuit-breaker usage in alert sinks. Also semantic.
- **`system` — chosen.** Its only conflict is with the directory `src/systems/`, a code-layout
  artifact that was never 1:1 with anything — mechanisms already map across both `src/domains/` and
  `src/systems/`. It is also the standard game-design term for the tier below a genre, so it needs no
  translation in conversation.

Also rejected: `domain` (`src/domains/`), `capability` (`simulation_capabilities.html`,
`registries/capability_envelope_registry.jsonl`), `feature` (`feature_packs`, `feature_flags.py`),
`pillar` (SimQ), `group` (an existing registry `layer` value), `loop` — which would contradict the
registry's own validated acyclic invariant.

Namespace the registry field and add a one-line note distinguishing it from `src/systems/`.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
