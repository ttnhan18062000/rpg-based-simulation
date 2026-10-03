# Test Plan — TCK-20260630-SIMQ-ANCHORS

## Anchors to commit (8 run keys)

Fast (200t / 500t — no slow mark):
1. sandbox_world_seed42_200t
2. sandbox_world_seed137_200t
3. sandbox_world_seed999_200t
4. dungeon_crawl_seed42_200t
5. urban_political_seed42_200t
6. simq_routing_test_seed42_500t

Slow (1000t — @pytest.mark.slow):
7. dungeon_crawl_seed42_1000t
8. sandbox_world_seed42_1000t

## Test structure

### Fixture
```python
@pytest.fixture(scope="module")
def grade_anchors():
    return json.loads(FIXTURE_PATH.read_text())
```
Module-scoped: loaded once per test session for the module.

### Band tolerance helper
```python
GRADE_ORDER = ["D", "C", "B", "A", "S"]  # ascending quality

def _within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    if actual not in GRADE_ORDER or anchor not in GRADE_ORDER:
        return False
    return abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance
```

Examples:
- anchor=B, actual=A → dist=1 → PASS
- anchor=B, actual=C → dist=1 → PASS
- anchor=B, actual=D → dist=2 → FAIL
- anchor=B, actual=S → dist=2 → FAIL
- anchor=A, actual=S → dist=1 → PASS
- anchor=A, actual=B → dist=1 → PASS

### Fast parametric test (6 run_keys)
```python
@pytest.mark.parametrize("run_key", FAST_ANCHOR_KEYS)
def test_grade_within_anchor_band(run_key, grade_anchors):
    ...
```
Loads `data/calibration/{run_key}/quality_report.json`, extracts per-pillar grades, checks each
against anchor with tolerance=1. Skips if calibration file missing.

### Slow parametric test (2 run_keys)
```python
@pytest.mark.slow
@pytest.mark.parametrize("run_key", SLOW_ANCHOR_KEYS)
def test_grade_within_anchor_band_long_run(run_key, grade_anchors):
    ...
```
Same as fast test but `@pytest.mark.slow` so excluded from `pytest -m "not slow"`.

### Structural test (replaces old test_grade_anchor_file_exists_and_valid)
```python
def test_grade_anchor_file_exists_and_valid(grade_anchors):
    ...
```
Checks: fixture loaded, MINIMUM_ANCHORS (6 fast) present, each entry has 10 pillars,
all grades valid (in GRADE_ORDER).

## Acceptance criteria coverage

| Criterion | Test |
|---|---|
| pytest passes with new anchors | test_grade_within_anchor_band (all 6 fast) |
| fixtures/grade_anchors.json committed | structural test + file existence |
| Band tolerance ±1 | _within_band unit check via mutation test |
| sandbox_world 3 seeds × 200t | parametrize covers seed42/137/999 |
| Doc comment explains update procedure | docstring in test file |

## Mutation test procedure

Temporarily change one anchor grade to a non-adjacent grade (e.g., "COMBAT": "B" → "COMBAT": "D"
for sandbox_world_seed42_200t). Run `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"`.
Expect AssertionError on sandbox_world_seed42_200t/COMBAT. Restore anchor.
