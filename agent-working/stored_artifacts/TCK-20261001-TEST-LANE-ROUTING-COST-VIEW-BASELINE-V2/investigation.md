---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2

## Findings so far
- `tools/test_architecture/scenario_lane_paths.py`: `IRRELEVANT_RE` includes `tools/` and `registries/`; nothing enforces that scenario-reachable code never reads them (#271's stored investigation.md lines 22-30 found no dependency by audit trace only).
- Workflow step at `.github/workflows/test.yml` ~657 passes `--perf-covers`; `render_summary` says "runs in perf-cert-arena (no separate job)" which is a routing statement.
- `core_rpg_report.py:586` `month_basis` says "includes open tickets under todos/ and inprogress/", read as "only"; the code rglobs all tickets incl. done/.
- Baseline v1: `tests/mutation/baselines/src_core_conservation.json`, 60/177 killed, stale after 2026-10-30.

## External-findings disposition table
(to be completed with the seven rows from the reviewer handoff as each lands)

| # | Finding | Disposition | Where |
|---|---|---|---|
| 1 | Close B/C only against existing criteria; promotion separate | Confirmed / already addressed; no new criteria added | B1 |
| 2a | Irrelevant `tools/` etc. weakens fail-open | Partly confirmed (no dependency today; exclusion not enforced) | B4 |
| 2b | Routing must report execution, not suppression | Confirmed | B4 |
| 3 | Epic D closure must keep its limits | Confirmed | B1 |
| 4 | B2 details | Done: v2 record with metadata, declared `supersedes`, `selection-changed`, real mutmut run (177 / 152 killed / 25 survived, 460 s), positive control reused with three recorded equality checks | B2 |

## B4 decision
Chose the AST scan over the static import closure from scenario code (454 files reachable, zero hits) instead of scanning all of src/: all-of-src flagged 9 hits in 6 files (src/api dashboard, src/lab, src/certification harness, src/engine/capability), none imported by any scenario, which exceeded a handful for the allowlist. The closure scan keeps an empty allowlist. Limit: dynamic imports are not followed. `tools/` was therefore not narrowed.
| 5 | Cost view covers all JUnit dirs; label "observed test duration" | Confirmed | B3 |
| 6 | Pilot ticket by ownership/stability | Deferred to P | P |
| 7 | Escaped-defect metric wording | Reviewer MISTAKEN on logic; wording reads as "only" | B1 |
