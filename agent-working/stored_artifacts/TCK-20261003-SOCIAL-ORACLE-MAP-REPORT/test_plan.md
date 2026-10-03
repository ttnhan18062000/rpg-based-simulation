---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-ORACLE-MAP-REPORT
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261003-SOCIAL-ORACLE-MAP-REPORT

## Proof Plan
- level: report from a read-only analysis (no test added or changed)
- proof kind: counts and lists derived from the ledger file by script, reproducible at the stated SHA
- oracle source: `docs/parity_ledger/social_narrative.yaml` itself, plus the source lines named
- expected effect: the plan's counts (227 P0, 211 without `test_path`) re-confirmed or any difference stated
- selected commands:

| Check | Command | Expected |
|---|---|---|
| Ledger counts and lists | a read-only `yaml.safe_load` script over `docs/parity_ledger/social_narrative.yaml` | 294 entries, 227 P0, 211 P0 without `test_path` |
| Cited test files exist | same script, `Path.exists` on each `tests/...py` in `test_path` | 0 missing |
| Source lines | `sed -n '46p;64p' src/systems/social_systems/appraisal.py` | the two reputation reads |
| Diff gate | `git diff --name-only origin/main` | no test file, no `docs/parity_ledger/` file |
