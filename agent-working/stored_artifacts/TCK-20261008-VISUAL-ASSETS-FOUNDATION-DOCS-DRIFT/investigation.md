---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT
artifact_type: investigation
date: 2026-10-09
tags: [architecture, documentation]
---

# Investigation

- Drift sites: `docs/assets/drawing_tools.md:18`; `docs/plans/visual-asset-foundation/README.md` (`handoff.py` "later ticket", CLI "build|release|verify|gc later", `test_catalog_integrity` "later ticket"); `visual_assets/README.md` (store "skeleton only", catalog "empty skeleton"); the summary table of `docs/assets/m1_contract_register.md` still said "Yes" for W02.7, W03.1 and W06.3 after they became `MET`.
- Evidence gap: `.gitignore:241` (`agent-working/stored_artifacts/**/*.json`) kept 47 evidence files (223,833 bytes) of the visual-asset tickets out of git: the M5 browser captures and the W05 result (DETAIL-M5-RERUN, M5-GAP-CLOSURE), and the blind-check answers and evaluations, look-alike reports, rule results and intakes of RECOGNISABILITY-CHECKS, V2-RECOGNISABILITY-REDRAW, OWNER-FIXES and THEME-FIT. PR #418 and the earlier M5 work pointed at files that existed on one disk only. The key-usage report's first run was caught the same way in child 6 and stored as `.json.txt` from the start.
- The planner's own handover (`asset-planner.md`) says "paused after child 4"; the snapshot keeps it as is and says it is stale (the planner refreshes it).
