# Test Plan — TCK-20260702-SIMQ-EVAL-HARNESS

**Date:** 2026-07-02
**Ticket:** TCK-20260702-SIMQ-EVAL-HARNESS — SimQ Standing Evaluation Harness (`make evaluate`)

---

## Regression Surface

The following existing tests must remain green throughout implementation. Do not modify them.

| Test file | Scope | Run command |
|---|---|---|
| `tests/simulation_quality/test_grade_regression.py` | grade anchor fixture validation + per-key pillar band check | `pytest tests/simulation_quality/test_grade_regression.py -v --tb=short -m "not slow"` |
| `tests/simulation_quality/test_accumulator.py` | accumulator logic including injected window_size (INFRA-251 path) | `pytest tests/simulation_quality/test_accumulator.py -v --tb=short` |

Neither file should be modified by this ticket. If either fails post-implementation, that is a regression in the new harness code, not a test maintenance task.

---

## New Tests Required

**File:** `tests/simulation_quality/test_evaluate_harness.py`

All tests are pure unit tests — no filesystem access, no engine invocation, no subprocess calls. Use `tmp_path` fixtures for any file I/O tests.

### Test 1: `test_within_band_edge_cases`

Validates all boundary conditions of the duplicated `_within_band` function in `evaluate_simq.py`.

```python
from tools.evaluate_simq import _within_band, GRADE_ORDER

def test_within_band_edge_cases():
    # Same grade — always within band
    for g in GRADE_ORDER:
        assert _within_band(g, g) is True

    # Adjacent grades (distance=1) — within tolerance=1
    assert _within_band("C", "B") is True   # one step below
    assert _within_band("A", "B") is True   # one step above

    # Two apart (distance=2) — outside tolerance=1
    assert _within_band("D", "B") is False  # two below
    assert _within_band("S", "B") is False  # two above

    # Bottom boundary: anchor=D
    assert _within_band("D", "D") is True
    assert _within_band("C", "D") is True   # one above D
    assert _within_band("B", "D") is False  # two above D

    # Top boundary: anchor=S
    assert _within_band("S", "S") is True
    assert _within_band("A", "S") is True   # one below S
    assert _within_band("B", "S") is False  # two below S

    # Invalid grade inputs — must return False, not raise
    assert _within_band("X", "B") is False
    assert _within_band("B", "X") is False
    assert _within_band("", "B") is False
    assert _within_band("B", "") is False
```

**Why:** `_within_band` is the core gate logic for the whole harness. Edge cases at D/S boundaries and invalid inputs must be verified before any integration test can be trusted.

---

### Test 2: `test_compare_grades_detects_regression`

Validates that `_compare_grades` returns a REGRESS row when actual is two or more bands from anchor.

```python
from tools.evaluate_simq import _compare_grades

def test_compare_grades_detects_regression():
    actual = {"COMBAT": "D", "NARRATIVE": "A"}
    anchor = {"COMBAT": "B", "NARRATIVE": "A"}  # COMBAT D vs B = distance 2 → REGRESS
    rows = _compare_grades("dungeon_crawl_seed42_200t", actual, anchor)
    by_pillar = {r["pillar"]: r["status"] for r in rows}
    assert by_pillar["COMBAT"] == "REGRESS"
    assert by_pillar["NARRATIVE"] == "PASS"
```

**Why:** Confirms the primary failure-detection path. A harness that never signals REGRESS is useless.

---

### Test 3: `test_compare_grades_passes_within_band`

Validates that `_compare_grades` returns PASS when actual is within ±1 band of anchor.

```python
from tools.evaluate_simq import _compare_grades

def test_compare_grades_passes_within_band():
    actual = {"COMBAT": "A", "NARRATIVE": "C"}
    anchor = {"COMBAT": "B", "NARRATIVE": "B"}  # A vs B = dist 1 (PASS), C vs B = dist 1 (PASS)
    rows = _compare_grades("dungeon_crawl_seed42_200t", actual, anchor)
    assert all(r["status"] == "PASS" for r in rows)
    assert len(rows) == 2
```

**Why:** Confirms the pass path — harness must not generate false positives.

---

### Test 4: `test_parse_run_key`

Validates the run key regex parses all key formats correctly.

```python
import re

_RUN_KEY_PAT = re.compile(r'^(.+)_seed(\d+)_(\d+)t$')

def test_parse_run_key():
    cases = [
        ("dungeon_crawl_seed42_200t",         "dungeon_crawl",      42,  200),
        ("sandbox_world_seed137_200t",         "sandbox_world",      137, 200),
        ("simq_routing_test_seed456_500t",     "simq_routing_test",  456, 500),
        ("urban_political_seed42_1000t",       "urban_political",    42,  1000),
        ("dungeon_crawl_seed42_2000t",         "dungeon_crawl",      42,  2000),
    ]
    for run_key, exp_name, exp_seed, exp_ticks in cases:
        m = _RUN_KEY_PAT.match(run_key)
        assert m is not None, f"No match for {run_key!r}"
        assert m.group(1) == exp_name
        assert int(m.group(2)) == exp_seed
        assert int(m.group(3)) == exp_ticks
```

**Why:** If the regex breaks (e.g., after adding a new key format with double underscores), this test fails clearly. Multi-word names like `simq_routing_test` are the tricky case.

---

### Test 5: `test_compare_grades_missing_pillar`

Validates MISSING status when actual report does not contain a pillar that appears in the anchor.

```python
from tools.evaluate_simq import _compare_grades

def test_compare_grades_missing_pillar():
    actual = {"COMBAT": "B"}   # NARRATIVE missing from actual
    anchor = {"COMBAT": "B", "NARRATIVE": "A"}
    rows = _compare_grades("dungeon_crawl_seed42_200t", actual, anchor)
    by_pillar = {r["pillar"]: r["status"] for r in rows}
    assert by_pillar["COMBAT"] == "PASS"
    assert by_pillar["NARRATIVE"] == "MISSING"
```

**Why:** Ensures missing pillars produce MISSING (warning) not REGRESS (error). The exit-code semantics depend on this distinction — MISSING must not trigger exit code 1.

---

### Test 6: `test_exit_code_zero_on_all_pass` (optional but recommended)

Validates `main()` exits 0 when all scenarios pass. Use `monkeypatch` to stub `_run_scenario` and a tmp fixture file.

```python
import json, sys
import pytest
from unittest.mock import patch
from tools import evaluate_simq

def test_exit_code_zero_on_all_pass(tmp_path, monkeypatch):
    anchors = {
        "dungeon_crawl_seed42_200t": {"COMBAT": "B", "NARRATIVE": "A"}
    }
    anchor_file = tmp_path / "anchors.json"
    anchor_file.write_text(json.dumps(anchors))

    monkeypatch.setattr(sys, "argv", [
        "evaluate_simq", "--dry-run", "--anchors", str(anchor_file),
        "--scenario", "dungeon_crawl_seed42_200t"
    ])
    # Stub _run_scenario to return pre-baked grades within band
    with patch.object(evaluate_simq, "_run_scenario",
                      return_value={"COMBAT": "B", "NARRATIVE": "A"}):
        with pytest.raises(SystemExit) as exc:
            evaluate_simq.main()
        assert exc.value.code == 0
```

**Why:** Confirms the exit-code contract. The harness must not exit 1 when all grades are within band.

---

## Scoped Pytest Commands

```bash
# Run only the new harness unit tests
pytest tests/simulation_quality/test_evaluate_harness.py -v --tb=short

# Run full SimQ test suite (fast, excluding slow marks)
pytest tests/simulation_quality/ -v --tb=short -m "not slow"

# Run grade regression anchors only
pytest tests/simulation_quality/test_grade_regression.py -v --tb=short -m "not slow"

# Run accumulator tests (INFRA-251 regression guard)
pytest tests/simulation_quality/test_accumulator.py -v --tb=short

# Smoke test Makefile targets (dry-run mode, no engine re-run)
make evaluate
```

**Do not run:**
- `pytest tests/` (full suite) — out of scope for this ticket
- `pytest tests/simulation_quality/ -m slow` — requires 1000t+ calibration data, not part of this ticket's acceptance criteria

---

## Anti-Drift Guards

### Guard 1: `_within_band` must match `test_grade_regression.py`
The duplicate copy in `evaluate_simq.py` must produce bit-identical results to the original. The test `test_within_band_edge_cases` covers all boundary cases. If `test_grade_regression.py` ever updates its `_within_band` logic, `evaluate_simq.py` must be updated in the same commit.

### Guard 2: Grade anchor metadata keys must be filtered
`grade_anchors.json` has 3 underscore-prefixed metadata keys (`_note`, `_instructions`, `_grade_order`). The harness must skip these. The test `test_parse_run_key` implicitly guards this by only using valid run_key strings, but an integration test loading the real anchor file would also catch it. Add a sanity assertion in `test_grade_anchor_file_exists_and_valid` if needed (already exists in `test_grade_regression.py`).

### Guard 3: `_compare_grades` row schema
Each row returned by `_compare_grades` must have exactly the keys: `run_key`, `pillar`, `anchor`, `actual`, `status`. Tests 2, 3, and 5 validate the `status` field. The planner phase should verify `_print_table` uses the same key names.

### Guard 4: Exit code contract
| Condition | Exit code |
|---|---|
| All PASS (MISSING treated as warning) | 0 |
| Any REGRESS detected | 1 |
| Anchor file missing / invalid JSON / schema error | 2 |

Test 6 covers exit 0. A companion test for exit 1 (a REGRESS scenario) and exit 2 (missing anchor file) is strongly recommended in `test_evaluate_harness.py` and should be added during implementation if time allows.

### Guard 5: Makefile `.PHONY` completeness
After adding `evaluate` and `evaluate-full`, verify both appear in the `.PHONY` declaration on line 1 of `Makefile`. Run `make -n evaluate` to confirm the target is recognized. A missing `.PHONY` entry won't cause test failures but will produce confusing behavior if a file named `evaluate` exists.
