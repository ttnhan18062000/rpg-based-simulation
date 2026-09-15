---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION
phase: open
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-MECHANISM-REGISTRY-FOUNDATION

## Title
The mechanism registry file, its schema, its validator, and the initial seed

## Status
OPEN

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

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
