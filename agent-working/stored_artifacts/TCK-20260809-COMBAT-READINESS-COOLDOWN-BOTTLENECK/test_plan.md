---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK

No production code changed by this ticket (investigation-only, per `plan.md`'s own explicit
reasoning). No new tests added. Verification consists of:
1. The real, live-instrumented corpus probe already documented in `investigation.md` — a
   2000-tick `dungeon_crawl_seed42`/`urban_political_seed42` `Kernel.tick_once()` loop, real
   `CombatActions.execute_attack` instrumentation, run after
   `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`'s own fix landed, confirming a real,
   zero-variance 11-tick-per-hit rhythm across all 16 sampled real gap measurements.
2. `python3 tools/validate_frontmatter.py` on the ticket and all 3 staging artifacts.
3. No scoped pytest run required — `git status` confirms zero `src/`/`tests/` changes.
