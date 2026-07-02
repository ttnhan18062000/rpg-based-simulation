# Investigation — TCK-20260702-SIMQ-EVAL-HARNESS

**Date:** 2026-07-02
**Ticket:** TCK-20260702-SIMQ-EVAL-HARNESS — SimQ Standing Evaluation Harness (`make evaluate`)
**Investigator:** agent (seq 2)

---

## Current State

### What exists

| Artifact | Status | Notes |
|---|---|---|
| `tools/calibrate_simq.py` | EXISTS | Full engine run + JSONL replay + quality_report.json writer. `main()` is callable; uses `argparse` with `parse_args()` — not `parse_known_args()`, so inline import with patched `sys.argv` is required. |
| `tests/simulation_quality/fixtures/grade_anchors.json` | EXISTS | 25 entries (3 metadata keys + 25 run entries). All keyed as `{name}_seed{N}_{T}t`. |
| `tests/simulation_quality/test_grade_regression.py` | EXISTS | 14 FAST_ANCHOR_KEYS, 11 SLOW_ANCHOR_KEYS, `_within_band` (3 lines), `_extract_pillar_grades` (3 lines). |
| `data/calibration/dungeon_crawl_seed42_200t/quality_report.json` | EXISTS | Confirmed field layout. |
| `tools/evaluate_simq.py` | DOES NOT EXIST | Target of this ticket. |
| `tests/simulation_quality/test_evaluate_harness.py` | DOES NOT EXIST | Target of this ticket. |
| `Makefile` targets `evaluate` / `evaluate-full` | DO NOT EXIST | Last entry is `eval-search` at line 281. |

### No `src/` utility for `_within_band`

`grep -r "_within_band\|within_band" src/ --include="*.py" -l` returned empty. The 3-line logic lives only in `test_grade_regression.py`. Duplication into `tools/evaluate_simq.py` is the correct path — no `src/` module exposes it.

---

## Run Key Inventory

All 25 keys in `grade_anchors.json` (excluding the 3 `_note`/`_instructions`/`_grade_order` metadata fields):

### FAST_ANCHOR_KEYS (14 keys — mirrored in test_grade_regression.py)

| # | run_key | name | seed | ticks | Routing flag? |
|---|---|---|---|---|---|
| 1 | `sandbox_world_seed42_200t` | sandbox_world | 42 | 200 | No |
| 2 | `sandbox_world_seed137_200t` | sandbox_world | 137 | 200 | No |
| 3 | `sandbox_world_seed999_200t` | sandbox_world | 999 | 200 | No |
| 4 | `dungeon_crawl_seed42_200t` | dungeon_crawl | 42 | 200 | No |
| 5 | `urban_political_seed42_200t` | urban_political | 42 | 200 | No |
| 6 | `simq_routing_test_seed42_500t` | simq_routing_test | 42 | 500 | **YES** |
| 7 | `simq_routing_test_seed123_500t` | simq_routing_test | 123 | 500 | **YES** |
| 8 | `simq_routing_test_seed456_500t` | simq_routing_test | 456 | 500 | **YES** |
| 9 | `dungeon_crawl_seed42_500t` | dungeon_crawl | 42 | 500 | No |
| 10 | `dungeon_crawl_seed123_500t` | dungeon_crawl | 123 | 500 | No |
| 11 | `dungeon_crawl_seed456_500t` | dungeon_crawl | 456 | 500 | No |
| 12 | `urban_political_seed42_500t` | urban_political | 42 | 500 | No |
| 13 | `urban_political_seed123_500t` | urban_political | 123 | 500 | No |
| 14 | `urban_political_seed456_500t` | urban_political | 456 | 500 | No |

### SLOW_ANCHOR_KEYS (11 keys)

| # | run_key | name | seed | ticks | Routing flag? |
|---|---|---|---|---|---|
| 15 | `dungeon_crawl_seed42_1000t` | dungeon_crawl | 42 | 1000 | No |
| 16 | `sandbox_world_seed42_1000t` | sandbox_world | 42 | 1000 | No |
| 17 | `dungeon_crawl_seed123_1000t` | dungeon_crawl | 123 | 1000 | No |
| 18 | `dungeon_crawl_seed456_1000t` | dungeon_crawl | 456 | 1000 | No |
| 19 | `urban_political_seed42_1000t` | urban_political | 42 | 1000 | No |
| 20 | `urban_political_seed123_1000t` | urban_political | 123 | 1000 | No |
| 21 | `urban_political_seed456_1000t` | urban_political | 456 | 1000 | No |
| 22 | `dungeon_crawl_seed42_2000t` | dungeon_crawl | 42 | 2000 | No |
| 23 | `dungeon_crawl_seed123_2000t` | dungeon_crawl | 123 | 2000 | No |
| 24 | `dungeon_crawl_seed456_2000t` | dungeon_crawl | 456 | 2000 | No |
| 25 | `sandbox_world_seed42_2000t` | sandbox_world | 42 | 2000 | No |

**Routing flag summary:** 3 of 25 keys (all `simq_routing_test_*`) require `ENABLE_ADVENTURE_ROUTING=ON` in the environment before calling the engine.

---

## Implementation Patterns

### Run key parsing regex — confirmed working on all 25 keys

```python
import re
m = re.match(r'^(.+)_seed(\d+)_(\d+)t$', run_key)
name, seed, ticks = m.group(1), int(m.group(2)), int(m.group(3))
```

Tested against all 25 keys: zero mismatches. The regex handles multi-word names with underscores (e.g., `simq_routing_test`) correctly because `.+` is greedy and `_seed` anchors the split.

### How to invoke `calibrate_simq.main()` inline (full mode)

`calibrate_simq.main()` calls `parser.parse_args()` with no arguments — it reads `sys.argv`. To call it inline for a given run_key, patch `sys.argv` before calling:

```python
import sys
import tools.calibrate_simq as _calibrate

def _run_scenario_full(run_key: str) -> None:
    m = re.match(r'^(.+)_seed(\d+)_(\d+)t$', run_key)
    name, seed, ticks = m.group(1), int(m.group(2)), int(m.group(3))
    old_argv = sys.argv[:]
    sys.argv = [
        "calibrate_simq",
        "--name", name,
        "--seed", str(seed),
        "--ticks", str(ticks),
    ]
    try:
        _calibrate.main()
    finally:
        sys.argv = old_argv
```

**Routing flag handling:** for `simq_routing_test_*` keys, set `os.environ["ENABLE_ADVENTURE_ROUTING"] = "ON"` before calling and restore (`del` or reset) in a `finally` block.

**Alternative (subprocess):** Simpler isolation but complicates env-var injection and loses the return value from `main()`. The ticket scope notes inline invocation is preferred.

### `_within_band` and `_extract_pillar_grades` — duplication decision

The full logic to duplicate (from `test_grade_regression.py` lines 34, 86–94, 97–102):

```python
GRADE_ORDER = ["D", "C", "B", "A", "S"]

def _within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    if actual not in GRADE_ORDER or anchor not in GRADE_ORDER:
        return False
    return abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance

def _extract_pillar_grades(report: dict) -> dict[str, str]:
    return {
        pillar: data["grade"]
        for pillar, data in report.get("pillars", {}).items()
    }
```

Total: 3 lines for `_within_band`, 3 lines for `_extract_pillar_grades`. Trivial to duplicate.

---

## Import Boundary Decision

**Decision: Duplicate `_within_band`, `GRADE_ORDER`, and `_extract_pillar_grades` into `tools/evaluate_simq.py`. Do NOT import from `tests/`.**

Rationale:
1. `tools/` is production-adjacent tooling. Importing from `tests/` would make a `tools/` script depend on test infrastructure — a layering violation that also breaks if tests move or pytest isn't installed.
2. The logic is 6 lines total. The maintenance risk of divergence is negligible given these are pure functions with no mutable state.
3. `src/` has no `within_band` utility (confirmed by grep). Adding one would be over-engineering for a 3-line helper.
4. `test_evaluate_harness.py` tests the duplicated copy in `evaluate_simq.py` directly — so both copies have independent test coverage and will stay in sync through the regression harness.

If the logic ever grows complex enough to warrant sharing, the correct migration target is `src/simulation_quality/grade_utils.py`, not a `tests/` import.

---

## Makefile Pattern

The canonical Python resolver pattern used by `eval-search` (line 281–282) and `mcp-server-test` (line 284–286):

```makefile
eval-search: ## Run search quality evaluation — Recall@5, MRR@10 (requires knowledge-index)
	$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) tools/eval_search.py
```

The `personality-audit` target (line 182–183) uses bare `python3` without the resolver — do NOT use that pattern for new targets.

**New targets must use the resolver pattern.** Exact recipe for `evaluate`:

```makefile
evaluate: ## Diff current calibration data against grade anchors (no engine re-run)
	$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) tools/evaluate_simq.py --dry-run

evaluate-full: ## Re-run engine for fast scenarios and diff against grade anchors
	$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) tools/evaluate_simq.py
```

Both targets must be added to the `.PHONY` line (line 1 of Makefile).

---

## quality_report.json Field Paths

Confirmed from `data/calibration/dungeon_crawl_seed42_200t/quality_report.json`:

```python
# Top-level keys
report.keys()  # ['run_id', 'tick_count', 'overall_score', 'overall_grade', 'generated_at', 'pillars']

# Per-pillar access (pillars is a dict keyed by pillar name)
report["pillars"]["COMBAT"]["grade"]      # e.g., "A"
report["pillars"]["COMBAT"]["normalized_score"]  # float
report["pillars"]["COMBAT"]["event_count"]       # int

# Full pillar dict structure
{
  "raw_score": 0.0,
  "normalized_score": 0.0,
  "grade": "C",
  "event_count": 0,
  "negative_count": 0,
  "loop_detected": False,
  "loop_flags": [],
  "worst_events": []
}
```

**Key for `_extract_pillar_grades`:** `report["pillars"][pillar]["grade"]` — the `grade` key is always present on each pillar dict. The existing `_extract_pillar_grades` uses `.get("pillars", {})` as a safe fallback for empty/malformed reports.

**Dry-run path:** `data/calibration/{run_key}/quality_report.json` — already used verbatim in `test_grade_regression.py` via `_CALIBRATION_ROOT / run_key / "quality_report.json"`.

---

## Parity Ledger Status

- Last entry: `INFRA-251` (calibrate_simq.py window-size/loop-threshold CLI flags).
- `INFRA-252` does not yet exist in `docs/parity_ledger/infrastructure.yaml`.
- New entry to add: `INFRA-252` — standing evaluation harness (`evaluate_simq.py`), status `verified` after implementation, test_path pointing to `tests/simulation_quality/test_evaluate_harness.py`.

---

## Risks and Open Questions

### Risk 1: `calibrate_simq.main()` calls `sys.exit()` on parse error
`argparse` calls `sys.exit(2)` on bad arguments. If `sys.argv` is patched incorrectly, this terminates the harness process. Mitigation: wrap inline calls in `try/except SystemExit` and re-raise as a meaningful error.

### Risk 2: `--dry-run` with missing calibration data
If `data/calibration/{run_key}/quality_report.json` does not exist, the harness must produce a `MISSING` status row, not crash. The table design (PASS / REGRESS / MISSING) already accounts for this. Exit code 0 on MISSING (warning, not error) per ticket spec.

### Risk 3: Exit code semantics — MISSING vs REGRESS vs setup error
Ticket spec: exit 0 = all PASS (MISSING = warning), exit 1 = any REGRESS, exit 2 = anchor file missing / invalid JSON / schema error. This must be carefully distinguished in `main()`. Do not conflate a missing calibration report (MISSING row, exit 0) with a missing anchor file (exit 2).

### Risk 4: ENABLE_ADVENTURE_ROUTING env var leakage
If the harness sets `os.environ["ENABLE_ADVENTURE_ROUTING"] = "ON"` for routing test keys and fails to restore it, subsequent scenarios in the same process run will pick up the flag spuriously. Always use a `try/finally` cleanup pattern.

### Risk 5: `calibrate_simq.main()` returns a report object but also writes to disk
In full mode, the harness can either (a) use the return value of `main()` directly, or (b) read back the JSON from disk after `main()` completes. Option (b) is safer because `main()` also writes the report file, and `--dry-run` already reads from disk. Using the same disk-read path in both modes simplifies `_run_scenario` logic.

### Open Question 1: Default scenario list in `evaluate_simq.py`
The ticket says "default list should mirror FAST_ANCHOR_KEYS". FAST_ANCHOR_KEYS has 14 entries. Should all 14 be the default for `make evaluate-full` (which re-runs the engine)? The 3 `simq_routing_test_*_500t` keys are 500-tick runs — potentially slow in full mode. Consider having `evaluate-full` default to only 200t fast keys and require `--scenario` for 500t routing test runs.

**Proposed resolution:** Keep all 14 FAST_ANCHOR_KEYS as the default. Document in `§11.4` that `evaluate-full` is not suitable for time-critical CI. The ticket spec does not distinguish within FAST_ANCHOR_KEYS.

### Open Question 2: How to handle pillar keys present in anchor but not in actual report
The anchor has 10 pillars. If a pillar is missing from the actual report, `_extract_pillar_grades` returns only the pillars that exist. The comparison loop should treat missing actual pillars as a MISSING row (not REGRESS), matching the "MISSING = warning" exit code 0 policy.

---

## Anti-Drift Hazards

1. **grade_anchors.json metadata keys:** The JSON has 3 underscore-prefixed metadata keys (`_note`, `_instructions`, `_grade_order`). The harness must skip these when iterating run keys (e.g., `if key.startswith("_"): continue`).
2. **FAST_ANCHOR_KEYS / SLOW_ANCHOR_KEYS divergence:** If `test_grade_regression.py` gains new entries, `evaluate_simq.py`'s hardcoded default list will drift. Add a comment in `evaluate_simq.py` pointing to `tests/simulation_quality/test_grade_regression.py::FAST_ANCHOR_KEYS` as the source of truth, so future readers know to keep them in sync.
3. **calibrate_simq.main() API stability:** `main()` currently returns the report object. If a future change makes it return `None` or call `sys.exit()`, the inline invocation path breaks. This is low risk but worth noting.
4. **Makefile `.PHONY` line:** The new `evaluate` and `evaluate-full` targets must be appended to the `.PHONY` declaration on line 1, or `make evaluate` will behave incorrectly if a file named `evaluate` ever exists in the repo root.
