---
status: active
layer: performance
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER
tags: [testing, bug, performance]
---

# Investigation: TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER

## Current Behavior (file:line refs)

`tests/perf/test_perf_combat.py:6-20`:
```python
@pytest.mark.perf
@pytest.mark.parametrize("side_count", [10, 50, 100, 500])
def test_perf_combat(side_count, perf_report_dir):
    ...
    result = BenchHarness(profile).run_benchmark(
        scenario_id=f"COMBAT_{side_count}v{side_count}",
        initial_state=state,
        warmup_ticks=10,
        sample_ticks=50
    )
    assert result["p95_tick_compute_ms"] < 200.0
```
No `@pytest.mark.slow` anywhere in the file. `git log --oneline -- tests/perf/test_perf_combat.py`
shows exactly one commit ever: `56211688` ("Resource V2 Implementation", 2026-05-18) — created and
never touched since.

Reproduced locally (`.venv`, Python 3.12):
```
[10]   p95=12.26ms   PASS
[50]   p95=36.45ms   PASS
[100]  p95=67.69ms   PASS
[500]  p95=440.91ms  FAIL (assert 440.912 < 200.0)
```
Scaling is smooth (10→50 ≈3x time for 5x entities; 100→500 ≈6.5x time for 5x entities) — mildly
superlinear, not a step/cliff. Dominant cost at every size: `final_integrity`
(`src/engine/pipeline.py:355`, dirty-checking/hardening/lifecycle/capacity bookkeeping) —
4.5ms→11.8ms→30.5ms→176.5ms across the 4 sizes, alone exceeding the 200ms budget at 500v500 before
other phases are counted.

## Mechanics/Engine Constraints

`docs/engine/performance_contract.md` §3.2 requires **100 warmup ticks + 1000 sample ticks
minimum**. This test uses **10 warmup + 50 sample** — non-compliant. Per the already-closed
`TCK-20260624-FIX-PERF-BUDGETS` (found via `tickets/done/`), "all thresholds are ad-hoc, not sourced
from performance_contract.md" was the exact, already-diagnosed root cause for a class of 13 sibling
perf tests, all resolved by marking `@pytest.mark.slow` (moving them to the CI `slow` job, which
runs under `--resource-budget large` — confirmed via `.github/workflows/test.yml:232`:
`pytest tests/ -m "slow or extra_slow" --resource-budget large ...`). `test_perf_combat.py` was not
in that ticket's own Files Changed list — it was simply missed by that sweep.

## Docs Requiring Update
None. `docs/engine/performance_contract.md` is unaffected — this ticket doesn't change methodology
or thresholds, only moves the test out of the fast lane, matching the disclosed-gap pattern already
accepted for most of the 13 sibling tests in the precedent ticket (which did NOT rewrite every
test's methodology to be contract-compliant — only a handful got specific threshold/warmup fixes).

## Parity Ledger Overlap (IDs + status)
`TCK-20260624-FIX-PERF-BUDGETS`'s own Files Changed list shows it updated `STRAT-225` in
`docs/parity_ledger/strategic_cognition.yaml` — unrelated to combat performance, no overlap. No
parity ledger entry references `test_perf_combat.py` or combat perf thresholds specifically
(confirmed via `grep -rn "test_perf_combat" docs/parity_ledger/*.yaml` — no hits).

## Prior Work
`TCK-20260624-FIX-PERF-BUDGETS` (2026-06-24) — the precedent this ticket follows exactly. Marked 13
sibling files `@pytest.mark.slow` for the identical root cause (ad-hoc, non-contract-compliant
thresholds noisy on CI runners); fixed 3 specific thresholds where warranted;
`test_perf_combat.py` not included, apparently missed.

## Risks and Open Questions
- **Checked**: no single suspicious commit found for either the test file or
  `final_integrity`/`kernel.py` around the 500v500 case — this reads as inherent authoritative-
  pipeline cost at 1000-entity scale, not a regression.
- **Not fixed, disclosed**: the test's own warmup/sample counts remain non-compliant with
  §3.2 after this ticket — matching the precedent's own scope (most of its 13 marked tests were not
  rewritten either), not a new gap introduced by this ticket.

## Anti-Drift Hazards
None — this is a single-file marker addition with no production code change and no other file
dependency.
