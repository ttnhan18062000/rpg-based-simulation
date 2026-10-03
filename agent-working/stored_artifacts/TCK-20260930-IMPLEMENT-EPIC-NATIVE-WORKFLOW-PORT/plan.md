---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT
artifact_type: plan
tags: [ai]
---

# Plan

1. Add `args.start_ts` (required; structured INVALID_ARGS, no record) and a `runCommand()`/`runMonitoringCommand()` helper copied from create-tickets.js; replace all 11 `bash()` sites; keep every fail-open WARNING.
2. Classify the 11 sites first (all bookkeeping, none a gate), so the plain runCommand route is safe.
3. Escape the raw backticks at line 247 (parse blocker added after the pilot).
4. `execution_mode:"workflow"` in every run record; a `WORKFLOW_ERROR` hint explaining that implement-ticket cannot run natively yet.
5. Update SKILL.md and docs/ai/skills.md; update the pinned tests, add `test_implement_epic_native_port.py`.
6. Measure: zero-agent probe for nested `workflow()`, then one real native run on the NOTHING_TO_DO path.
