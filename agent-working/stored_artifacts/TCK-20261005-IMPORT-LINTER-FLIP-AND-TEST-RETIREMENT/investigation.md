---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT
artifact_type: investigation
tags: [architecture, planning]
---

# Investigation — TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT

Findings. (1) The soak window (2026-10-05 to 2026-10-19) shows 182 counted runs on `main`: 11 broken in the first 3.9 days (five real layer breaks, fixed in #420), none after; no false-positive class (`import_linter_soak_review.md`). (2) The count line counts contracts, not ignores, so a stale ignored import is invisible to the soak; the blocking step's stale check found one on the flip day (`src.engine.world_dynamics -> src.world.spawn`, left by main #645). (3) Seven tests are strictly weaker than their contracts: 37 injections, the contracts caught all 37, the tests missed 9. (4) phase19: the static scan never matches `src.observability...` and has no notion of OFF mode, so the condition behind the four ignores is unenforced until a runtime test lands (owner decision 2026-10-18, #547). (5) `Code health` has been a required check since 2026-10-06, so no ruleset change is needed.
