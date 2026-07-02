---
title: Testing — Getting Started Guide
layer: testing
authority: P1
audience: developer
tags: [testing, ci, regression, markers, gates]
---

# Testing — Getting Started Guide

How to write, run, and triage tests in this repo.
Taxonomy reference: [`docs/testing/test_taxonomy.md`](../testing/test_taxonomy.md).
Regression policy: [`docs/testing/regression_policy.md`](../testing/regression_policy.md).

---

## Test layout

```
tests/
  unit/           — isolated unit tests (no I/O, no engine loop)
  integration/    — multi-component tests (kernel, pipeline, observability)
  parity/         — differential parity tests between src and legacy behavior
  certification/  — full-run smoke tests (determinism, long-run stability)
  scenarios/      — named scenario regression tests
  architecture/   — import boundary and structural guards
  api/            — REST endpoint tests
  perf/           — performance benchmarks (advisory; see §CI gates)
```

---

## Running tests

**Always scope to the domain you changed** — never run the full suite blindly.

```bash
# Unit tests for a specific domain
pytest tests/unit/simulation_quality/ -v
pytest tests/unit/observability/ -v
pytest tests/unit/engine/ -v

# Exclude slow tests
pytest tests/unit/ -m "not slow" -v

# Integration tests for the kernel
pytest tests/integration/kernel/ -v

# Architecture boundary guards (always worth running after refactors)
pytest tests/architecture/ -v

# Full certification suite (slow — run before a release)
pytest tests/certification/ -v
```

---

## Test markers

Every test in `tests/parity/` **must** carry at least one of these markers or it will not run:

| Marker | When to use |
|---|---|
| `legacy_characterization` | Freezing current legacy behavior as an oracle |
| `v2_contract` | Asserting behavior of new engine components; no legacy comparison needed |
| `differential` | Proving bit-identical parity between two implementations |
| `intentional_divergence(id="X")` | Explicitly documenting a known behavioral difference; `id` maps to `docs/parity_ledger/` |
| `regression` | Preventing return of a previously fixed bug; include a comment linking to the ticket |
| `certification` | High-level smoke test over a full run |
| `worldassembly` | Tests that own world module assembly (see taxonomy for exact ownership boundaries) |

Example:

```python
@pytest.mark.v2_contract
def test_conservation_law_holds_after_harvest():
    # REQ: CONSERVATION-001 — gold created only through valid transactions
    ...
```

---

## CI gates — what blocks merge

These test groups must pass on every commit:

| Group | Location | What it protects |
|---|---|---|
| Certification | `tests/certification/` | Full-run determinism and stability |
| Kernel determinism | `tests/integration/kernel/test_determinism_suite.py` | Bit-identical replay |
| World compile determinism | `tests/certification/test_world_compile_determinism.py` | Reproducible world assembly |
| Authoritative pipeline | `tests/integration/pipeline/test_mutation_boundary.py` | No hidden state mutation |
| Resource conservation | `tests/integration/kernel/test_resource_conservation.py` | Atomic conservation law |
| Combat legality | `tests/integration/pipeline/test_combat_legality_matrix.py` | No illegal combat outcomes |
| API security | `tests/api/` (path-traversal, sanitization) | Security gates |
| Architecture guards | `tests/architecture/` | Import boundary enforcement |

**Performance gates** (from `docs/performance/perf_baseline_policy.md`):
- p50 latency: ≤ baseline + 5%
- p95 latency: ≤ baseline + 10%
- p99 latency: ≤ baseline + 15%
- RSS delta (tick 100→1000): ≤ baseline + 15%

Soft monitors (alert only, don't block merge): live API tests, integration observability flows,
scenario tests, non-gate perf benchmarks.

---

## Writing a requirement test

A requirement test protects a named simulation law. Its failure means "investigate the code,"
not "update the test." Full pattern in
[`docs/testing/how_to_add_requirement_tests.md`](../testing/how_to_add_requirement_tests.md).

The four-part structure:

```python
@pytest.mark.v2_contract
def test_harvest_does_not_duplicate_resources():
    # REQ: CONSERVATION-001 — items created only through valid harvest transactions
    # Cite: docs/mechanics/03_economic_laws.md §3.2

    # 1. Arrange — minimal valid world state
    world = build_minimal_world()

    # 2. Act — single authoritative mutation
    result = apply_harvest(world, node_id="node_1", entity_id="hero_1")

    # 3. Assert the invariant, not the implementation detail
    assert result.item_count_before + 1 == result.item_count_after
    assert world.gold_total == world.gold_total_before  # conservation holds

    # 4. Assert source state was not mutated (immutability law)
    assert world_snapshot_before == world_snapshot_after_harvest
```

After writing the test, add a row to
[`docs/testing/requirement_traceability.md`](../testing/requirement_traceability.md)
and update the parity ledger entry if this closes a `missing` or `divergent` item.

---

## Triage: when a gate test fails

1. **Find which requirement it protects.** Look up the file in `docs/testing/requirement_traceability.md`.
2. **Check the parity ledger.** Find the entry in `docs/parity_ledger/` for the subsystem — is it `verified`, `divergent`, or `missing`?
3. **Was the change intentional?** If yes, it must appear in `docs/guidelines/v2_intentional_divergences.md`. If not there, the change is unauthorized — revert it.
4. **Decide:**
   - Code broke the law → fix the code, not the test.
   - Intentional + divergence filed → update the test and the parity ledger in the same session.
   - Test was always wrong → fix the test, add a correct replacement, note in the ticket.

Never delete a P0 test without a replacement. Never update a P0 test without a filed divergence.

---

## P0 test authority

A **P0 test** protects a P0 requirement (see `docs/testing/requirement_traceability.md`).
Updating one requires:
1. A filed entry in `docs/guidelines/v2_intentional_divergences.md` explicitly covering the behavior.
2. The parity ledger entry updated (`status`, `v2_evidence`, `divergence_note`) in the same session.
3. The `docs/compliance/checklist.md` entry updated if the proof path changes.

---

## Further reading

- [`docs/testing/test_taxonomy.md`](../testing/test_taxonomy.md) — complete marker definitions and enforcement rules
- [`docs/testing/regression_policy.md`](../testing/regression_policy.md) — full regression triage decision tree
- [`docs/testing/how_to_add_requirement_tests.md`](../testing/how_to_add_requirement_tests.md) — four-part test pattern with examples
- [`docs/testing/requirement_traceability.md`](../testing/requirement_traceability.md) — which tests protect which laws
- [`docs/testing/no_duplication_test_policy.md`](../testing/no_duplication_test_policy.md) — ownership boundaries by test group
- [`docs/parity_ledger/`](../parity_ledger/) — per-subsystem parity status
