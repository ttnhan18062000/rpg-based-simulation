---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS
artifact_type: test_plan
tags: [simulation-quality, combat, observability]
---

# Test Plan — TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS

No production code changed by this ticket (investigation-only, per `plan.md`'s explicit
reasoning). Verification is the real, controlled A/B testing already documented in
`investigation.md`:
1. Same-run file-vs-memory comparison (`dungeon_crawl` with flag, `urban_political` with flag,
   `dungeon_crawl` with a fixed `run_id`) — all 3 show exact file/memory parity, zero diff.
2. `dungeon_crawl` with vs. without `ENABLE_COMBAT_ENGAGEMENT=ON` — the real, isolated variable
   that explains the original discrepancy.
3. 3 real, direct `tools/calibrate_simq.py` invocations (the actual tool, not a hand probe)
   without the flag, confirming its own real JSONL output includes every push-shaper combat
   event type for both `dungeon_crawl` and `urban_political`.
4. `python3 tools/validate_frontmatter.py` on the ticket and all 3 staging artifacts.

No scoped pytest run required — `git status` confirms zero `src/`/`tests/` changes.
