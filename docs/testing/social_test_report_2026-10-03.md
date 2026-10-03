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
out of scope for this batch; the gap was routed to `rpg-feature-planning` together with section 3's findings (section 3.5).

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
- `guilds.py` is at 0% under every social selection, which is an artefact of the selection, not untested
  code. It is imported by `src/systems/guild_system.py`, which the ownership map lists under Quests / guild,
  so it is live code in the social directory owned by another domain. `tests/unit/world/test_guild_intel.py`
  (2 tests, 2 passed) calls `GuildIntelSystem.update` and covers `guilds.py` at **92%** (39 statements,
  3 missed), measured on the same branch head with the same coverage command.

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

## 3 · Oracle map (`TCK-20261003-SOCIAL-ORACLE-MAP-REPORT`)

Report only. No ledger entry, test or mechanism link was changed or proposed (owner decision, 2026-10-03).
Measured at `origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6`, 2026-10-03, by a read-only script
over `docs/parity_ledger/social_narrative.yaml`.

### 3.1 Ledger shape

294 entries: 246 `verified`, 44 `legacy_verified`, 3 `divergent`, 1 `missing`. By priority: 227 P0, 53 P1,
14 P2. The plan's figures (227 P0, 211 without `test_path`) hold at this SHA. All 23 test-file references
that the existing `test_path` values contain resolve to files that exist.

### 3.2 P0 entries with no `test_path`: 211 of 227

16 P0 entries have a `test_path`. The 211 without one are: 166 `verified` (no `proof_type`), 44
`legacy_verified` (`proof_type: parity`) and 1 `missing` (SOC-052). CLAUDE.md requires a passing `test_path`
for P0 entries; this is reported, not fixed. Every P1 and P2 entry has a `test_path`. Reproduce: load the
YAML, filter `priority == P0` and an empty or null `test_path`.

Ids: SOC-009 SOC-010 SOC-011 SOC-012 SOC-013 SOC-014 SOC-015 SOC-016 SOC-017 SOC-018 SOC-019 SOC-020 SOC-021 SOC-022 SOC-023 SOC-024 SOC-025 SOC-026 SOC-027 SOC-028 SOC-029 SOC-030 SOC-031 SOC-032 SOC-033 SOC-034 SOC-035 SOC-036 SOC-037 SOC-038 SOC-039 SOC-040 SOC-041 SOC-042 SOC-043 SOC-044 SOC-045 SOC-046 SOC-047 SOC-048 SOC-049 SOC-050 SOC-052 SOC-053 SOC-054 SOC-055 SOC-056 SOC-057 SOC-058 SOC-059 SOC-060 SOC-061 SOC-062 SOC-063 SOC-064 SOC-065 SOC-066 SOC-067 SOC-068 SOC-069 SOC-070 SOC-071 SOC-072 SOC-073 SOC-074 SOC-075 SOC-076 SOC-077 SOC-078 SOC-079 SOC-080 SOC-081 SOC-082 SOC-083 SOC-084 SOC-085 SOC-086 SOC-087 SOC-088 SOC-089 SOC-090 SOC-091 SOC-092 SOC-093 SOC-094 SOC-095 SOC-096 SOC-097 SOC-098 SOC-099 SOC-100 SOC-101 SOC-102 SOC-103 SOC-104 SOC-105 SOC-106 SOC-107 SOC-108 SOC-109 SOC-110 SOC-111 SOC-112 SOC-113 SOC-114 SOC-115 SOC-116 SOC-117 SOC-118 SOC-119 SOC-120 SOC-121 SOC-122 SOC-123 SOC-124 SOC-125 SOC-126 SOC-127 SOC-128 SOC-129 SOC-130 SOC-131 SOC-132 SOC-133 SOC-135 SOC-136 SOC-137 SOC-138 SOC-139 SOC-140 SOC-141 SOC-142 SOC-143 SOC-144 SOC-145 SOC-146 SOC-147 SOC-148 SOC-149 SOC-150 SOC-151 SOC-152 SOC-153 SOC-154 SOC-155 SOC-156 SOC-157 SOC-158 SOC-159 SOC-160 SOC-161 SOC-162 SOC-163 SOC-164 SOC-165 SOC-166 SOC-167 SOC-168 SOC-169 SOC-170 SOC-171 SOC-172 SOC-173 SOC-174 SOC-175 SOC-176 SOC-177 SOC-178 SOC-179 SOC-180 SOC-181 SOC-182 SOC-183 SOC-184 SOC-185 SOC-186 SOC-187 SOC-188 SOC-189 SOC-190 SOC-191 SOC-192 SOC-193 SOC-194 SOC-195 SOC-196 SOC-197 SOC-198 SOC-199 SOC-200 SOC-201 SOC-202 SOC-203 SOC-205 SOC-206 SOC-209 SOC-210 SOC-211 SOC-212 SOC-213 SOC-214 SOC-215 SOC-216 SOC-218 SOC-219 SOC-220 SOC-221 SOC-222 SOC-223 SOC-224 SOC-225

### 3.3 The divergent and missing entries

| Id | Status, priority | What it is | `test_path` |
|---|---|---|---|
| SOC-052 | missing, P0 | the `test_entity_integration` parity entry (Entity and IdentityComponent absorb new Phase 3 fields), whose cited `tests_v2/parity/test_entity_construction.py` never existed in this repository; its own `support_boundary` says `missing` here means unverified, not known-broken (`TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`) | none |
| SOC-242 | divergent, P1 | `quest_event` moved from post-tick diffing to a push-based `NarrativeShaper` (observability delivery mechanism only; no scoring change) | `tests/unit/observability/test_event_shapers_narrative.py` |
| SOC-263 | divergent, P1 | `SocialComponent` canonical hash previously covered 10 of 17 fields; 7 added (`TCK-20260902-SOCIAL-CANONICAL-HASH-GAP`) | two cases in `tests/unit/core/test_entity_integrity.py` |
| SOC-265 | divergent, P1 | nemesis versus friend-bond precedence in party composition (`TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE`) | five cases in `tests/unit/social/test_party_composition.py` |

SOC-265 concerns party composition, which is outside this batch's findings scope (no oracle or owner, D-P);
it is listed because the ledger marks it divergent.

### 3.4 Other findings

- **Bible-table gap.** `docs/mechanics/07_social_political_dynamics.md` exists but is not in CLAUDE.md's
  Mechanics Bible table, which lists chapters 01 to 06. Owner: `rpg-feature-planning`, who raised it already.
  This batch does not block on it and does not edit CLAUDE.md.
- **Current behaviour, catalog-CONFLICTING (PERC-01 / KNOW-01).** Two reads in `appraisal.py` at this SHA:
  line 46, `public_trust = source_entity.social.public_reputation / 2.0`, and line 64,
  `clan_trust = (state.clans[clan_id].clan_reputation / 2.0) if clan_id else 0.5`. The classification comes
  from `world-rule-catalog-design` through the plan's G4 answer and is not re-derived here. These are
  recorded as current behaviour, not as bugs, and not as targets for tests.
- **`reputation.py` coverage gap.** `reputation.py` (13 statements) has no direct importer under
  `tests/unit/social/`. It reaches 77% from that directory through other modules and 85% with the
  elsewhere-files (section 2.2).
- **Name matches are not links.** No test-to-id link was made by name; only the ledger's own `test_path`
  values were read.

### 3.5 Routing

Sections 1 and 3 are routed to `rpg-feature-planning` by one cross-session message. Sent 2026-10-03 (the send
succeeded and was queued to that session; no reply had been received when this was written, so this records
that it was sent, not that anyone agreed).
