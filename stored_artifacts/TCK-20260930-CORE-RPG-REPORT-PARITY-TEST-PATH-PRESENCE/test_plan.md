---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE
artifact_type: test_plan
tags: [testing]
---

# Test Plan

## Regression Surface
`tests/unit/tools/test_impact_report.py`, `tests/unit/tools/test_core_rpg_report.py`, `tests/unit/tools/test_marker_vocabulary.py`, `tests/unit/tools/test_marker_check.py`.

## New Tests Required
1 new test in `tests/unit/tools/test_core_rpg_report.py`.

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| all | unit | regression | pilot report `docs/testing/core_rpg_test_pilot_2026-09-30.md` (tooling behaviour; no Bible law) | see tests | `pytest tests/unit/tools/test_impact_report.py tests/unit/tools/test_core_rpg_report.py tests/unit/tools/test_marker_vocabulary.py tests/unit/tools/test_marker_check.py` |

## Scoped Pytest Commands
As above.

## Anti-Drift Test Guards
A plain substrate module stays substrate-only; declared markers never override another rule's result.
