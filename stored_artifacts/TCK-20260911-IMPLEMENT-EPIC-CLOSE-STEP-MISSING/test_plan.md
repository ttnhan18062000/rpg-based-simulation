---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING
artifact_type: test_plan
tags: [workflows, process-improvement]
---

# Test Plan — TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING

## Automated

`tests/tools/test_implement_epic_close_step.py` (new, 7 tests) — raw-source-text pin against
`.claude/workflows/implement-epic.js`, following `test_finalize_phase_status_instruction_pin.py`'s
established pattern (no JS test runner exists for `.claude/workflows/*.js`):

1. Frontmatter instruction present (`phase: done` / `status: historical`).
2. Body-status instruction says DONE, with the EPIC_SCOPED contrast still present as an
   explanation (not silently reverted to the wrong value).
3. `mv` instruction present, moving into `tickets/done/${epicId}.md`.
4. Guard condition references `epicId`, not `folder`.
5. Ordering: folder-cleanup guard precedes epic-close guard precedes `phase('Report')`.
6. Bookkeeping framing present ("do NOT fail the workflow").
7. Fresh, non-colliding negative sidecar seq (`-5`), confirmed against every existing
   `writeSidecar(-N, ...)` call site in the file.

## Manual verification (no JS test runner exists to execute the agent-prompt path directly)

- Hand-run `check_ticket_location_consistency()` against a synthetic ticket dict with
  `status: historical`, `phase: done` at a `tickets/done/` path — confirms it returns `[]` (passes),
  proving the exact frontmatter values this step's instruction specifies satisfy the existing
  validator rule (AC4), without needing a real `implement-epic` run (which would cost real tokens
  and isn't warranted for a workflow-instruction-text change).
- Confirm no other test in `tests/tools/test_implement_epic.py` (if any exists) or elsewhere
  references the exact line ranges this edit shifted, so nothing else silently breaks.

## Scope of testing

This is a `.js` workflow-instruction-text change with no `src/` behavior touched — Parity is
skip-eligible (no `src/` path changed, `behavior_changed=false`: the new step only affects
epic-ticket bookkeeping, not simulation mechanics).
