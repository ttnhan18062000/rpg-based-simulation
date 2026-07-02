# TCK-20260702-SIMQ-EVAL-MATRIX — Investigation

**Date:** 2026-07-02
**Ticket:** TCK-20260702-SIMQ-EVAL-MATRIX
**Phase:** Investigation (seq 2)

---

## 1. Current Calibration Corpus

Current `data/calibration/` contents (13 entries as of investigation date):

| run_key | Tick count | Anchor list |
|---|---|---|
| `sandbox_world_seed42_200t` | 200t | FAST |
| `sandbox_world_seed137_200t` | 200t | FAST |
| `sandbox_world_seed999_200t` | 200t | FAST |
| `dungeon_crawl_seed42_200t` | 200t | FAST |
| `urban_political_seed42_200t` | 200t | FAST |
| `simq_routing_test_seed42_500t` | 500t | FAST |
| `dungeon_crawl_seed42_1000t` | 1000t | SLOW |
| `sandbox_world_seed42_1000t` | 1000t | SLOW |
| `frontier_extended_seed42_200t` | 200t | not in anchor lists |
| `frontier_living_world_seed42_200t` | 200t | not in anchor lists |
| `highland_traverse_seed42_200t` | 200t | not in anchor lists |
| `swamp_border_world_seed42_200t` | 200t | not in anchor lists |
| `wilderness_survival_seed42_200t` | 200t | not in anchor lists |

The 5 non-anchor entries (frontier_extended, frontier_living_world, highland_traverse, swamp_border_world, wilderness_survival) are zero-pillar or low-signal worlds not required by the matrix. They are ignored for this ticket.

Grade anchor file (`tests/simulation_quality/fixtures/grade_anchors.json`) has exactly 8 entries: the 6 FAST keys and 2 SLOW keys listed above.

Key observed grades for reference:
- `dungeon_crawl_seed42_200t`: COMBAT=A, NARRATIVE=B, PROGRESSION=B, WORLD=A; others C
- `dungeon_crawl_seed42_1000t`: COMBAT=B, NARRATIVE=B, PROGRESSION=B, WORLD=B; others C
- `urban_political_seed42_200t`: COMBAT=B, NARRATIVE=A, PROGRESSION=B, WORLD=A; others C
- `simq_routing_test_seed42_500t`: COMBAT=B, NARRATIVE=A, PROGRESSION=B, AGENCY=B, WORLD=B; others C
- `sandbox_world_seed42_1000t`: COMBAT=B, NARRATIVE=A, PROGRESSION=B, COGNITION=B, ECONOMY=B, WORLD=B; others C

---

## 2. Run Matrix

### Full matrix — all run_keys, existence status, and list assignment

| run_key | Ticks | Env flag | Already exists? | Target list |
|---|---|---|---|---|
| `simq_routing_test_seed42_500t` | 500t | ENABLE_ADVENTURE_ROUTING=ON | YES | FAST (already in list) |
| `simq_routing_test_seed123_500t` | 500t | ENABLE_ADVENTURE_ROUTING=ON | NO — **must run** | FAST |
| `simq_routing_test_seed456_500t` | 500t | ENABLE_ADVENTURE_ROUTING=ON | NO — **must run** | FAST |
| `dungeon_crawl_seed42_500t` | 500t | none | NO — **must run** | FAST |
| `dungeon_crawl_seed123_500t` | 500t | none | NO — **must run** | FAST |
| `dungeon_crawl_seed456_500t` | 500t | none | NO — **must run** | FAST |
| `urban_political_seed42_500t` | 500t | none | NO — **must run** | FAST |
| `urban_political_seed123_500t` | 500t | none | NO — **must run** | FAST |
| `urban_political_seed456_500t` | 500t | none | NO — **must run** | FAST |
| `dungeon_crawl_seed42_1000t` | 1000t | none | YES | SLOW (already in list) |
| `dungeon_crawl_seed123_1000t` | 1000t | none | NO — **must run** | SLOW |
| `dungeon_crawl_seed456_1000t` | 1000t | none | NO — **must run** | SLOW |
| `urban_political_seed42_1000t` | 1000t | none | NO — **must run** | SLOW |
| `urban_political_seed123_1000t` | 1000t | none | NO — **must run** | SLOW |
| `urban_political_seed456_1000t` | 1000t | none | NO — **must run** | SLOW |
| `dungeon_crawl_seed42_2000t` | 2000t | none | NO — **must run** | SLOW |
| `dungeon_crawl_seed123_2000t` | 2000t | none | NO — **must run** | SLOW |
| `dungeon_crawl_seed456_2000t` | 2000t | none | NO — **must run** | SLOW |
| `sandbox_world_seed42_2000t` | 2000t | none | NO — **must run** | SLOW |

### Summary counts

- Already exists and already in anchor lists: 2 (`simq_routing_test_seed42_500t`, `dungeon_crawl_seed42_1000t`)
- Already exists, NOT yet in anchor lists: 0
- Must run (new): **17**

Note: `dungeon_crawl_seed42_200t`, `dungeon_crawl_seed42_1000t`, `urban_political_seed42_200t` are in corpus but are 200t/1000t entries, not the new 500t/2000t runs. The ticket explicitly calls for new tick-count granularity, not re-use of those entries as matrix representatives.

### Exact new run_keys to create (17 total)

```
simq_routing_test_seed123_500t
simq_routing_test_seed456_500t
dungeon_crawl_seed42_500t
dungeon_crawl_seed123_500t
dungeon_crawl_seed456_500t
urban_political_seed42_500t
urban_political_seed123_500t
urban_political_seed456_500t
dungeon_crawl_seed123_1000t
dungeon_crawl_seed456_1000t
urban_political_seed42_1000t
urban_political_seed123_1000t
urban_political_seed456_1000t
dungeon_crawl_seed42_2000t
dungeon_crawl_seed123_2000t
dungeon_crawl_seed456_2000t
sandbox_world_seed42_2000t
```

### Run order (fast first, as specified in ticket Implementation Notes)

1. `simq_routing_test` seed 123, 456 at 500t (ENABLE_ADVENTURE_ROUTING=ON)
2. `dungeon_crawl` seed 42, 123, 456 at 500t
3. `urban_political` seed 42, 123, 456 at 500t
4. `dungeon_crawl` seed 123, 456 at 1000t
5. `urban_political` seed 42, 123, 456 at 1000t
6. `dungeon_crawl` seed 42, 123, 456 at 2000t (slow)
7. `sandbox_world` seed 42 at 2000t (slow)

---

## 3. World Spec Availability

All four worlds confirmed to have `resolved/` subdirectories under `data/worlds/`:

| World | Path | Status |
|---|---|---|
| `dungeon_crawl` | `data/worlds/dungeon_crawl/resolved/` | confirmed |
| `urban_political` | `data/worlds/urban_political/resolved/` | confirmed |
| `simq_routing_test` | `data/worlds/simq_routing_test/resolved/` | confirmed |
| `sandbox_world` | `data/worlds/sandbox_world/resolved/` | confirmed |

Each world dir also contains `world.yaml` and `world_compile_report.json`. No blockers on world spec availability.

---

## 4. Test Structure

### Current state

`tests/simulation_quality/test_grade_regression.py` defines:

```python
FAST_ANCHOR_KEYS = [
    "sandbox_world_seed42_200t",
    "sandbox_world_seed137_200t",
    "sandbox_world_seed999_200t",
    "dungeon_crawl_seed42_200t",
    "urban_political_seed42_200t",
    "simq_routing_test_seed42_500t",   # already present
]

SLOW_ANCHOR_KEYS = [
    "dungeon_crawl_seed42_1000t",      # already present
    "sandbox_world_seed42_1000t",
]
```

`MINIMUM_FAST_ANCHORS` is derived from `set(FAST_ANCHOR_KEYS)` and is asserted in the structural sanity test — this must remain correct after additions.

### New keys — list assignment

**FAST_ANCHOR_KEYS additions (≤500t):**
```
simq_routing_test_seed123_500t
simq_routing_test_seed456_500t
dungeon_crawl_seed42_500t
dungeon_crawl_seed123_500t
dungeon_crawl_seed456_500t
urban_political_seed42_500t
urban_political_seed123_500t
urban_political_seed456_500t
```

**SLOW_ANCHOR_KEYS additions (≥1000t):**
```
dungeon_crawl_seed123_1000t
dungeon_crawl_seed456_1000t
urban_political_seed42_1000t
urban_political_seed123_1000t
urban_political_seed456_1000t
dungeon_crawl_seed42_2000t
dungeon_crawl_seed123_2000t
dungeon_crawl_seed456_2000t
sandbox_world_seed42_2000t
```

### Anchor skip behavior

The existing test infrastructure auto-skips any parametrized run_key whose calibration report file or grade_anchors.json entry is missing. This means:
- New keys can be safely added to the lists before calibration runs complete — tests will skip rather than fail.
- After calibration completes and grade_anchors.json is populated, tests become active.
- The structural sanity test (`test_grade_anchor_file_exists_and_valid`) only asserts `MINIMUM_FAST_ANCHORS` — it does NOT enforce the new fast keys, since `MINIMUM_FAST_ANCHORS = set(FAST_ANCHOR_KEYS)` is recalculated at import time from the updated list. This is correct and is the intended design.

### Important: MINIMUM_FAST_ANCHORS consequence

After adding new keys to `FAST_ANCHOR_KEYS`, `MINIMUM_FAST_ANCHORS` will automatically expand. This means `test_grade_anchor_file_exists_and_valid` will require entries for all new fast keys in grade_anchors.json. Sequence matters: add list entries and grade_anchors.json entries together in the same commit.

---

## 5. Docs Structure

### Existing docs in `docs/simulation_quality/`

```
event_type_coverage.md
quality_scoring_contract.md
```

`eval_matrix_results.md` does NOT exist — it is a new file to be created in this ticket.

### New docs required

1. **`docs/simulation_quality/eval_matrix_results.md`** (new)
   - Per-pillar grade distribution table: min/max/mode across seeds for each tick count
   - Sections: dungeon_crawl (500t, 1000t, 2000t), urban_political (500t, 1000t), simq_routing_test (500t), sandbox_world (2000t)
   - AGENCY stability column for simq_routing_test (all three seeds must show ≥ B)
   - Status: Created AFTER calibration runs complete and grades are extracted

2. **`docs/audits/D20_simq_integration.md`** — update existing "Calibration results" section
   - Already located at line ~348 ("Calibration results — richer worlds (2026-07-02, TCK-20260701-SIMQ-CALIBRATE-REFRESH)")
   - Add new subsection: "Multi-seed/multi-tick matrix (2026-07-02, TCK-20260702-SIMQ-EVAL-MATRIX)"
   - Include summary table of matrix results

### §11.3 anchor update workflow (from quality_scoring_contract.md)

The contract section describes the intended workflow as:
1. Re-run calibration (`make calibrate` or per-scenario variant)
2. Inspect new grades in `data/calibration/<run_key>/quality_report.json`
3. Edit `tests/simulation_quality/fixtures/grade_anchors.json` with new grades
4. Run test file to confirm all pass
5. Commit fixture and calibration data together

Note: §11.3 in the contract doc is legacy prose (references old 100-tick scenarios). The actual authoritative workflow is captured in the test file's module docstring and the grade_anchors.json `_instructions` field. No discrepancy — both say the same thing.

---

## 6. Risks and Open Questions

### Risk R1 — Seed collision / early extinction
Ticket assumption: seeds 123 and 456 are valid. Mitigation: if a seed produces `early_extinction` at tick < 50, substitute 789 and 999 respectively (per ticket §Assumptions). Evidence so far: the `early_extinction` penalty was caused by `sandbox_world`-specific hazard drain bugs (resolved in TCK-20260701-SANDBOX-MONSTER-BALANCE + TCK-20260701-HAZARD-NATIVE-IMMUNITY). `dungeon_crawl` and `urban_political` have no comparable structural hazard issue, so early extinction risk is low for those worlds.

### Risk R2 — 2000t wall time
Ticket estimates ~25s/200t → ~250s (~4.2 min) per 2000t run. Three dungeon_crawl 2000t runs = ~12.5 min plus sandbox_world 2000t = ~17 min for the slowest tier. Total matrix estimated at 20–25 min. If any run exceeds 90s/200t, cap at 1500t and document in eval_matrix_results.md.

### Risk R3 — Grade drift across seeds
dungeon_crawl at 200t shows COMBAT=A, at 1000t COMBAT=B (one-step drop). At 2000t COMBAT may drift further (to B or C). This is expected behavior. The band-tolerance test (±1 letter) accommodates normal drift. Risk: if COMBAT drops to C at 2000t seed42 while anchor is set to B, that would fail. Mitigation: set anchors empirically after runs complete, not speculatively.

### Risk R4 — AGENCY consistency for simq_routing_test
Acceptance criterion 6 requires AGENCY ≥ B for all three seeds at 500t with ENABLE_ADVENTURE_ROUTING=ON. The existing seed42 run confirms B. Seeds 123 and 456 are untested. If AGENCY drops to C for either non-42 seed, investigate AdventureDecisionPhase behavior under those seeds before committing anchors.

### Risk R5 — MINIMUM_FAST_ANCHORS enforcement order
`test_grade_anchor_file_exists_and_valid` will fail if new FAST_ANCHOR_KEYS entries are in the list but not yet in grade_anchors.json. The list update and grade_anchors.json population must be committed atomically. Do not commit the list expansion without the corresponding anchor entries.

### Open Question OQ1 — urban_political 1000t signal
urban_political at 200t shows COMBAT=B, NARRATIVE=A, PROGRESSION=B, WORLD=A. It is unknown whether these grades hold or drift at 1000t. Investigate once runs complete; if NARRATIVE drops below B at 1000t that should be noted in eval_matrix_results.md.

### Open Question OQ2 — sandbox_world 2000t COGNITION/ECONOMY
sandbox_world at 1000t shows COGNITION=B, ECONOMY=B (both rise from C at 200t). It is an open question whether these continue to climb at 2000t or plateau. This data point is the primary purpose of the sandbox_world 2000t run.

---

## 7. Anti-Drift Hazards

These are patterns that could cause silent test pass / silent corpus rot:

1. **Phantom skips**: If grade_anchors.json entries are added with wrong grades (e.g., copied from another run_key), tests will silently pass even if the calibration data shows a true regression. Mitigation: always extract grades from the actual `quality_report.json` file, not by guessing from adjacent seeds.

2. **Stale calibration data**: If `data/calibration/{run_key}/quality_report.json` already exists from an aborted/partial run, `calibrate_simq.py` may overwrite it or may skip. Verify each run_key directory is either absent before running or produced by a clean run (check `run_metadata.ticks` in the report).

3. **MINIMUM_FAST_ANCHORS silent expansion**: Adding keys to FAST_ANCHOR_KEYS without adding to grade_anchors.json will cause `test_grade_anchor_file_exists_and_valid` to fail. This is a safety net, not a hazard — but it means the structural test must be run in CI after any list expansion.

4. **ENABLE_ADVENTURE_ROUTING leakage**: If a simq_routing_test run is executed without the env flag set, AGENCY will score C instead of B. The run_key will look identical but the data will be wrong. Mitigation: always use `ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py ...` for all simq_routing_test runs, never omit the flag.

5. **dungeon_crawl_seed42_1000t re-run**: This key already exists in corpus and in SLOW_ANCHOR_KEYS. Do NOT re-run it unless a deliberate anchor refresh is intended. The ticket's Implementation Notes already mark it "(may already exist)" — skip it.
