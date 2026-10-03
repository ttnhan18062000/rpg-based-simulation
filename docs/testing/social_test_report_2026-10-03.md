---
status: active
layer: testing
authority: P2
audience: agent
tags: [testing]
---

# Social test report — Phase 2 batch (2026-10-03)

The single findings document for the Phase 2 social batch
(`docs/plans/test_architecture/phase2_social_scale_out.md`). Every figure names the full `origin/main` SHA
it was measured at. Nothing here edits, moves, marks or strengthens an RPG feature test (owner
constraint, 2026-10-03), and `party*.py`, `src/systems/social_systems/memory.py`, `src/domains/perception/`
and dormant paths are excluded.

**Staleness line (all sections).** Measurements of `relationships.py`, `appraisal.py` and
`consequence_events.py` go stale when `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` lands.

Sections: 1 scenario gap (C1, below), 2 locate (C2), 3 oracle map (C3), 4 mutation summary (C4), 5 batch
review (after C4). Sections 2 to 5 are added by their own tickets.

## 1 · Scenario gap and lane routing (`TCK-20261003-SOCIAL-LANE-ROUTING-CASE-AND-SCENARIO-GAP`)

Measured at `origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6`, 2026-10-03.

**Routing.** `PERF_RE` (read from `.github/workflows/test.yml`) omits `src/systems/`. A change touching only
`src/systems/social_systems/**` therefore matches the scenario-lane trigger set and not `PERF_RE`: the
classifier returns `run=True` and the dedicated `Scenario lane` job covers it, with `Perf / cert / arena`
not running for it. This is pinned by one rule-level case,
`tests/unit/tools/test_scenario_lane_paths.py::test_src_systems_social_only_routes_to_the_dedicated_job`
(27 tests in the file pass). That case is **rule-level evidence, not a CI observation**: no PR touching
only `src/systems/social_systems/**` has been observed in CI. Positive control: with `src/systems|` added
to a scratch copy of the `PERF_RE` string, the social path matches it, so the case's `perf is False`
assertion would fail; the live pattern does not match.

**Scenario gap.** `tests/mechanic_scenarios/` holds no social mechanic scenario. Searched: every file
under `tests/mechanic_scenarios/` for imports of `social_systems`, and for the words `social`,
`relationship`, `reputation` and `appraisal`. Result: 0 imports of `social_systems`. Three files mention social
data, none the system code: `test_combat_judgement_withdrawal.py` (a `faction_relationships.yaml`
docstring mention), `test_combat_death_trace_encounterability.py` (uses `src.core.social_constants` and
sets `trust_history` on the entity's social component) and
`test_succession_heir_selection_value_differential.py` (uses `src.core.models.social.SocialBond` as input
to succession). They exercise other systems that read social state, not `src/systems/social_systems/`. So
the lane's scenarios give a social-only change no check of the social systems today. Writing a social scenario is
out of scope for this batch and is routed to `rpg-feature-planning` as a gap.
