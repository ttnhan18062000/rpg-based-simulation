# Investigation — TCK-20260630-SIMQ-ANCHORS

## Current test_grade_regression.py structure

The existing file (at time of investigation) uses a different design than what the ticket specifies:

- **Format**: `grade_anchors.json` uses `{"sandbox_world": {"seed": 42, "ticks": 100, "pillars": {...}}}` — keyed by world name, not run_key
- **All grades are "UNKNOWN"** — the fixture was written as a stub, never populated
- **Tests are all `@pytest.mark.slow`** — they try to `import run_and_grade` from a Python fixture module and actually re-run the simulation (not read from calibration reports)
- **Two scenario tests**: `test_sandbox_world_grade_anchors`, `test_urban_political_grade_anchors`
- **One structural test**: `test_grade_anchor_file_exists_and_valid` which checks old schema (requires `seed`, `ticks`, `pillars` keys)

The INFRA-250 parity ledger entry records "4 skipped: 2 grade regression anchors UNKNOWN" — confirming the current state.

## Calibration data extracted from quality_report.json

All runs from `data/calibration/`. tick_count is actual ticks processed (simulation may end before the budget).

| run_key | tick_count | COMBAT | NARRATIVE | PROGRESSION | AGENCY | COGNITION | ECONOMY | FACTION | INFORMATION | SOCIAL | WORLD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sandbox_world_seed42_200t | 57 | B | A | B | C | C | C | C | C | C | C |
| sandbox_world_seed137_200t | 93 | B | A | C | C | C | C | C | C | C | C |
| sandbox_world_seed999_200t | 96 | B | A | C | C | C | C | C | C | C | C |
| dungeon_crawl_seed42_200t | 172 | A | B | A | C | C | C | C | C | C | A |
| dungeon_crawl_seed42_1000t | 988 | B | B | B | C | C | C | C | C | C | B |
| urban_political_seed42_200t | 198 | B | A | B | C | C | C | C | C | C | A |
| simq_routing_test_seed42_500t | 401 | B | A | B | B | C | C | C | C | C | B |
| sandbox_world_seed42_1000t | 968 | B | A | B | C | C | C | C | C | C | B |
| wilderness_survival_seed42_200t | 57 | A | S | B | C | C | C | C | C | C | C |

**Note:** wilderness_survival is excluded from the committed anchors. NARRATIVE=S on a 57-tick run is volatile (high event density on short run). Excluded per task scope — depends on TCK-20260630-SIMQ-CALFIX differentiation.

## quality_report.json structure

```json
{
  "run_id": "...",
  "tick_count": 57,
  "overall_score": 0.207,
  "overall_grade": "B",
  "pillars": {
    "COMBAT": {
      "raw_score": 26.0,
      "normalized_score": 0.456,
      "grade": "B",
      ...
    }
  }
}
```

`_extract_pillar_grades(report)` → `{pillar: report["pillars"][pillar]["grade"] for pillar in report["pillars"]}`.

## Which runs have signal (non-C for ≥1 pillar)

All 8 runs have signal. Anchors worth committing for differentiation:
- **dungeon_crawl_seed42_200t**: COMBAT=A, PROGRESSION=A, WORLD=A (strongest differentiation)
- **simq_routing_test_seed42_500t**: AGENCY=B (unique — only run with AGENCY > C)
- **urban_political_seed42_200t**: WORLD=A (significant)
- **sandbox_world_seed42_200t**: PROGRESSION=B (seed42 differs from 137/999)

## Discrepancy from ticket scope table

The ticket scope table stated sandbox_world seed42/200t PROGRESSION=C and seed999/200t PROGRESSION=B.
Actual calibration data disagrees: seed42=B, seed999=C. Ticket was written with estimates.
Implementation uses actual calibration data as authoritative.
