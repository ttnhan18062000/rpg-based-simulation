---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION
artifact_type: test_plan
tags: [world, determinism, observability, testing]
---

# Test plan — sovereignty ownership-writer consolidation

The decision is **decision-only, no behaviour change** (`plan.md`), so this plan is deliberately
small. It covers one new guard test plus the regression surface that must stay green. It does **not**
cover the `-1` sentinel fix — that is
`TCK-20261003-REGION-OWNER-NONE-SENTINEL-PERSISTED-RAW`'s own test plan.

## Baseline, measured before any change

`tests/integration/world/test_regional_sovereignty.py` + `tests/unit/world/test_sovereignty_events.py`
= **10 passed** at `6d630250d`. Recorded so "still passing" is a comparison, not an assumption.

## Proof Plan

Per-criterion, in the Phase 1 test-architecture convention. Only AC-4 is proved by a new test; the
rest are proved by record or by absence of change, and each says which.

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 — decision recorded with the phase-ordering consequence stated | n/a | record | `plan.md` + `investigation.md` §3; `docs/engine/authoritative_pipeline.md:79` | A written decision naming outcome 3 and the one-tick consequence | none — not a test-provable criterion |
| 2 — no ownership-transfer capability lost | integration | regression (unchanged behaviour) | `docs/mechanics/05_world_evolution.md` ±50 thresholds; `WORLD-107` | Pre-existing flips still occur; no `src/` diff exists to change them | `pytest tests/integration/world/test_regional_sovereignty.py -q` |
| 3 — `test_regional_ownership_flip` still passes | integration | regression | existing test as its own oracle | Unchanged pass | `pytest tests/integration/world/test_regional_sovereignty.py::test_regional_ownership_flip -q` |
| 4 — ownership re-evaluated for a region with no death that tick | integration | **new guard test (T1)** | `docs/mechanics/regional_sovereignty.md`; sweep is unconditional per `pipeline.py:348` | Unowned region at influence ≥ +50 flips to `HERO_GUILD` with zero deaths that tick | `pytest tests/integration/world/test_regional_sovereignty.py::test_ownership_reevaluated_for_region_with_no_death_that_tick -q` |
| 5 — any same-tick/next-tick timing change recorded | n/a | record (negative) | `docs/guidelines/intentional_divergences.md` §2.58/§2.59 shape | **No entry**, because no timing change exists; recorded as a decision in `plan.md` step 4 | none |
| 6 — `WORLD-107` `status` + `v2_evidence` updated | unit | parity | `docs/parity_ledger/world_dynamics.yaml` `WORLD-107` | `v2_evidence` names the second writer; `status: verified` retained with the retention justified in-entry | `pytest tests/unit/world/test_sovereignty_events.py -q` |

**Oracle note.** For AC-2 and AC-3 the oracle is the pre-change behaviour itself, which is only a valid
oracle because this ticket changes no `src/` file — verified by `git diff --stat` showing no `src/` path
in its commit. If a later revision of this ticket touches `src/`, these two rows need a real oracle
from the Bible chapter instead.

## T1 — AC-4 guard: ownership is re-evaluated with no death that tick

`tests/integration/world/test_regional_sovereignty.py::test_ownership_reevaluated_for_region_with_no_death_that_tick`

The only new test this ticket lands. An unowned region at influence 99.5 receives a non-death
`influence_delta` and must flip to `HERO_GUILD` through the unconditional `world_dynamics` sweep, with
a live bystander entity and **no death anywhere that tick** (asserted, so the fixture cannot silently
acquire one).

Guards the specific regression AC-4 names: narrowing ownership evaluation to the death-gated path.
Any future consolidation that only evaluates ownership inside `process_influence_shift` fails this.

**Why a dedicated test when `test_regional_ownership_flip`'s second half already covers it:** that
test's primary assertion is the flip itself, so a future edit could weaken the no-death property
without the name or the failure message revealing what was lost. This one fails with a message that
says exactly what broke.

## T2 — regression surface that must stay green

Scoped per the Testing Rule; the full suite is not run.

| scope | expectation |
|---|---|
| `tests/integration/world/` | green except the two pre-existing failures below |
| `tests/unit/world/` | green (338 passed standalone) |
| `tests/unit/world/test_sovereignty_events.py` | green — holds `WORLD-107`'s P1 `test_path` |
| `tests/unit/world/test_influence.py` | green — holds §2.58's threshold pins |

Command:

```
PYTHONPATH=. /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 \
    -m pytest tests/integration/world/ tests/unit/world/ -q
```

## T3 — no test for the deferred consolidation, on purpose

No test asserts "there is exactly one ownership writer", because the decision is that there are two.
Writing one would encode an intent the ticket explicitly did not adopt. If consolidation is later
taken up, `investigation.md` §3 holds the contract evidence and the test belongs with that work.

## Pre-existing failures — reported, not fixed, not masked

Both were proven independent of this ticket by re-running without its changes. Neither is skipped,
xfailed, or deselected in the committed state.

1. **`tests/integration/world/test_long_run_stability.py::test_long_run_stability`** — `TimeoutError`
   at `tests/conftest.py:90`. Fails identically on clean `src/` with this ticket's changes reverted.
   Plausibly related to `INFRA-273`'s wall-clock mechanism (`investigation.md` §5b), but **not
   investigated and not claimed** — naming a cause I did not measure is how the earlier wrong claims
   in this arc happened.
2. **`tests/unit/world/providers/test_resource_opportunity_provider.py::test_stone_outcrop_node_surfaces_as_opportunity_in_frontier_village`**
   — cross-test pollution from the integration suite. Evidence it is not mine: passes 3/3 standalone;
   `tests/unit/world/` alone is 338/338 green; it still fails with this ticket's new test file
   excluded via `--ignore`. So the polluter is pre-existing integration code.

## Determinism

No determinism sweep is claimed for this ticket, because there is no behaviour change to perturb one.
Note for anyone running one here: it must set `audit_mode=True` and preferably relax
`max_tick_budget_ms`, or it measures the throttle rather than the engine — see `investigation.md` §5b.
A single-threaded executor is **not** a substitute; that was measured.
