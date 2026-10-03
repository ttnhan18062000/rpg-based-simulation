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

`tests/tools/test_implement_epic_close_step.py` (10 tests: 7 pin + 3 parametrized fixture) against
`.claude/workflows/implement-epic.js`:

1-7. Raw-source-text pins, following `test_finalize_phase_status_instruction_pin.py`'s established
pattern (no JS test runner exists for `.claude/workflows/*.js`): frontmatter instruction present
(`phase: done` / `status: historical`); body-status instruction says DONE with the EPIC_SCOPED
contrast still present as an explanation; `mv` instruction present, moving into
`tickets/done/${epicId}.md`; guard condition references `epicId`, not `folder`; ordering
(folder-cleanup guard precedes epic-close guard precedes `phase('Report')`); bookkeeping framing
present ("do NOT fail the workflow"); fresh, non-colliding negative sidecar seq (`-5`).

**Honest limitation (post-review, agent-working-design): tests 1-7 pin the agent PROMPT's
wording, not the dispatched agent's runtime behavior** — they pass if the prompt is worded
correctly even if the agent ignores it, and fail on any reword that preserves meaning. This
mirrors the existing folder-cleanup block's own test coverage in the same file.

8-10 (`test_epic_close_step_target_values_satisfy_the_real_location_validator`, parametrized over
`EPIC_SCOPED`/`OPEN`/`DONE` starting values). Applies the prompt's own specified end-state
transformation (frontmatter → historical/done, body `## Status` → DONE unconditionally, file moved
to `tickets/done/`) to a synthetic ticket in `tmp_path`, then asserts the result satisfies the
real `check_ticket_location_consistency()` — the same function TCK-20260907's own corpus test runs
over all of `tickets/done/` at CI. This closes part of the gap above for the frontmatter half —
it still does not prove the dispatched agent performs the transformation correctly at runtime.
Body `## Status` has no automated CI enforcement at all (only this step's own unverified prompt
instruction); the fixture test pins only what the prompt claims to produce, not real agent output.

## Scope of testing

This is a `.js` workflow-instruction-text change with no `src/` behavior touched — Parity is
skip-eligible (no `src/` path changed, `behavior_changed=false`: the new step only affects
epic-ticket bookkeeping, not simulation mechanics).
