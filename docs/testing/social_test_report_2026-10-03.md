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
14 P2. The plan's figures (227 P0, 211 without `test_path`) hold at this SHA. 83 entries carry a `test_path`.
Each value can hold several paths (separated by commas, semicolons, backticks or spaces), so paths were
extracted with the pattern `tests/[A-Za-z0-9_./-]+?\.py` over every value: they cite **63 distinct test
files** (P0 entries 14, P1 entries 39, P2 entries 16, with overlaps between priorities), and all 63 exist.
An earlier count of 23 came from a first-path-only parse and was wrong.

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
that it was sent, not that anyone agreed). A second message on 2026-10-03 routed the section 4 follow-up (the
line 46 and 64 reads are pinned by existing tests, so a later gate on them will fail those tests as
expected) to `rpg-feature-planning`, with a copy to `world-rule-catalog-design`; both sends were queued and
neither had replied when this was written.

## 4 · Mutation baseline on `appraisal.py` (`TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE`)

Record: `tests/mutation/baselines/src_systems_social_appraisal_v1.json` (the full survivor diffs, the
selection, the tool and the provenance are there; this section only summarises). The staleness line at the top of this
report applies to it.

| Field | Value |
|---|---|
| Target | `src/systems/social_systems/appraisal.py`, 542 lines, sha256 `d921245aaab745c724f5e1ef1011b8b5ef2eb3f2df1d48b6eb9891e12b78eceb` |
| Source SHA | `origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6` (scratch copy by `git archive`, outside the repo) |
| Tool | `mutmut` 2.5.1 (`pip --target`, not a project dependency; 3.x rejects `src.` module paths) |
| Selection | `import-based-one-hop`, target `src.systems.social_systems.appraisal`, excluding `tests/mutation/`: 46 files, 313 tests, hash `41fc8fd6…`, no curated additions. Green before mutation (313 passed, about 5 s) |
| Run | 2026-10-03T09:17:20Z to 09:47:11Z, 1,791 s |
| Result | 345 mutants: **188 killed, 157 survived**, 0 timeout, 0 suspicious; equivalent mutants not classified (mutmut does not) |
| Positive control | fresh: `(public_trust * 0.7)` to `(public_trust * 0.6)` by hand in the scratch copy is killed by the selection (original 313 passed); target restored, hash equal |
| `stale_after` | target sha256 changes, selection changes, 30 days, or `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` landing |

**G3 (determinism).** The kernel runs in this selection: a read-only probe (kept outside the repo) saw 5
`Kernel.tick_once` calls, in `tests/mechanic_scenarios/test_action_pacing_readiness_gate.py` (2),
`tests/mechanic_scenarios/test_combat_judgement_withdrawal.py` (2) and
`tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py` (1), all as found with `audit_mode`
False and `max_tick_budget_ms` 100. The mutation run forced `audit_mode=True` and a relaxed tick budget
through that scratch plugin, and the selection is still 313 passed under that forcing. No test or source
file in the repo was changed. `tests/unit/social/test_multi_hero.py`, which the plan expected to be
selected, is not in the selection (it does not import `appraisal`).

**Where the survivors are** (by enclosing function, from the mutmut cache; counts, not judgements):

| Function | Killed | Survived | Mutants |
|---|---|---|---|
| `_appraise_recruitment` | 59 | 38 | 97 |
| `_appraise_position_swap` | 0 | 38 | 38 |
| module level (constants, imports) | 1 | 17 | 18 |
| `_appraise_loan` | 7 | 15 | 22 |
| `recalibrate_trust` | 0 | 13 | 13 |
| `_appraise_trade` | 19 | 10 | 29 |
| `process_betrayal` | 13 | 9 | 22 |
| `calculate_recruitment_cost` | 12 | 6 | 18 |
| `appraise_contract` | 46 | 5 | 51 |
| `_appraise_team_up` | 7 | 5 | 12 |
| `update_familiarity` | 6 | 1 | 7 |
| `recalibrate_source_trust` | 18 | 0 | 18 |

No mutant on `_appraise_position_swap` or `recalibrate_trust` is killed by the selected tests. That is
what the selection catches today, not a statement that either function is wrong, and not an equivalent-mutant
classification: some survivors may be equivalent. Survivors are findings, not fixes, and no test is changed
or suggested.

**0 kills on `_appraise_position_swap` is measured under the one-hop selection only.** Tests that may reach
it through the movement phase (`src/engine/pipeline_phases/movement.py`) and the social-contract goal scorer
were not selected, and whether they kill these mutants was not measured. In the selection,
`test_appraisal_logic.py` only names `POSITION_SWAP` in a gate-dispatch dict. A coverage reach check, like
the one for `guilds.py` and in scratch only, was run on three such files
(`tests/unit/movement/test_position_swap.py`,
`tests/integration/pipeline/test_movement_micro_arena_position_swap.py`,
`tests/unit/ai/goals/test_social_contract_goal_scorer.py`; 24 passed): they execute **1 of the 28
statements** of the function (lines 234 to 298), so they do not reach its body either. Other tests in the
repository were not measured. Neither result is a defect finding.

**Static follow-up on whether anything creates a `POSITION_SWAP` contract** (a source search at
`9640ff942`, not a runtime measurement). In `src/`, `ContractKind.POSITION_SWAP` appears only in the enum
(`src/core/strategic.py`), the dispatch at `appraisal.py:90` and the read at
`src/engine/pipeline_phases/movement.py:407`; the `kind=ContractKind.…` construction sites found in `src/`
build `LOAN`, `RECRUITMENT` and `PAID_INFORMATION` contracts. The constructions of a `POSITION_SWAP`
contract that were found are in tests (for example `tests/unit/movement/test_position_swap.py`, lines 105
and 192). No creation site in `src/` was found, which fits a branch that nothing produces at runtime, but a
search absence is not proof: contracts built from data, strings or another path would not appear, and no run
was probed. Whether the branch is dormant or just untested is left open for the contracts-mechanism work.

**What kills the line 46 and 64 mutants, and a forward consequence.** Each of the 7 mutants was re-applied in
the scratch copy and the selection re-run (mutmut does not record the killing test). Line 46 mutants fail
6, 2 and 10 tests; line 64 mutants fail 1, 1, 4 and 34 tests (the 34-test mutant breaks the read itself, so
many unrelated tests fail with it). The tests that most directly pin the reads are
`tests/unit/social/test_parity_soc_134.py` (`test_high_public_reputation_source_accepted`,
`test_zero_public_reputation_source_rejected`), `tests/unit/social/test_reputation_learning.py::test_public_vs_private_trust`,
`tests/unit/social/test_domain_7_social.py::test_appraisal_traits`,
`tests/unit/social/test_appraisal_logic.py::test_stranger_judgment_incorporates_clan_reputation` and
`tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py::test_defection_degrades_clan_reputation_and_flips_stranger_loan_decision`.
So if anyone later gates the reads on lines 46 and 64 to resolve PERC-01 / KNOW-01, existing selected tests
will fail; those failures are expected and are the tests pinning today's behaviour. They are not defects,
and this report does not say which way the behaviour should go.

**Current behaviour, catalog-CONFLICTING (kept as a separate list).** The reads on lines 46
(`public_reputation`) and 64 (`clan_reputation`) have 3 and 4 mutants. All 7 were **killed**, so there are no
survivors in the CONFLICTING list: the existing tests pin that current behaviour. The label is the G4 answer,
not re-derived here, and this is an observation, not a recommendation.

## 5 · Batch review (written after C4)

Recorded against the roadmap §2 measures. Every sample size is stated and none is a trend. One domain, one
batch, one target.

| Measure | What the batch showed | Sample |
|---|---|---|
| Locate | The social test surface was found by import (372 tests in 53 files; 20 files outside `tests/unit/social`) and measured (83.0% line coverage excluding party and `memory.py`). The same coverage run read `guilds.py` as 0% while a test elsewhere covers it at 92%, so a single selection can give a **false zero** for live code. Placement: 1 candidate misplacement, 1 ambiguous. The impact report was not exercised, so no selection misses were recorded or counted | 1 domain, 372 tests, 53 files, 2 selections |
| Run | One rule-level routing case pins that a social-only change goes to the `Scenario lane` job. No PR touching only `src/systems/social_systems/**` has been observed in CI, and no social mechanic scenario exists for that job to run | 1 rule-level case, 0 CI-observed social-only PRs, 0 social scenarios |
| Report honestly | Coverage, marker and mutation figures each carry a SHA, a command and an exclusion list. The core-RPG report tool was not extended for social (it lists party modules only). The oracle map found 211 of 227 P0 ledger entries with no `test_path` (section 3.2) | 294 ledger entries, 227 P0 |
| Detect faults | A baseline now exists for one social target: 188 of 345 mutants killed (54.5%), 157 survived. There is no earlier run, so "non-decreasing" cannot be tested yet. The fresh positive control was killed | 1 target, 1 run, 345 mutants, 1 control |
| Escape less | Not measured: this batch tagged no `escaped-defect` and found none | 0 |
| Route failures | The social row of the ownership map was updated, and one findings message was sent to `rpg-feature-planning` (no reply received when written). No failure was triaged in this batch | 1 row, 1 message, 0 failures |
| Stay proportionate | The mutation selection is cheap (about 5 s per run, 1,791 s for 345 mutants). `tool_call_count` per phase was not analysed here. Process slip: the C2 ticket was first closed without its staging set, which the done-checker caught; it was repaired and disclosed, and C3 and C4 created the set first | 4 tickets, 1 slip |

**Workflow observation (plan item 5).** No social-domain ticket other than this batch's four children was
observed running the Epic C steps during the batch. This is what this session saw, not a census of other
sessions.

**Owner decision (2026-10-03): pause scale-out after social** (the owner's answer, relayed by
`test-architecture-reviewer`). The batch's main findings are foundation gaps for the feature teams (211 of
227 P0 entries without `test_path`; selected tests pin the catalog-CONFLICTING reputation read;
`_appraise_position_swap` barely reached), not a case for more measurement batches. No next domain is chosen.
Watch items (a)–(e) in the roadmap §6 continue; scale-out is revisited by a new owner decision, for example
when the semantic-foundation work lands.
