---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION
phase: done
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-MECHANISM-REGISTRY-FOUNDATION

## Title
The mechanism registry file, its schema, its validator, and the initial seed

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create the single hand-authored source for what simulation mechanisms exist, which layer each belongs
to, and what each depends on. Everything else in
`TCK-20260915-EPIC-MECHANISM-REGISTRY` builds on this file.

Two blocks — layers carry frequency, mechanisms carry dependency:

```yaml
layers:
  entity:  { cadence: per_tick, rank: 1 }
  faction: { cadence: daily,    rank: 3 }

mechanisms:
  - id: combat
    layer: entity
    depends_on: [movement, perception]
    state: done
```

`state` uses the atlas's existing six classes (`done`, `partial`, `gap`, `orphan`, `gated`,
`skeleton`) — not a new vocabulary. Those six already encode the built-but-never-runs distinction;
inventing a seventh is explicitly out of scope.

## Scope
1. **The registry file** — location alongside the existing generated index
   (`docs/brainstorm/`), YAML for hand-authorability.
2. **Seed it with real mechanisms**, ~30–50 expected. Derive from the wiring map's existing flowchart
   nodes and the atlas's layer sections rather than inventing a taxonomy; both already name the real
   systems.
3. **Validator** enforcing four invariants, wired into CI:
   - every `depends_on` id resolves to a declared mechanism,
   - the dependency graph is acyclic,
   - every `layer` is declared in the `layers` block,
   - every `state` is one of the six classes.
4. **`make` target**, registered alongside `brainstorm-idea-index`.
5. **Graphify cross-check (report-only)** — flag any declared `depends_on` edge with no supporting
   call/import path as suspicious. Report, never fail: graphify's 35k-node graph is advisory here.

## Out of Scope
- The `verified` block (child 2).
- Priority derivation and chart generation (child 3).
- Changing any artifact to read from this file (child 4).
- Auto-generating `depends_on` from code. Hand-authored; 30–50 nodes is human-scale.

## Acceptance Criteria
1. The registry file exists, is valid, and is seeded with the real mechanism set.
2. `depends_on` is the only hand-authored edge data — no stored dependent-count anywhere.
3. Frequency appears only on layers, never on a mechanism.
4. The validator fails on each of the four invariants, each proven by a test using a deliberately
   invalid fixture — **not** by a clean pass on valid input. A validator only ever run against good
   data is indistinguishable from one that does nothing.
5. The `make` target regenerates or validates without manual steps.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent
- `TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX` — the generated-index precedent

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` §3 — shape and invariants

## Related Stored Artifacts
- `stored_artifacts/TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX/plan.md`

## Related Code Areas
- `tools/generate_brainstorm_idea_index.py`
- `docs/brainstorm/idea_index.json`
- `Makefile`

## Assumptions / Open Questions
1. Real mechanism count once seeded — 30–50 is an estimate.
2. Whether mechanism ids should align to atlas card ids, wiring-map node ids, or stand alone. Leaning
   stand-alone with mappings added by child 4, so seeding is not blocked on reconciling 139 cards.
3. Whether the file belongs in `docs/brainstorm/` beside `idea_index.json` or in `registries/`.
   `registries/` is append-only allowlists and a mechanism registry must support edits, so
   `docs/brainstorm/` is the better fit — confirm against repo convention before committing.

## Implementation Notes
The strongest reason to enforce the validator from day one: a `depends_on` pointing at a renamed
mechanism fails silently, which is the exact defect family this arc spent weeks cataloguing. Build
the failure loud.

**Two stale source documents fixed before seeding** (seeding known-wrong data would propagate the
error into every future consumer at once): Breakthrough Bonuses was badged `gap`/stub in the atlas
and wiring map, but `BreakthroughService.apply_bonuses()` is real and called on every stat
recalculation from the production path (`progression/breakthroughs.py:36-58`, called from
`rpg_depth.py:367`) — fixed in `rpg_feature_atlas.html`, `rpg_simulation_wiring_map.html`, and
mirrored into `simulation_capabilities.html` per the standing atlas-sync rule. Race-Keyed
Evolution Chains cited a duplicate implementation already deleted by
`TCK-20260824-WIRE-ORPHANED-MECHANISMS`; collapsed to a single `done` mechanism.

**Real mechanism count is 75, not the 30–50 estimate** (Assumptions #1) — 71 atlas JSON cards
(`entity-action` through `beyond-city`, all 14 sections excluding `design-ideas`) + 2 net splits
(`aging_death`/`succession`, `xp_leveling`/`breakthrough_bonuses`) + 2 wiring-map-only additions
(`nest`/`lair`, which have no atlas JSON card at all — sourced from the wiring map's own separate
"Beyond the City" table). Seeded all 75, no curation, per peer review — every id carries a real
citation, and a mechanism missing from the registry is invisible, the exact failure this epic
exists to prevent. This investigation itself carried three separate inherited-but-unverified
numbers across roughly a day (73→75 mechanism count, a stale ~25/75 `depends_on`-density claim
corrected to the real 42/75, and the two stale atlas badges above) — each caught only by checking
the real source directly. Documented in investigation.md's own "This Document's Own Drift" section
as structural evidence for the registry's founding rationale, not a self-criticism.

**Assumption #2 (mechanism ids stand-alone, not aligned to atlas card ids) confirmed correct as
scoped** — ids are derived names (`combat_resolution`, `tactical_decision`, etc.), not literal
atlas card indices; card-index citations live only in investigation.md's provenance trail, not in
the registry file itself.

**Assumption #3 (file location) resolved: `docs/brainstorm/mechanisms.yaml`.** `registries/*.jsonl`
is documented as strictly append-only (managed via a `tools/*_registry.py add` CLI, never
hand-edited) — incompatible with a file that needs real hand-edits as mechanism state changes.
`docs/brainstorm/` is git-tracked, editable, and already houses `idea_index.json` (a related but
distinct generated-index precedent, not hand-authored the way this file is).

**`depends_on` density**: 42 of 75 mechanisms declare an outgoing dependency, but only 26 distinct
mechanisms are ever named as someone else's dependency (49 have zero dependents) — a small set of
real hub prerequisites (`action_pacing_readiness`, `regional_trauma_hazards_sovereignty`,
`combat_resolution`, `belief_cycle`, `betrayal_siege_war`, others) surrounded by leaves. This is
the expected shape of a real dependency graph, not a defect — flagged for T3 (priority derivation)
since `rank × dependents` will have layer rank doing most of the ordering work for the 49 leaves,
which is correct (small real blast radius), not a degradation.

**Two known placeholders, not blocking**: `race_collective_force` and `settlement_capacity_axis`
are seeded under `layer: faction` as the nearest organizational tier a real implementation would
likely live in — a guess, not a citation-backed placement, flagged inline via YAML comment for a
future layer-design ticket.

**Graphify cross-check real output**: 47 `depends_on` edges checked against `graphify-out/graph.json`
(38,139 nodes / 107,182 links), 9 supported, 8 suspicious, 30 no_match — many `no_match` results
are the token-subset matching heuristic correctly admitting it can't find a code symbol for a
given id phrasing (e.g. `action_pacing_readiness`) rather than falsely claiming support. Report-only,
never fails the build; wired as informational output appended after the hard-invariant `validate()`
call in `make mechanism-registry-validate`.

## Test Summary
`tests/unit/tools/test_mechanism_registry.py` (24 tests) + `test_mechanism_registry_graphify_check.py`
(6 tests) + regression check `tests/unit/engine/test_capability_registry.py` (9 tests, the imitated
pattern, unmodified) — 39/39 passing. Per Acceptance Criteria #4, all four validator invariants
proven failing on deliberately broken fixtures (unresolved `depends_on`, direct 2-node cycle, a
longer 3-node cycle so a pairwise-only check can't accidentally pass, undeclared layer, invalid
state), each fixture isolated to exactly one invariant, plus a parametrized test proving all six
valid states are individually accepted (the enum boundary is exact on both sides), plus a
valid-fixture canary using real seeded ids so the invalid-fixture tests are proven to be testing a
validator that *can* pass. `make mechanism-registry-validate` tested both against the real
committed file and against a `tmp_path` copy with an injected defect (never mutating the real file
in place). Regenerated `docs/brainstorm/idea_index.json` after the two atlas badge fixes; verified
the idea count stayed at 68 with no generator assertion failure.

Scoped pytest command used throughout:
```
.venv313/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_graphify_check.py tests/unit/engine/test_capability_registry.py -v
```

## Files Changed
- `docs/brainstorm/mechanisms.yaml` (new) — the registry, 75 mechanisms
- `tools/mechanism_registry.py` (new) — reader + validator
- `tools/mechanism_registry_graphify_check.py` (new) — report-only cross-check
- `tests/unit/tools/test_mechanism_registry.py` (new) — 24 tests
- `tests/unit/tools/test_mechanism_registry_graphify_check.py` (new) — 6 tests
- `Makefile` — `mechanism-registry-validate` target
- `docs/brainstorm/rpg_feature_atlas.html` — two stale badges corrected (Breakthrough Bonuses,
  Race-Keyed Evolution Chains)
- `docs/brainstorm/rpg_simulation_wiring_map.html` — same two corrections mirrored (BRK node +
  Buildup table row)
- `docs/brainstorm/simulation_capabilities.html` — Breakthrough Bonuses tier corrected
  (`built`→`live`), plain-language desc updated, per the standing atlas-sync rule
- `docs/brainstorm/idea_index.json` — regenerated (badge-text edits changed two
  `wiring_map_mentions` counts; both verified as expected, not regressions)
- `staging_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/` — investigation.md, plan.md,
  test_plan.md

## Completion Summary
DONE. Registry built and seeded with the real, citation-backed mechanism set (75, not the
estimated 30–50 — reported and decided with peer review before seeding). Validator enforces all
four invariants, each proven against a deliberately broken fixture, not just a clean pass. Two
stale source-document badges fixed before they could seed wrong data. Report-only graphify
cross-check shipped as a real, conservative first version rather than deferred. All out-of-scope
items (verified block, priority/chart derivation, artifact convergence, auto-derived depends_on)
correctly deferred to child tickets 2–4. `tests/unit/tools/` is already wired into the
"Unit · infra / observability" CI fast lane (verified directly against `.github/workflows/test.yml`
before considering this ticket closeable — no new CI-wiring gap, unlike an earlier ticket this same
session that added a brand-new top-level test directory).
