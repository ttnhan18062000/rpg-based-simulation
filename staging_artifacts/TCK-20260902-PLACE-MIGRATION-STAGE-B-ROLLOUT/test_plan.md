---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

**Normal flow:** `hero_guild_routing` compiles with 4 correctly-kinded Places/regions, verified by direct
inspection (not just an automated hash check — Stage B's whole point is a human-verifiable structural
check on non-uniform content).

**Edge cases:** `mountain_pass`-style content that may have no City-kind Place at all (pure wilderness
Region with zero Places, per the plan doc).

**Failure modes:** a region silently dropping content during migration (Place count mismatch vs. source
world-module tag count).

**Regression-prone paths:** each of the remaining 19 worlds compiling successfully post-migration — no
world should fail to compile.

**Scope command:** compile each target world via the standard entry point; inspect
`world_compile_report.json` directly for Stage B, hand off to the recalibration ticket for the remaining
19.
