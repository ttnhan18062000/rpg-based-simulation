# TCK-20260702-SIMQ-EVAL-MATRIX — Implementation Plan

**Date:** 2026-07-02
**Ticket:** TCK-20260702-SIMQ-EVAL-MATRIX
**Phase:** Plan (seq 3)

---

## Overview

Data collection and documentation ticket. No source code changes. Seventeen new calibration runs expand the corpus from single-seed point estimates to a multi-seed, multi-tick matrix covering all signal-producing worlds. The resulting grade distributions are committed to `grade_anchors.json`, wired into `test_grade_regression.py`, and documented.

The grade_anchors.json and FAST/SLOW key list expansions must happen atomically (see CRITICAL constraint below). All other steps have a clear dependency chain.

---

## Ordered Steps

### Step 1 — Run fast calibration: simq_routing_test seeds 123 and 456 (500t, ENABLE_ADVENTURE_ROUTING=ON)

**Rationale:** AC6 requires AGENCY ≥ B for all three seeds. Run these first to surface any ENABLE_ADVENTURE_ROUTING failure early.

**Commands:**
```bash
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --name simq_routing_test --seed 123 --ticks 500
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --name simq_routing_test --seed 456 --ticks 500
```

**Output directories:**
- `data/calibration/simq_routing_test_seed123_500t/quality_report.json`
- `data/calibration/simq_routing_test_seed456_500t/quality_report.json`

**Verify:** Each report must have AGENCY grade ∈ {A, B, S}. Use the AGENCY spot check from test_plan.md §2c. If either seed yields AGENCY=C, the ENABLE_ADVENTURE_ROUTING flag was not active — rerun with the flag explicitly before proceeding.

**Fallback:** If seed 123 or 456 produces early_extinction at tick < 50, substitute 789 and 999 respectively per ticket §Assumptions.

**AC mapping:** AC6

---

### Step 2 — Run fast calibration: dungeon_crawl 500t, seeds 42 / 123 / 456

**Rationale:** Baseline 500t snapshot for dungeon_crawl across three seeds. All are new (500t tick count does not yet exist in corpus for any seed).

**Commands:**
```bash
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 500
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 123 --ticks 500
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 456 --ticks 500
```

**Output directories:**
- `data/calibration/dungeon_crawl_seed42_500t/quality_report.json`
- `data/calibration/dungeon_crawl_seed123_500t/quality_report.json`
- `data/calibration/dungeon_crawl_seed456_500t/quality_report.json`

**Verify:** Each report exists with `run_metadata.ticks = 500` and 10 pillars present.

**AC mapping:** AC1

---

### Step 3 — Run fast calibration: urban_political 500t, seeds 42 / 123 / 456

**Rationale:** Baseline 500t snapshot for urban_political. Like dungeon_crawl, the 500t tick count is entirely new for all seeds.

**Commands:**
```bash
python3 tools/calibrate_simq.py --name urban_political --seed 42 --ticks 500
python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 500
python3 tools/calibrate_simq.py --name urban_political --seed 456 --ticks 500
```

**Output directories:**
- `data/calibration/urban_political_seed42_500t/quality_report.json`
- `data/calibration/urban_political_seed123_500t/quality_report.json`
- `data/calibration/urban_political_seed456_500t/quality_report.json`

**Verify:** Each report exists with `run_metadata.ticks = 500` and 10 pillars present.

**AC mapping:** AC1

---

### Step 4 — Run slow calibration: dungeon_crawl 1000t, seeds 123 and 456 (seed 42 already in corpus)

**Rationale:** `dungeon_crawl_seed42_1000t` already exists and is in SLOW_ANCHOR_KEYS. Only seeds 123 and 456 are new at 1000t.

**Do NOT re-run `dungeon_crawl_seed42_1000t`** — it is already in the corpus. Running it again would overwrite an established anchor without justification.

**Commands:**
```bash
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 123 --ticks 1000
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 456 --ticks 1000
```

**Output directories:**
- `data/calibration/dungeon_crawl_seed123_1000t/quality_report.json`
- `data/calibration/dungeon_crawl_seed456_1000t/quality_report.json`

**Verify:** Each report exists with `run_metadata.ticks = 1000` and 10 pillars present.

**AC mapping:** AC1

---

### Step 5 — Run slow calibration: urban_political 1000t, seeds 42 / 123 / 456

**Rationale:** 1000t snapshot for urban_political to observe OQ1 — whether NARRATIVE, COMBAT, PROGRESSION, WORLD grades hold or drift from the 200t/500t baseline. All three seeds are new at this tick count.

**Commands:**
```bash
python3 tools/calibrate_simq.py --name urban_political --seed 42 --ticks 1000
python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000
python3 tools/calibrate_simq.py --name urban_political --seed 456 --ticks 1000
```

**Output directories:**
- `data/calibration/urban_political_seed42_1000t/quality_report.json`
- `data/calibration/urban_political_seed123_1000t/quality_report.json`
- `data/calibration/urban_political_seed456_1000t/quality_report.json`

**Verify:** Each report exists with `run_metadata.ticks = 1000` and 10 pillars present. Note NARRATIVE and COMBAT grades for OQ1.

**AC mapping:** AC1

---

### Step 6 — Run slow calibration: dungeon_crawl 2000t, seeds 42 / 123 / 456

**Rationale:** Long-run snapshot for dungeon_crawl. Primary purpose: observe Risk R3 (COMBAT grade drift at 2000t) and establish 2000t anchors for the dungeon_crawl world.

**Wall-time risk:** Estimated ~4–5 min per run at ~25s/200t. Total ~12–15 min for all three. If any single run exceeds 90s/200t, cap at 1500t and document the reduction in eval_matrix_results.md.

**Commands:**
```bash
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 123 --ticks 2000
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 456 --ticks 2000
```

**Output directories:**
- `data/calibration/dungeon_crawl_seed42_2000t/quality_report.json`
- `data/calibration/dungeon_crawl_seed123_2000t/quality_report.json`
- `data/calibration/dungeon_crawl_seed456_2000t/quality_report.json`

**Verify:** Each report exists. Check `run_metadata.ticks` — if capped at 1500t, the run_key directory name uses the actual tick count (or document the discrepancy). Check COMBAT grade for drift from 1000t baseline.

**AC mapping:** AC1

---

### Step 7 — Run slow calibration: sandbox_world 2000t, seed 42

**Rationale:** OQ2 — whether COGNITION and ECONOMY climb above B or plateau beyond the 1000t snapshot. sandbox_world has no seed multiplication requirement (single-seed long-run trend is sufficient).

**Commands:**
```bash
python3 tools/calibrate_simq.py --name sandbox_world --seed 42 --ticks 2000
```

**Output directory:**
- `data/calibration/sandbox_world_seed42_2000t/quality_report.json`

**Verify:** Report exists with `run_metadata.ticks = 2000` and 10 pillars. Check COGNITION and ECONOMY grades for OQ2.

**AC mapping:** AC1

---

### Step 8 — Update grade_anchors.json and test_grade_regression.py ATOMICALLY

**CRITICAL CONSTRAINT:** `MINIMUM_FAST_ANCHORS = set(FAST_ANCHOR_KEYS)` is recalculated at import time. If any key is added to `FAST_ANCHOR_KEYS` without a corresponding entry in `grade_anchors.json`, `test_grade_anchor_file_exists_and_valid` will fail. Both files must be updated together and committed together.

**Substep 8a — Verify all 17 calibration reports are complete.**

Run the Guard G5 integrity check from test_plan.md §4:
```bash
python3 -c "
import json, pathlib
for key in [
    'simq_routing_test_seed123_500t',
    'simq_routing_test_seed456_500t',
    'dungeon_crawl_seed42_500t',
    'dungeon_crawl_seed123_500t',
    'dungeon_crawl_seed456_500t',
    'urban_political_seed42_500t',
    'urban_political_seed123_500t',
    'urban_political_seed456_500t',
    'dungeon_crawl_seed123_1000t',
    'dungeon_crawl_seed456_1000t',
    'urban_political_seed42_1000t',
    'urban_political_seed123_1000t',
    'urban_political_seed456_1000t',
    'dungeon_crawl_seed42_2000t',
    'dungeon_crawl_seed123_2000t',
    'dungeon_crawl_seed456_2000t',
    'sandbox_world_seed42_2000t',
]:
    p = pathlib.Path(f'data/calibration/{key}/quality_report.json')
    if not p.exists():
        print(f'MISSING: {key}')
        continue
    r = json.loads(p.read_text())
    pillars = r.get('pillars', {})
    ticks = r.get('run_metadata', {}).get('ticks', '?')
    print(f'OK ({ticks}t, {len(pillars)} pillars): {key}')
"
```
All 17 lines must show `OK`. If any show MISSING, do not proceed with this step.

**Substep 8b — Extract empirical grades from each new run_key.**

For each of the 17 new run_keys:
```bash
python3 -c "
import json, pathlib, sys
run_key = sys.argv[1]
p = pathlib.Path(f'data/calibration/{run_key}/quality_report.json')
report = json.loads(p.read_text())
grades = {k: v['grade'] for k, v in report['pillars'].items()}
print(json.dumps({run_key: grades}, indent=2))
" <run_key>
```
Never guess or interpolate grades from adjacent seeds. Always extract from the actual report.

**Substep 8c — Add all 17 new entries to grade_anchors.json.**

File: `tests/simulation_quality/fixtures/grade_anchors.json`

Append extracted grades for each of the 17 run_keys. No existing entries should be modified. The file already has 8 entries (6 FAST + 2 SLOW); after this step it should have 25 entries.

**Substep 8d — Add new run_keys to FAST_ANCHOR_KEYS in test_grade_regression.py.**

File: `tests/simulation_quality/test_grade_regression.py`

Add the following 8 new fast keys (append after the existing 6, grouped by world for readability):
```python
# new — simq_routing_test additional seeds
"simq_routing_test_seed123_500t",
"simq_routing_test_seed456_500t",
# new — dungeon_crawl 500t
"dungeon_crawl_seed42_500t",
"dungeon_crawl_seed123_500t",
"dungeon_crawl_seed456_500t",
# new — urban_political 500t
"urban_political_seed42_500t",
"urban_political_seed123_500t",
"urban_political_seed456_500t",
```
Result: FAST_ANCHOR_KEYS grows from 6 to 14 entries.

**Substep 8e — Add new run_keys to SLOW_ANCHOR_KEYS in test_grade_regression.py.**

Add the following 9 new slow keys (append after the existing 2, grouped by world and tick count):
```python
# new — dungeon_crawl 1000t
"dungeon_crawl_seed123_1000t",
"dungeon_crawl_seed456_1000t",
# new — urban_political 1000t
"urban_political_seed42_1000t",
"urban_political_seed123_1000t",
"urban_political_seed456_1000t",
# new — dungeon_crawl 2000t
"dungeon_crawl_seed42_2000t",
"dungeon_crawl_seed123_2000t",
"dungeon_crawl_seed456_2000t",
# new — sandbox_world 2000t
"sandbox_world_seed42_2000t",
```
Result: SLOW_ANCHOR_KEYS grows from 2 to 11 entries.

**Do not add 1000t/2000t keys to FAST_ANCHOR_KEYS** — they are governed by `test_grade_within_anchor_band_long_run` (marked `@pytest.mark.slow`).

**AC mapping:** AC2, AC3

---

### Step 9 — Run tests to validate

**Pre-condition:** Step 8 fully complete — both `grade_anchors.json` and `test_grade_regression.py` updated.

**Fast suite (structural sanity + all 14 fast parametrize entries):**
```bash
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v
```
Expected: 14 fast entries pass, 0 skips, 0 failures. The structural sanity test (`test_grade_anchor_file_exists_and_valid`) must also pass.

**Slow suite (all 11 slow parametrize entries):**
```bash
pytest tests/simulation_quality/test_grade_regression.py -m slow -v
```
Expected: 11 slow entries pass, 0 skips, 0 failures.

**AGENCY spot-check (AC6):**
```bash
pytest tests/simulation_quality/test_grade_regression.py \
  -k "simq_routing_test_seed123 or simq_routing_test_seed456" -v -m "not slow"
```
Both must pass (not skip). If AGENCY is not within band (anchor=B, actual must be A/B/C), investigate R4.

**AC mapping:** AC4, AC6

---

### Step 10 — Write docs/simulation_quality/eval_matrix_results.md

**Pre-condition:** All 17 calibration runs complete and grades verified (Step 8a passes).

**File:** `docs/simulation_quality/eval_matrix_results.md` (new file — does not yet exist)

**Required content:**
1. Header with ticket reference and date.
2. Per-world per-pillar grade distribution table. For each world × tick count combination, show: min grade / max grade / mode grade across seeds. Only show non-C pillars unless all pillars are C.
3. Sections in this order:
   - `dungeon_crawl` — 500t (seeds 42/123/456), 1000t (all seeds including seed42), 2000t (all seeds)
   - `urban_political` — 500t (all seeds), 1000t (all seeds)
   - `simq_routing_test` — 500t (all three seeds, ENABLE_ADVENTURE_ROUTING=ON), with dedicated AGENCY column showing per-seed grade
   - `sandbox_world` — 2000t (seed 42), COGNITION/ECONOMY trend vs. 1000t baseline
4. Stability analysis paragraph per world: are the active pillars stable across seeds (all same grade), mildly variable (±1 letter), or unstable?
5. OQ1 resolution: what happened to urban_political NARRATIVE at 1000t?
6. OQ2 resolution: what happened to sandbox_world COGNITION/ECONOMY at 2000t vs. 1000t?
7. AC6 confirmation: AGENCY ≥ B confirmed for all three simq_routing_test seeds.

**AC mapping:** AC5

---

### Step 11 — Update docs/audits/D20_simq_integration.md

**Pre-condition:** Step 10 complete (grades documented, OQ resolutions in hand).

**File:** `docs/audits/D20_simq_integration.md`

Add a new subsection at the bottom of the "Calibration results" section (after the existing "Calibration results — richer worlds (2026-07-02, TCK-20260701-SIMQ-CALIBRATE-REFRESH)" subsection):

```
### Multi-seed / multi-tick matrix (2026-07-02, TCK-20260702-SIMQ-EVAL-MATRIX)
```

Include:
- Summary matrix table showing corpus expansion: before (8 anchor entries) → after (25 anchor entries)
- Brief per-world stability conclusion (copy from eval_matrix_results.md §stability)
- OQ1 and OQ2 resolution one-liners
- AC6 AGENCY confirmation for simq_routing_test

Do not modify any other section of the audit document.

**AC mapping:** AC7

---

### Step 12 — Update ticket Implementation Notes and Files Changed

**File:** `tickets/inprogress/TCK-20260702-SIMQ-EVAL-MATRIX.md`

Update:
- `## Implementation Notes` — add summary of any OQ resolutions, fallback seeds used (if any), or wall-time caps applied.
- `## Files Changed` — confirm the exact list matches what was written (17 calibration dirs + 2 fixture/test files + 2 doc files).

After implementation, the ticket finalize phase will fill `## Completion Summary` and move to `tickets/done/`.

**AC mapping:** None directly — bookkeeping step.

---

## Scope Guards

- Do NOT change any source code files (`tools/calibrate_simq.py`, `src/`)
- Do NOT change grade thresholds or scoring weights in the scorer
- Do NOT run calibration for worlds with confirmed zero-pillar signal in default mode (wilderness_survival, highland_traverse, swamp_border_world, frontier_extended, frontier_living_world)
- Do NOT re-run `dungeon_crawl_seed42_1000t` — it is already in corpus and in SLOW_ANCHOR_KEYS
- Do NOT add 1000t or 2000t run_keys to FAST_ANCHOR_KEYS (wrong test function)
- Do NOT set anchor grades speculatively — extract empirically from quality_report.json only
- Do NOT commit FAST_ANCHOR_KEYS expansion without the corresponding grade_anchors.json entries

---

## Dependency Map

```
Steps 1–7:  independent (can run in any order — all are calibration runs with no inter-dependency)
Step 8:     depends on ALL of steps 1–7 (needs all 17 reports)
Step 9:     depends on step 8
Step 10:    depends on step 8 (needs grades), step 9 preferred (want test confirmation first)
Step 11:    depends on step 10
Step 12:    depends on steps 10–11
```

Steps 1–7 may be parallelized if tooling supports concurrent calibration runs. Steps 8–12 are strictly sequential.

---

## AC Mapping Summary

| Acceptance Criterion | Covered By |
|---|---|
| AC1 — all matrix runs complete with quality_report.json | Steps 1–7 |
| AC2 — grade_anchors.json has entries for all 17 new run_keys | Step 8c |
| AC3 — test_grade_regression.py FAST/SLOW lists include all new keys | Steps 8d, 8e |
| AC4 — pytest passes for all new parametrize entries | Step 9 |
| AC5 — eval_matrix_results.md exists with per-pillar grade distribution table | Step 10 |
| AC6 — AGENCY ≥ B for simq_routing_test seeds 123 and 456 | Steps 1, 9 |
| AC7 — D20 audit "Calibration results" updated with matrix summary | Step 11 |

---

## New Run Keys Reference (17 total)

**FAST (≤500t) — 8 new:**
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

**SLOW (≥1000t) — 9 new:**
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
