---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-FACTION
artifact_type: test_plan
tags: [simulation-quality, faction, world, corpus, calibration]
---

# Test Plan — TCK-20260710-SIMQ-DEPTH-FACTION

## N/A Framing

Investigation resolved UQ-1 definitively: **no genuinely uncovered, tier-appropriate FACTION
candidate world remains in the 17-world corpus** (see `investigation.md`'s "UQ-1 Resolution").
Scope items 2-8 of the ticket (candidate selection, content authoring, recalibration, grade-anchor
updates, corpus-wide regression sweep, doc/parity updates) have no valid target and should not be
executed. This test plan is therefore scoped to two things only: (1) the regression surface that
would need to stay green *if* the Plan phase somehow still authorizes content authoring against
this investigation's recommendation, and (2) guard tests that would catch any accidental drift if
someone later (mistakenly) adds `faction_tension_overrides` to a tier-inappropriate world. No new
tests are required for the "close as already-satisfied" path, since no code or content changes
would occur.

## Regression Surface

If the Plan phase overrides this investigation and proceeds with content authoring anyway, these
existing tests must keep passing (grouped by domain, all confirmed present on disk):

**Unit — Pattern-6 plumbing (schema/compiler/resolver), unaffected by any world-content change:**
- `tests/unit/worldbuilding/test_worldspec_schema.py::test_faction_spec_initial_tension_level_defaults_to_zero`
- `tests/unit/worldbuilding/test_worldspec_schema.py::test_faction_spec_initial_tension_level_round_trips`
- `tests/unit/worldbuilding/test_worldspec_schema.py::test_faction_spec_initial_tension_level_out_of_range_rejected`
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_seeds_faction_tension_from_spec`
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_seeds_full_faction_roster_at_zero_tension_by_default`
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_no_factions_declared_yields_empty_factions_dict`
- `tests/unit/worldassembly/test_assembly.py::test_faction_tension_overrides_applied_after_merge`
- `tests/unit/worldassembly/test_assembly.py::test_no_faction_tension_overrides_matches_current_behavior`
- `tests/unit/worldassembly/test_assembly.py::test_faction_tension_overrides_unknown_faction_raises`
- `tests/unit/worldassembly/test_assembly.py::test_faction_tension_overrides_out_of_range_raises`
- `tests/unit/faction/test_diplomacy.py::test_urban_political_seeded_tension_fires_tense_transition`
  (and the full `test_diplomacy.py` module — FAC-004/005/006/007 coverage)

**Unit — corpus-wide invariants that any world-content change could disturb:**
- `tests/unit/worldassembly/test_corpus_diversity.py` (full module — `EXPECTED_DISTINCT_POPULATED_FACTIONS`,
  `ANCHORED_WORLD_BANDS` population-stability membership, `test_population_stability` for every
  corpus world including the 6 tier-purity worlds)
- `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` (world-scoped,
  ON-flag population floor for `hero_guild_routing` specifically — must stay green untouched since
  this world is confirmed out of scope)

**Integration — arena/faction-campaign scenarios:**
- `tests/integration/scenarios/test_faction_campaign.py` (full module — FAC-010/011 territory
  transfer, war exhaustion)

**SimQ grade regression:**
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` subset) — must show 0
  regressions for the 11 already-covered worlds' anchors; since no new world is being authored, no
  new anchor entries are expected.

## New Tests Required

**None** — per the AC map below, every acceptance criterion in the ticket presupposes a selected
candidate world, and investigation found zero legitimate candidates. Restating the AC list for
traceability:

| Acceptance Criterion | Status given UQ-1 resolution |
|---|---|
| Re-verified candidate list of 2-3 archetype-appropriate worlds | Produced — the list is empty (0 candidates), with the stale-premise gap fully reconciled in `investigation.md` |
| Each selected world has >=2 non-zero `faction_tension_overrides` entries | N/A — no world selected |
| Each selected world compiles with 0 warnings, >=60% alive floor | N/A — no world selected |
| Each selected world's FACTION grade moves off `C` | N/A — no world selected |
| `make evaluate` full corpus sweep exits 0 | N/A — no content change to sweep; if the Plan phase wants a confirmatory no-op sweep to prove closure doesn't regress anything, that is a Plan-phase decision, not a new test artifact |
| `docs/parity_ledger/faction.yaml` FAC-012 extended | N/A — no new evidence world to add; FAC-012 already documents 2 data points (`urban_political`, `frontier_marches`) and remains accurate as-is |
| `eval_matrix_results.md`/`corpus_tier_taxonomy.md` updated | Recommend a small closure note only (documenting that Phase 3's FACTION half was found already-satisfied), not new grade tables — a Plan-phase doc-update decision, not a test |
| Newly-discovered engine bug filed separately | N/A — no engine bug found; Pattern-6 plumbing confirmed correct and unmodified |

If the Plan phase instead chooses to author a formal "coverage complete" closure note into
`eval_matrix_results.md` or `corpus_tier_taxonomy.md`, no new test is needed for a documentation-only
change — the existing `docs/` structure has no automated content-accuracy test beyond the manual
investigation-time cross-check this document performed.

## Scoped Pytest Commands

For regression verification only (no content change is being made, so this is a confirmatory
sweep, not a pre-change/post-change diff):

```bash
# Pattern-6 plumbing (schema/compiler/resolver) — confirms no accidental drift
pytest tests/unit/worldbuilding/test_worldspec_schema.py tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_assembly.py -v

# Faction domain (diplomacy state machine, siege, war exhaustion)
pytest tests/unit/faction/ -v

# Corpus-wide diversity/population-stability invariants (covers all 17 worlds, including the 6 tier-purity worlds)
pytest tests/unit/worldassembly/test_corpus_diversity.py tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -v

# Integration faction campaign scenarios
pytest tests/integration/scenarios/test_faction_campaign.py -v

# SimQ fast grade-anchor regression
pytest tests/simulation_quality/test_grade_regression.py -v
```

Never: `pytest tests/` (unscoped). `make evaluate`/`make evaluate-full` full-corpus sweeps are not
warranted for a no-content-change closure — reserve them for if/when the Plan phase actually
authorizes content authoring against this investigation's recommendation.

## Anti-Drift Test Guards

These existing tests are the load-bearing guards against the specific scope-creep this
investigation explicitly warns against:

- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability` (parametrized
  across all corpus worlds via `ANCHORED_WORLD_BANDS`) — would catch any accidental population-floor
  regression if `crowded_frontier`/`resource_dense_basin` were mistakenly given
  `faction_tension_overrides` content that destabilizes their carefully-isolated scale/composition
  variable.
- `tests/unit/worldassembly/test_assembly.py::test_faction_tension_overrides_unknown_faction_raises`
  — guards against a future mistaken attempt to seed tension for a faction not actually populated in
  a given world (the exact "copy-pasted from another world's values" anti-pattern
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`'s precedent warns against).
- `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` — the sole authoritative
  ON-flag evidence for `hero_guild_routing`'s AGENCY isolation; if this ticket's scope were
  mistakenly expanded to add FACTION content to `hero_guild_routing`, this test's framing
  (AGENCY-only isolation) would need re-justification, which is a signal this ticket must not touch
  that world.
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`) — would catch any
  unintended grade drift in the 11 already-covered worlds if a future change (this ticket's or
  otherwise) accidentally touched shared catalog content (e.g.
  `data/content/social/faction_relationships.yaml`, explicitly out of scope per the ticket's Out of
  Scope section) that FACTION scoring depends on.
