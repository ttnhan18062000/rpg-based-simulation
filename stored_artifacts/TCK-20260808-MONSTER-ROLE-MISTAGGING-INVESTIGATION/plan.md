---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION
artifact_type: plan
tags: [content, world]
---

# Plan: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION

## Approach
1. Trace the real, complete root cause before proposing any fix — the ticket's own filing
   already flagged one real lead (ambiguous role_ids) but explicitly left it unconfirmed.
2. Once confirmed, fix at the real source (the loading layer that fails to surface an
   already-correct, already-computed artifact) rather than patching each individual symptom
   (e.g., renaming ambiguous role_ids in content, which wouldn't have fixed anything — the
   catalog lookup was never being reached at all).
3. Centralize the fix into one shared method rather than duplicating the correct logic a third
   time, given 2 real call sites already had independently-correct implementations.
4. Update every real, confirmed-buggy call site — not just the one used by SimQ tooling — since
   the bug was traced to affect the general "run a simulation" CLI entrypoint too.
5. Measure and honestly disclose the real downstream impact rather than assuming it's small.

## Rejected Alternatives
- **Fix the ambiguous shared role_ids in `roles.yaml`** (e.g. give monster-specific archetypes
  their own unambiguous role_ids) — rejected as the primary fix: this would only address
  Hypothesis 1, a real but secondary contributing factor, and would NOT fix the primary cause
  (unambiguous role_ids like "predator_hunter" were equally affected). Worth revisiting as a
  separate, smaller content-quality improvement if desired, but not a substitute for the real fix.
- **Give `WorldCompiler.compile()` its own `catalog_repo` parameter** and call
  `RoleSemanticsService`/`FactionSemanticsService` directly, bypassing the need for a
  pre-computed `CompileContext` — a real, valid alternative architecture, but a much larger
  change (touches every real call site's own signature, and `WorldCompiler.compile()`'s own
  design intentionally keeps it catalog-agnostic per its own docstring, relying entirely on a
  pre-resolved `context`). The chosen fix (surface the already-computed, already-correct
  `compile_context.json`) is smaller, safer, and matches the pattern 2 real call sites already
  used correctly.

## Verification Plan
- 4 new direct tests for `WorldRepository.load_world_with_context()`.
- Full regression sweep across worldbuilding/simulation_quality/content_semantics/core/
  entities/world/tactical/combat/engine/kernel/worldassembly test suites.
- Real corpus re-verification via direct compiled-state inspection (role/faction distributions)
  on both `dungeon_crawl` and `urban_political`, before and after.
- Real SimQ calibration re-run on both worlds to measure and honestly disclose the material
  downstream scoring impact.
