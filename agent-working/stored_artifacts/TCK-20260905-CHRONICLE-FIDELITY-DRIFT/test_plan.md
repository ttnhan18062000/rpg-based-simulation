---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-CHRONICLE-FIDELITY-DRIFT
artifact_type: test_plan
tags: [social, strategy]
---

# Test Plan — TCK-20260905-CHRONICLE-FIDELITY-DRIFT

## Regression Surface

**Unit:**
- `tests/unit/domains/culture/test_culture_deriver.py` — must pass unmodified (AC5: zero changes to
  `CultureDeriver`'s own read/write behavior).
- `tests/unit/domains/culture/test_culture_exporter.py` — must pass unmodified (exporter call-site
  precedent; new `FidelityExporter` must not alter `CultureDriftExporter`'s own behavior).
- `tests/unit/domains/chronicle/test_chronicle_compiler.py`,
  `tests/unit/domains/chronicle/test_significance.py`,
  `tests/unit/domains/chronicle/test_faction_chronicle.py` — must pass unmodified (Out of Scope:
  zero changes to `grouper.py`/`significance.py`).
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py`,
  `tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py` — must pass unmodified;
  `test_orchestrator_plan_wiring.py` is the direct precedent for calling `_advance_state()` directly
  in a test, reused for the new AC3 wiring test.
- `tests/unit/domains/campaigns/test_grief_urgency.py`, and any other `_advance_state()`-adjacent
  test — must still pass since `_advance_state()` gains one new call, matching the existing pattern
  of sequential exporter calls.
- `tests/architecture/test_clan_reputation_write_paths.py`,
  `tests/architecture/test_social_write_paths.py` — precedent source-text-guard tests; must remain
  green, confirming this ticket's new guard test follows the same `inspect.getsource()` + regex
  technique without disturbing these.

**Integration:**
- `tests/integration/culture/test_culture_drift_acceptance.py::test_two_regions_diverge_after_5_episodes`
  — must pass unmodified; the strongest existing proof that a Chronicle-derived Deriver-pattern
  sibling can coexist correctly at the same episode-boundary call site.

**Serialization / determinism:**
- Any existing `CampaignState.to_dict()`/`from_dict()` round-trip test — confirm the new
  `historical_drift` (or equivalently named) field does not break existing sorted-key serialization
  for `region_cultures`, `grief_urgencies`, `nemesis_relations`, etc.

## New Tests Required

- **`test_fidelity_lowers_with_era_distance`**
  Category: unit
  Verifies: AC1 — given a `ChronicleHierarchy` spanning ≥2 Eras, `FidelityDeriver.derive()` produces
  a strictly lower fidelity value for an event in an older Era than for an event in the current Era.
  Location: `tests/unit/domains/chronicle/test_fidelity_deriver.py` (mirrors
  `tests/unit/domains/culture/test_culture_deriver.py`'s `_hierarchy()`/`_entry()` helper pattern;
  needs ≥`ERA_EPISODE_MIN * 2 = 6` distinct episodes each with ≥1 chronicle-worthy event to force
  two real `Era` objects via `ChronicleGrouper`, not a single-era hierarchy).

- **`test_fidelity_derive_is_deterministic_byte_identical`**
  Category: unit
  Verifies: AC2 — calling `FidelityDeriver.derive()` twice with the same `ChronicleHierarchy` input
  produces byte-identical output (e.g. compare `repr()` or the `to_dict()` serialization of both
  results for exact equality, matching the "byte-identical" wording literally rather than only
  `==` on the dataclass, since `==` alone would not catch, e.g., non-deterministic dict key
  ordering surviving into a JSON round-trip).
  Location: `tests/unit/domains/chronicle/test_fidelity_deriver.py`.

- **`test_fidelity_exporter_runs_alongside_culture_drift_exporter_in_advance_state`**
  Category: integration (orchestrator wiring)
  Verifies: AC3 — `FidelityExporter.export()` is called from the same
  `CampaignOrchestrator._advance_state()` call site as `CultureDriftExporter.export()`. Follow
  `tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py`'s precedent of calling
  `orch._advance_state(final_state, summary)` directly with a synthetic `AuthoritativeState`
  containing chronicle-worthy world events, then assert both `campaign_state.region_cultures` and
  `campaign_state.historical_drift` (or equivalently named field) are populated after the single
  call — proving both derivers consumed the same `_hierarchy` local within one `_advance_state()`
  invocation, not two independently-triggered hooks.
  Location: `tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py` (new test appended) or a
  new `tests/unit/domains/campaigns/test_fidelity_wiring.py`.

- **`test_historical_drift_written_only_through_established_direct_mutation_pattern`**
  Category: architecture guard (source-text scan, `inspect.getsource()` + regex — same technique as
  `tests/architecture/test_clan_reputation_write_paths.py`)
  Verifies: AC4, resolved per this ticket's own Risks finding (the literal "`src/engine/patches.py`"
  requirement is unachievable against real precedent — Plan must confirm which requirement wording
  survives before this test is written; do not write a test asserting `patches.py` involvement that
  cannot pass against any real implementation of this ticket). Whatever the resolved requirement is,
  the test must assert `campaign_state.historical_drift[...] = ...`-shaped mutation occurs only
  inside the designated exporter method (e.g. `FidelityExporter.export`), not from any other
  call site — mirroring the "only from this one place" spirit of
  `test_clan_reputation_write_paths.py`.
  Location: `tests/architecture/test_fidelity_write_paths.py`.

- **`test_no_changes_to_belief_entry_knowledge_fact_or_culture_deriver`**
  Category: architecture guard (source-text scan)
  Verifies: AC5 — this ticket introduces zero changes to `BeliefEntry`, `KnowledgeFact`, or
  `CultureDeriver`'s own read/write behavior. Two parts: (1) a source-text/hash-stability check (or
  simply: `tests/unit/domains/culture/test_culture_deriver.py`'s full suite passing unmodified is
  the primary proof per AC5's own wording — no new test needed for that half beyond the regression
  run); (2) a guard confirming no new code path imports `BeliefEntry`/`KnowledgeFact` for write
  purposes (`inspect.getsource()` scan over the new `FidelityDeriver`/`FidelityExporter` modules for
  `BeliefEntry(` / `KnowledgeFact(` construction call patterns).
  Location: `tests/architecture/test_fidelity_write_paths.py` (co-located with the AC4 guard above).

- **`test_fidelity_carry_forward_round_trips_through_campaign_state_serialization`**
  Category: unit
  Verifies: not a literal AC line but required by the Durable State Rule and the Anti-Drift Hazard
  flagged in investigation.md (missed `to_dict()`/`from_dict()` wiring for the new field) — mirrors
  `test_exporter_round_trips_through_campaign_state_serialization` in
  `tests/unit/domains/culture/test_culture_exporter.py`.
  Location: `tests/unit/domains/chronicle/test_fidelity_exporter.py` (mirrors
  `tests/unit/domains/culture/test_culture_exporter.py`'s naming/structure).

- **`test_fidelity_deriver_no_engine_or_core_state_imports`**
  Category: architecture guard
  Verifies: the Mechanics/Engine Constraint that the new model/deriver modules must not import
  `src.engine` or `src.core.state` at module level (same constraint `CultureState` upholds) — a
  simple `ast`/source-text scan over the new module's top-level import statements.
  Location: `tests/architecture/test_fidelity_write_paths.py` or a dedicated
  `tests/architecture/test_fidelity_no_engine_import.py`.

## Scoped Pytest Commands

```
pytest tests/unit/domains/chronicle/ tests/unit/domains/culture/ tests/unit/domains/campaigns/ \
       tests/integration/culture/ tests/architecture/test_clan_reputation_write_paths.py \
       tests/architecture/test_social_write_paths.py -q
```

Add, once created:
```
pytest tests/architecture/test_fidelity_write_paths.py -q
```

Never `pytest tests/` — scope stays to the Chronicle/Culture/Campaigns domain plus the two
precedent architecture-guard files this ticket's own new guard test mirrors.

## Anti-Drift Test Guards

- `tests/unit/domains/culture/test_culture_deriver.py` and
  `tests/unit/domains/culture/test_culture_exporter.py` passing unmodified is itself the AC5 guard
  for `CultureDeriver` — any red here means this ticket accidentally touched the sibling it must
  leave alone.
- `tests/unit/domains/chronicle/test_chronicle_compiler.py`,
  `tests/unit/domains/chronicle/test_significance.py` passing unmodified guards against
  accidental changes to `grouper.py`/`significance.py`, which Out of Scope explicitly forbids.
- The new `test_no_changes_to_belief_entry_knowledge_fact_or_culture_deriver` guard
  (`tests/architecture/test_fidelity_write_paths.py`) directly catches any accidental import/write
  of `BeliefEntry`/`KnowledgeFact` from the new module — the exact scope-creep vector Out of Scope
  calls out by name.
- The new orchestrator wiring test (AC3) doubles as an anti-drift guard against a future refactor
  accidentally splitting `FidelityExporter.export()` and `CultureDriftExporter.export()` onto
  different call sites/cadences — both must always fire together from the same `_advance_state()`
  invocation.
- `tests/integration/culture/test_culture_drift_acceptance.py::test_two_regions_diverge_after_5_episodes`
  passing unmodified guards against any accidental interference between the new Fidelity write path
  and Culture Drift's own existing 5-episode acceptance signal, since both now run at the same call
  site in the same method.
