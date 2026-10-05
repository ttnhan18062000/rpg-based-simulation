---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-04
tags: [delivery, planning]
---

# Python Code Craft: M5 structure soak review (DRAFT, finalize after 2026-10-18)

Covers `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING` and `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING`.
Window for both: 2026-10-04T06:26:43Z (PR #315 merged) to 2026-10-18 (start + 14 days). **Drafted on 2026-10-04, a few
hours into the window.** Every count is re-measured on the final day. Method as in
`python_code_craft_gates_soak_review.md`: run logs are not readable from this environment, so a run's outcome comes
from check-run annotations and the PR it ran on, not from the job summary.

## Precondition record (main must be clean at the flip commit)

| When | Commit | `codebase.health check` (includes `ast_grep`) | `codebase.structure.packages validate` | `mypy_gate` |
|---|---|---|---|---|
| 2026-10-04 (draft) | `origin/main` 053f459e4 | exit 0, 0 new, 0 worse (ast_grep: 0 new or worse of 111 rows) | exit 0, 0 problems over 36 rows | exit 0 |
| Before merge (on or after 2026-10-18 05:00Z) | to fill | to fill | to fill | to fill |

`ast_grep` was report-only until now, so a non-zero count would not have failed a run before; the explicit check
above is why its zero is worth recording.

## Package registry (ticket 2)

| Measure | Draft | Final |
|---|---|---|
| Runs of the `Package registry` step since #315 | not separately counted yet (it ran in the `Code health (advisory)` job) | |
| Completeness or schema problems reported | none seen; no new top-level `src/` package was added since #315 | |
| False positives | none | |
| Rows reviewed (`reviewed` field) | the 36 rows came from the audit table of 2026-10-04 and were reviewed by the planner when seeded | |

Behaviour at the flip: a tracked top-level `src/` package with no row, a row for a package that is gone, or a schema
problem fails `Code health` (exit 1); a failure to run fails it too (exit 2). The live-repo test in
`tests/codebase/test_package_registry.py` is a second enforcement point.

## ast-grep rules N3, N4, E3 (ticket 3)

Seeded by #315: 111 rows, 150 findings by value.

| Rule | Rows | Findings | Spot-check of the rule's matches (draft) | Final |
|---|---|---|---|---|
| `n3-private-name-import` | 13 | 23 | `adventure_scorer.py:109 _GOAL_UTILITY_SCORE_MAX`: a real cross-module private import | |
| `e3-silent-except` | 91 | 120 | `search.py:212`, `scorers.py:26/225/234`, `server.py:81`: each an `except` whose body is only `pass` | |
| `n4-version-marker-name` | 7 | 7 | `create_v2_app`, `V2EngineManager`, `V2EntityBuilder`, `V2Recipe`: existing `V2` names, grandfathered | |

Per-rule disposition counts (real / false positive) over the window's runs: **none seen as new findings so far**
(the only ratchet-failing runs of the first hours, PR #291 and PR #319, were ruff and complexipy findings; the SARIF
`ast-grep` check run on PR #291 reported "No new alerts"). The final review lists every new `ast_grep` finding in the
window with its disposition. N4 leaves a trailing digit (`2`) to the reviewer and E3 counts only an `except` whose body
is only `pass`; both are documented limits, not false positives. A false-positive class found before the flip is fixed
or the flip stops and the planner is told.

Rows deleted as debt was paid: none yet. Rows reseeded or added since #315: none.

## Live demos

Steps 3 to 5 of the demo PR #331 (details and the other links in the gates soak review): step 3 (no row) failed only at `Package registry` and in the one completeness test of `Tools · a–e`; step 4 (row added) passed both; step 5 (E3) failed `Code health` on one `ast_grep e3-silent-except` finding. The E3 demo uses a typed silent `except OSError: pass` rather than a bare `except: pass`: a bare `except:` would also trip ruff `E722`, and the proof would not isolate ast-grep.

## Verdict (draft)

No false-positive class and no problem seen in the first hours. The flips are on track, subject to the final-day
re-measurement and the pre-merge precondition run above.
