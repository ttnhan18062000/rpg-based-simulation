---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT
artifact_type: investigation
tags: [strategy, cognition]
---

# Investigation: how live is the social-contract objective path, and what does it do?

Ruling (rpg-feature-planning, 2026-10-06): option A, no rule ratification needed.

## 1. The ticket's premise does not match the corpus

The ticket says the scorer captures a **moving counterparty's** position as a fixed point. Measured, that is not what happens. In both contract projects the four corpus worlds produced, the objective's target is the **holder itself**: entity 12 targets "12", entity 26 targets "26". The captured position is the entity's own old position, which is why it drifts when the entity moves.

Cause, read from code:
- `domains/cooperation/services.py:233` (posture REQUEST_HELP or HIRE_SUPPORT) builds a RECRUITMENT contract with `source_id=entity.id` and adds it **only to that entity**. It is the only production producer of these contracts.
- `SocialContractGoalScorer` targets `contract.source_id` for whoever holds the contract. For a contract held by its own source that is the holder.
- `execute_recruit` (core_actions.py) would give both parties a copy, so the recruit would target the recruiter, which is right; but nothing in `src` issues the RECRUIT action, so that mirror is a dead path (recorded as a finding, not fixed).

## 2. Measurement (before; `probes/social_contract_exposure.py`, `probes/sc_measure.sh`)

4 worlds x 2000 ticks, seed 42, `audit_mode`, run twice: **identical** (values). Logs: `probes/sc_before_run1.log`, `probes/sc_before_run2.log`.

| world | scorer calls | wins with utility > 0 | contract projects formed | ticks active | captured != live | active after contract not ACTIVE |
|---|---|---|---|---|---|---|
| crowded_frontier | 1352 | 81 | 1 | 20 | 0 | 0 |
| frontier_living_world | 1623 | 80 | 0 | 0 | 0 | 0 |
| urban_political | 983 | 23 | 1 | 20 | 18 (max gap 2) | 16 |
| dungeon_crawl | 512 | 11 | 0 | 0 | 0 | 0 |

Only RECRUITMENT contracts exist in these runs (no LOAN). The path is rare: 2 projects in 8000 world-ticks, each live 20 ticks. The gap between 195 scorer wins and 2 materialized projects is **not investigated** (planner: note, do not chase).

## 3. Contract lifecycle (Scope 3's first question)

`ContractStatus` has OFFERED, ACCEPTED, COUNTERED, ACTIVE, FULFILLED, FAILED, BETRAYED, EXPIRED, CANCELLED, with `SocialContractSystem.transition_contract` and an expiry check (`reap_expired_offers`, `resolve_contract_outcome`), so the lifecycle does have cancellation and expiry. The termination rule chosen is the one the ruling names: **a contract objective ends when its contract is no longer ACTIVE**. FULFILLED completes the project; every other status, or the contract gone from the entity, abandons it. That is not copied from the combat case (no "target dead"): it follows the contract the project exists to serve. "Counterparty unreachable" is not added: with the guard, no corpus path produces a counterparty to be unreachable, and inventing a distance rule would be a new world semantic.

## 4. Why the ticket's Scope 1 (typed `target_entity_id`) is dropped

Moving the objective onto the typed entity target as written would make a self-sourced holder target **itself**. `entity_target_outcome` ends an objective when its target is dead, gone or beyond the perception radius; a target that is the holder is alive and at distance 0, so it would never end. The typed shape would turn a 20-tick artefact into a permanent hold. With the guard, the remaining holder (the other party) keeps Design Decision #8's captured position; nothing in `src` produces that holder today.

## 5. The `accept_contract()` check (acceptance criterion 6)

`ContractService.accept_contract` has no production caller (its own scorer docstring says so); the objectives now come from the scorer. Negative result: that path does not construct objectives in production, so it has no defect to fix.

## 6. After the change (`probes/sc_after.log`; same probe, same worlds, seed and ticks)

| world | scorer calls (before -> after) | contract projects formed | captured != live | active after contract not ACTIVE |
|---|---|---|---|---|
| crowded_frontier | 1352 -> 1235 | 0 | 0 | 0 |
| frontier_living_world | 1623 -> 1623 | 0 | 0 | 0 |
| urban_political | 983 -> 982 | 0 | 0 | 0 |
| dungeon_crawl | 512 -> 512 | 0 | 0 | 0 |

Both Scope 4 numbers are 0, **because no contract project forms any more** (the two self-targeted projects were the only ones), not because termination was exercised on the corpus; termination is covered by the constructed cases in `tests/unit/strategic/test_contract_objective.py`. The runs differ from the "before" runs where those two entities no longer pursue their own old positions (`crowded_frontier` and `urban_political` trajectories move; the other two worlds are unchanged), so this is a behaviour change, recorded as divergence 2.72. After was measured once per world (not repeated).

## 7. Pre-existing red found while sweeping

`tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression` fails identically on a clean `origin/main` export and on this branch (alive_avg 5.52 vs 13.3, gold_avg 0.0 vs 584.16, quest_active_count 1.02 vs 0). Not caused by this change; tracked by Lane B's `TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC`.
