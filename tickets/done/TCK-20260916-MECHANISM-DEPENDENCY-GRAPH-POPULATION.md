---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION

## Title
Populate the mechanism registry's `depends_on` graph — 26 of 75 mechanisms are isolated, so
foundational systems score priority 0 and vanish from the ranked view

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
User feedback on the published priority view: it looks like it only contains new features, missing
`movement`, `combat`, `interaction`, `stats`, `attributes`, `buildings`. All of these ARE present
as registered mechanisms (`movement`, `combat_resolution`, `attributes_biology`, `derived_stats`,
`interaction_channeling`, `buildings_town_services`) — the seed isn't missing them. The perception
is correct for a different, real reason.

**Measured, confirmed independently before acting** (not taken on peer's report):
```
declare no depends_on:            33 / 75
never named as anyone's dependency: 49 / 75
isolated (both, i.e. priority 0):  26 / 75
mechanisms naming `movement` as a dependency: 0
```
`priority = layer weight × transitive dependents`. An isolated mechanism scores exactly 0 and falls
out of the top-25 ranked view entirely — the foundational systems are IN the registry and INVISIBLE
in the output, because nothing in the hand-authored graph names them as a prerequisite. `movement`
is the clearest case: 0 dependents despite combat requiring adjacency (the combat-judgement
scenario had to force it explicitly), adventure routing needing it, and party cohesion radius
needing it.

## Scope
1. For each of the 26 isolated mechanisms, determine real `depends_on` edges FROM code (what
   depends on it, i.e. who should name it), not guessed. `depends_on` means "requires to exist in
   order to function" — not tick execution order, not containment, not lifecycle transition. Those
   are three separate axes (see `mechanisms.yaml`'s own header comment) the registry deliberately
   does not capture; converting them into `depends_on` would produce a confident, wrong graph.
2. `movement` specifically must end this ticket with real, cited dependents — the proof case.
3. Every one of the 26 isolated mechanisms gets a decision: real edges added (cited), or an
   explicit recorded note explaining why it genuinely has none (a root like `world_generation` may
   legitimately have no prerequisites — but it should have dependents; note that distinction).
4. Use `tools/mechanism_registry_graphify_check.py` (already built, report-only) as corroboration —
   a declared edge with no supporting call/import path in the real code graph is worth a second
   look before committing it, not committed on citation alone.
5. Reconsider whether the priority view's top-25 truncation is still the right cut once the graph
   is fuller — record the decision either way.

## Out of Scope
- Building the combined all-75/verified+priority view — sequenced explicitly AFTER this ticket by
  peer review, since generating it from an under-populated graph would publish numbers already
  known to be wrong. Separate ticket.
- Re-deriving containment, execution-order, or lifecycle edges — explicitly a different axis, not
  this registry's job (see `mechanisms.yaml`'s own "THREE AXES" header comment).
- Calibrating layer `weight` again — settled by `TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED`.

## Acceptance Criteria (stated as outcomes, not edge counts — not gameable by bulk-adding edges)
1. `movement` has real, cited dependents. If it is still 0 afterward, the pass failed.
2. Each of the 26 isolated mechanisms has a decision on record: edges added (cited to real
   call/import paths), or a recorded note explaining a genuine absence.
3. The ranked priority view stops omitting foundational systems — confirmed by regenerating it and
   checking directly, not assumed.
4. The graphify cross-check is run against every new edge before committing it; any edge it flags
   as unsupported is investigated, not silently kept.
5. The top-25 truncation question is explicitly decided and recorded, not left as an unexamined
   default.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent epic (closed; this is a post-close follow-up)
- `TCK-20260915-MECHANISM-PRIORITY-DERIVATION` — built the priority formula and the graphify
  cross-check tool this ticket reuses
- `TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED` — fixed the weight direction; this ticket
  fixes the other half of why foundational mechanisms don't surface (the graph itself, not the
  formula)

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` §"THREE AXES" — the containment/execution-order/
  dependency distinction this ticket must not blur

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md` — the original,
  deliberately-sparse (~25 of 75 rows) `depends_on` seed this ticket extends

## Related Code Areas
- `docs/brainstorm/mechanisms.yaml`
- `tools/mechanism_registry_graphify_check.py` (corroboration, reused not rebuilt)
- `docs/brainstorm/mechanism_priority_view.md`, `tools/generate_mechanism_priority_view.py`,
  `tools/generate_mechanism_charts.py` (top-25 cut)

## Assumptions / Open Questions
- Whether every one of the 26 isolated mechanisms genuinely has real dependents in the current
  codebase, or some are real roots/leaves with no dependents yet (e.g. a mechanism whose consumers
  haven't been built) — resolved per-mechanism during investigation, not assumed uniformly.

## Implementation Notes
12 real, cited edges added (see investigation.md for the full table). `movement` (the proof case)
went from 0 dependents/priority 0 to 2 direct dependents (`combat_resolution`, `party_formation`),
14 transitive dependents, priority 70 — now #1 (tied) in the ranked view, having previously been
completely invisible. `entity_role`, `personality`, `campaigns`, `inventory_trade_conservation`,
`status_effects`, `skill_unlocks`, `diplomacy`, and `world_generation` all gained their first real
dependent, resolving 8 more of the 26. `crafting`, `equipment_scoring`, `cross_episode_grief_nemesis`,
and `adventure_routing`'s own upstream edges resolved 4 more mechanisms' own `depends_on` (though
these 4 don't themselves gain dependents from this pass — a separate, correctly-distinguished
question from whether their own upstream dependencies are now recorded).

Two edges were explicitly investigated and ruled OUT despite looking plausible from the atlas's own
citation grouping (`crafting` does not use `EntityRole`; `motivation_doctrine`'s own module has zero
real callers per its own docstring, superseded by `adventure_routing`'s scoring) — recorded as
findings in their own right, not silently dropped.

Graphify cross-check run against the full new edge set: 6 of 13 new edges independently supported
by the tool's own 3-hop BFS; 3 flagged suspicious but kept on the strength of a direct,
line-level primary-source citation (stronger evidence than the tool's own conservative heuristic,
reasoning recorded in investigation.md); 4 landed in the tool's own documented non-defect
`no_match` bucket.

The remaining 14 isolated mechanisms each get a recorded reason (investigation.md's own table) —
mostly explained by genuinely gated/gap/orphan/skeleton state (no real code exists yet to have
dependents) or a directly-checked absence of any plausible consumer. `social_contracts` is flagged
honestly as the one shallower check in the set, not overclaimed as exhaustive.

Top-25 truncation: kept as-is for this ticket's own focused "verify next" view — the graph fix
itself resolves the visibility problem, and the truncation question properly belongs to the
separately-sequenced complete all-75 view (queued next, per peer review).

## Test Summary
139 tests in the scoped suite, all passing, re-verified with `graphify-out/` genuinely moved aside
and restored. One pre-existing hardcoded transitive-dependent-count fixture
(`test_transitive_dependents_matches_real_data`, `action_pacing_readiness`: 23→24) updated with an
explanatory comment — a real, expected consequence of `party_formation`'s own new `movement`
dependency (movement already depended on `action_pacing_readiness`, so `party_formation` became a
new transitive dependent), not a defect.

## Files Changed
- `docs/brainstorm/mechanisms.yaml` — 12 new `depends_on` edges across 8 mechanisms
  (`combat_resolution`, `combat_engagement`, `adventure_routing`, `party_formation`,
  `cross_episode_grief_nemesis`, `crafting`, `equipment_scoring`, `regional_trauma_hazards_sovereignty`)
- `docs/brainstorm/mechanism_priority_view.md` — regenerated; `movement`/`personality`/
  `tactical_decision` now tied at #1
- `tests/unit/tools/test_mechanism_priority_derivation.py` — one hardcoded fixture count corrected
  with explanation
- `staging_artifacts/TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION/` — investigation.md,
  plan.md, test_plan.md
- `docs/REGISTRY.yaml` — regenerated (Finalize's own post-migration self-check)

## Completion Summary
DONE. The dependency graph's real problem wasn't the priority formula (already fixed by
`TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED`) — it was that 26 of 75 mechanisms were
graph-isolated, so foundational systems the user correctly expected to see (`movement`, and by
extension anything depending on it) scored exactly 0 and vanished from the ranked view entirely.
Populated 12 real, individually-cited edges (never invented — each backed by a direct source-code
citation, corroborated where possible by the graphify cross-check, with two plausible-looking edges
explicitly investigated and ruled out rather than force-fit), resolving 12 of the 26 isolated
mechanisms including `movement` itself (the explicit proof case: 0→14 transitive dependents,
priority 0→70, now #1). The remaining 14 each have a recorded, mechanism-specific reason rather than
being left as an unexamined gap. Sets up the next two queued deliverables (the complete all-75
verified+priority view, then the generated HTML page) on a properly-populated graph rather than one
known to under-report priority.
