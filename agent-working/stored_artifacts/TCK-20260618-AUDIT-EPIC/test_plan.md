# TCK-20260618-AUDIT-EPIC — Test Plan

This is an audit epic. "Tests" are success criteria for each audit dimension: what
constitutes a completed, trustworthy audit of that dimension.

---

## General Completion Criteria (all dimensions)

A dimension audit is `done` when:
1. A detail file exists at `docs/audits/D{NN}_{slug}.md`
2. The detail file contains: dimension profile, rating method, feature/finding table,
   key findings, and follow-up dimension links
3. State is updated to `done` in `docs/audits/audit_dimensions.md`
4. The child ticket is moved to `tickets/done/`

---

## Dimension-Specific Criteria

### D03 — Behavioral Emergence Quality
- Run at minimum 500 ticks with `seed=42` standard world
- Record: entity survival rate at tick 100, 300, 500; economy equilibrium (resource
  balance at tick 500); quest completion count; social event count (party formations,
  betrayals, reputation changes)
- Classify behavior as: emergent (varied patterns per entity), mechanical (all entities
  converge to same loop), or stagnant (world stops changing after N ticks)
- Document specific evidence of emergence or failure to emerge

### D04 — Balance & Tuning
- Same run data as D03 (coordinate or reuse)
- Record: average entity lifespan; distribution of routes chosen over 500 ticks;
  resource abundance vs. scarcity ratio; time-to-first-death; XP accumulation curve
- Flag any parameter that produces degenerate outcomes (entities die within 10 ticks,
  entities never die, one route dominates >80% of decisions)

### D05 — Entity Differentiation
- Requires D03 complete
- Compare behavioral profiles across at least 3 entity classes and 2 seed values
- Differentiation confirmed if: different classes show statistically different route
  distributions; different OCEAN profiles produce different dominant behaviors at tick 500
- Differentiation failed if: all classes converge to identical route distribution

### D06 — Long-Run Simulation Health
- Run at minimum 2000 ticks with `seed=42` standard world
- Record: alive entity count over time (is it stable, growing, or collapsing?);
  regional resource availability trend; strategy shift count per 100-tick window
- World is "healthy" if: entity population stabilizes, resources fluctuate rather than
  monotonically depleting, at least 2 strategy shifts detected per 100-tick window

### D07 — Content Depth & Variety
- Enumerate content catalog: count item types, recipe chains, entity class definitions,
  quest kind enum values, world module definitions, biome types
- Define "minimum interesting variety" thresholds and check against them
- Flag content gaps that would cause simulation homogeneity

### D08 — Multi-Scenario Consistency
- Requires D03 complete (establishes what "good" looks like)
- Run D03's behavioral quality check across 3 different world configs and 3 seeds
- Consistency confirmed if all 9 runs classify as "emergent" using D03 criteria
- Document which world configurations produce lower-quality behavior and why

### D09 — System Wiring & Integration
- For every `[E]` feature in D02, locate the call site that invokes it from the live pipeline
- Track: does it reach `Kernel.tick_once()`, `WorldDynamicsSystem.resolve_dynamics()`,
  or `AuthoritativeState` apply path on a live run?
- Document any `[E]` feature that is only exercised in unit tests and never in a live tick
- Produce an updated status table: `live`, `test-only`, or `unreachable`

### D10 — Test Coverage & Regression Risk
- Run `pytest --co` and map test files to source modules
- Identify modules with zero direct test coverage
- For each `[P]` feature in D02, confirm whether a regression test exists
- Produce: covered/uncovered table by module, list of P0 behaviors with no test

### D11 — Dead Code & Orphaned Modules
- Use static analysis (import graph, call graph) to identify source files with no callers
- Cross-reference with D09 wiring findings — a module with no live callers is a candidate
- Produce: list of files to remove or archive, estimated line count, risk classification

### D12 — Pattern Consistency
- Check all 14 domain packages against: read-only contract (no direct state writes),
  typed result records usage, content family extension pattern for any new families
- Sample 3–5 domains for pattern deviation
- Produce: compliant / deviating classification per domain

### D13 — Type Safety & Validation Boundary
- Search for `Any` usage on public interfaces (`grep -rn ': Any'` in `src/api/`)
- Search for external input handling that bypasses `pydantic` or similar validators
- List all API route handlers and confirm they pass through schema validation

### D14 — Coupling Depth
- Look for shared constants (`src/core/constants.py` or equivalent), shared enums used
  across domain boundaries, shared config objects
- Identify cases where data model coupling creates implicit cross-domain dependencies
  even when import coupling is clean
- Produce: coupling inventory with severity (cosmetic / structural / architectural)

### D15 — Entity Decision Inspection Tooling
- Define the inspector task: "Find out why entity E chose route R on tick T"
- Attempt the task using current tooling only (no code changes allowed during audit)
- Rate the current experience: immediate (< 1 min), moderate (1–10 min), difficult
  (10+ min), impossible (no path exists without code changes)
- Document what tooling exists and what is missing

### D16 — Scenario & Content Authoring DX
- Count files that must change to add: one new world module, one new item type,
  one new entity class, one new quest kind
- Attempt to write a minimal world module from scratch and document errors encountered
- Rate error message quality: clear / misleading / silent

### D17 — Documentation Currency
- Read `docs/engine/known_limitations.md`, `docs/mechanics/` chapters 01–06,
  `docs/engine/kernel.md`, `docs/engine/authoritative_pipeline.md` against current code
- For each doc: confirm a sample of 3–5 claims against source code
- Flag any claim that contradicts current source as `stale`
- Produce: staleness table per doc file

### D18 — CI / Release Pipeline Completeness
- Map the path from: code change → test run → certification harness → release artifact
- Identify manual steps in this path (steps not automated)
- Confirm: does the certification harness cover the full scenario matrix defined in
  `src/certification/scenarios.py`? Is there a version artifact produced?
- Produce: complete / gap-with-workaround / blocked classification per pipeline stage
