---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2
artifact_type: test_plan
tags: [testing]
---

# Test plan — TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2

- B4: `tests/unit/tools/test_scenario_lane_paths.py` (routing fixtures, summary wording) and a new static exclusion test; a positive control proves the scanner flags a synthetic offending file and skips docstrings.
- B3: `tests/unit/tools/test_junit_cost_report.py` — empty, partial, multi-run, duplicate-artifact, overlapping nodes, missing-duration, absent directory, deterministic output.
- B2: core_rpg_report tests for supersedes/current selection and `selection-changed`; real mutmut run recorded as evidence, not a test.
- B1: existing doc/frontmatter validators; `tests/unit/tools` report tests pinned to `month_basis`.
- Commands: `.venv/bin/python -m pytest tests/unit/tools -k "lane or junit or core_rpg or impact" -q`, `make docs-registry-check`.

## Proof Plan

- level: unit (tooling; no RPG behaviour change)
- proof kind: deterministic unit tests with synthetic fixtures plus a positive control for the exclusion scanner
- oracle source: roadmap §6/§9 decisions of 2026-10-01 and the reviewer-approved plan (no Mechanics Bible rule applies)
- expected effect: exclusion guard fails on a dependency, routing statements are not execution records, cost view never reports 0 s for absent data, report picks the baseline by declared link
- selected commands: `.venv/bin/python -m pytest tests/unit/tools tests/docs -q`
