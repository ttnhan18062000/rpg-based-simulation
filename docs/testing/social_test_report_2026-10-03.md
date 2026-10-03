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
out of scope for this batch; the gap will be routed to `rpg-feature-planning` together with section 3's findings (not yet sent).

## 2 · Locate: coverage, markers, placement (`TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING`)

Measured on branch `test-arch-phase2-social-children` at `f13baaf24578eb4529948f4e7e045c8468ca6886`, which is
`origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6` plus one tooling test case (C1) that is outside
every selection below. Date 2026-10-03. Findings are recorded only: no test was edited, moved, marked or
deleted, and the coverage files were written to a scratch path, not the repo.

### 2.1 Selections

| Selection | Files | Tests | Result |
|---|---|---|---|
| `tests/unit/social` | 33 test files (34 entries in the directory, counting `__init__.py`) | 296 | 296 passed, 12.45 s |
| Social tests elsewhere: the 20 files outside `tests/unit/social` that import `src.systems.social_systems` (3 `tests/architecture`, 3 `tests/integration`, 6 `tests/simulation_quality`, 8 `tests/unit` under `combat`, `core`, `domains/faction`, `engine`, `observability`, `strategic`) | 20 | 76 | with the above: 372 passed, 47.65 s |

The 20 elsewhere-files are found by import, not by subject, so several are not social-domain tests (2.4).
The plan names `tests/simulation_quality`, `tests/architecture` and `tests/integration`; the `tests/unit`
files outside `tests/unit/social` are an addition found by the same import search. The selections run
party tests too; party files are excluded only from the findings below.

### 2.2 Line coverage of `src/systems/social_systems/` (coverage.py 7.16.1, `--source`, line coverage not branch)

Command: `COVERAGE_FILE=<scratch> python -m coverage run --source=src/systems/social_systems -m pytest -q -p no:cacheprovider <selection>`, then `coverage report`.

| File | Stmts | `tests/unit/social` only | all 372 tests |
|---|---|---|---|
| `appraisal.py` | 215 | 82% (39 missed) | 82% (38 missed) |
| `clan_lifecycle.py` | 57 | 28% | 95% |
| `consequence_events.py` | 27 | 100% | 100% |
| `contracts.py` | 117 | 93% | 93% |
| `group_service.py` | 25 | 76% | 76% |
| `guilds.py` | 39 | 0% | 0% |
| `loyalty_drift.py` | 12 | 100% | 100% |
| `relationships.py` | 63 | 95% | 98% |
| `reputation.py` | 13 | 77% | 85% |
| `reward_distribution.py` | 26 | 85% | 85% |
| `__init__.py` | 0 | n/a | n/a |
| **Total, excluding `party*.py` and `memory.py`** | 594 | 75.9% (143 missed) | 83.0% (101 missed) |

Excluded from the totals and the findings: `party.py`, `party_composition.py`, `party_lifecycle.py` (no
oracle or owner, D-P) and `memory.py` (dormant, `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`). For
reference the unfiltered all-files total is 85% (813 statements, 119 missed).

Reading it: coverage is execution evidence, not proof of an approved claim (taxonomy §7).
- `clan_lifecycle.py` is covered by `tests/unit/domains/faction/`, not by `tests/unit/social` (28% to 95%).
- `reputation.py` has no direct importer under `tests/unit/social`, yet reaches 77% there: it is exercised
  through other modules. The 85% figure adds the elsewhere-files.
- `guilds.py` is at 0% under every social selection. It is imported by `src/systems/guild_system.py`,
  which the ownership map lists under Quests / guild, so it is live code in the social directory owned by
  another domain. Whether guild tests elsewhere reach it was not measured here.

### 2.3 Marker coverage (collect-only census of the same 372 tests)

| Group | Tests | Files | No marker at all | Markers present |
|---|---|---|---|---|
| `tests/unit/social` | 296 | 33 | 238 | `v2_contract` 57, `differential` 1, `slow` 1 |
| Elsewhere | 76 | 20 | 66 | `architecture` 8, `slow` 2 |

No test of the 372 carries `domain(...)` or `level(...)`. That is not a defect under the taxonomy:
those markers are required for new or modified core-RPG tests and existing tests are not bulk-marked
(taxonomy §10). No marker was added.

### 2.4 Placement audit against the taxonomy (§5 placement column, §8)

| Finding | Detail | Verdict |
|---|---|---|
| `tests/unit/social/test_multi_hero.py` runs a real `Kernel` (`tick_once`) | Taxonomy §5 puts kernel integration in `tests/integration/<area>/`; this file sits under `tests/unit/` and is `slow`-marked. It is also the only `tests/unit/social` file that references the kernel (G3) | **Candidate misplacement.** Not moved |
| Clan lifecycle tests in `tests/unit/domains/faction/` (3 files, 16 tests) | They test `ClanLifecycleService`, which lives in `social_systems/` | **Ambiguous**: placed by component (faction), not by code directory. Owner call, not a finding of error |
| Files outside the social tree that import one social service for another component's test (`unit/combat/test_combat_ecology.py`, `unit/core/test_p1_semantic_hardening.py`, `unit/strategic/test_strategic_social_contracts.py`, plus the party-related `unit/engine/test_legality_faction_mutation.py` and `unit/observability/test_event_extractor_identity.py`) | Placed by the component under test | **No misplacement** |
| `tests/architecture/test_*write_paths.py` (3), `tests/integration` campaigns and cooperation phase (3), `tests/simulation_quality` corpora (6) | Match the levels in §5 (architecture guard, integration, broad simulation) | **No misplacement** |

Recorded misplacement list: 1 candidate (`test_multi_hero.py`) and 1 ambiguous placement (the clan
lifecycle files). No moves.

### 2.5 Owner routing

The ownership map already has a social row. `docs/plans/test_architecture/reference/architecture_design_notes.md` §3.1
*Social / narrative* was updated with the measured roots (`src/systems/social_systems/`; `party*.py` stays in
the Party row; `memory.py` excluded), the oracle documents and the owner contact `rpg-feature-planning`. No
other ownership-map or triage text changed. A test-found social defect routes to the feature-owning team
through that map (`docs/testing/regression_policy.md` §13.4).
