---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT

Source of truth: `docs/plans/codebase_health/import_linter_flip_batch_brief.md` (steps 1a-1f). Order, as done: finish the soak review; name the broken pairs in the step summary and annotations (`ci` mode); retire the seven class E tests with their replacement contracts, valid only together with the blocking commit; give the four phase19 `ignore_imports` rpg's per-edge reasons and state the OFF-mode condition as UNENFORCED (follow-up `TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK`); make the `Import contracts` step blocking in the already-required `Code health` job (no ruleset change); handoffs (decision 8.11 notice to testing, left unsent; one line to rpg). Day-of: merge main, clear one stale ignore as a ratchet-down. Nothing under `src/`.
