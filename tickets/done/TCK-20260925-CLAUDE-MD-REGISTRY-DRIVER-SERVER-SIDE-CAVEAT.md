---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260925-CLAUDE-MD-REGISTRY-DRIVER-SERVER-SIDE-CAVEAT
phase: done
date: 2026-09-25
tags: [testing]
---

# TCK-20260925-CLAUDE-MD-REGISTRY-DRIVER-SERVER-SIDE-CAVEAT

## Title

Clarify in CLAUDE.md that the `docs/REGISTRY.yaml` merge driver only applies to local git operations, never GitHub's own PR merge-ref computation

## Status

DONE

## Tier

hotfix

## Type

chore

## Priority

P2

## Request Summary

While investigating PR #246's CI failure, agent-working-design flagged that CLAUDE.md's "After
Work" bullet about `make setup-merge-drivers` reads as if it fully solves `docs/REGISTRY.yaml`
merge conflicts, without saying that it only ever applies to a *local* `git merge`/rebase/
cherry-pick run through an agent's own worktree — GitHub's own server-side PR merge-ref
computation (`refs/pull/N/merge`) never sees a local `.git/config` driver registration, since
`make setup-merge-drivers` writes to `.git/config` (never committed/pushed).

Checked the source ticket (`TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX`) first: its own
`investigation.md` "Assumptions / Open Questions" section already states this plainly ("GitHub's
own server-side merge does not run local drivers... this was never in question") — so the fact was
known and recorded on 2026-09-12. The actual defect is narrower than "nobody named this": CLAUDE.md's
terse summary of that ticket dropped the caveat the source ticket already carried. A
summarization-loss defect, not a missing investigation.

## Scope

- Append one clarifying sentence to CLAUDE.md's `docs/REGISTRY.yaml` merge-driver bullet (After
  Work section), stating plainly that the driver only helps local git operations and that a
  `docs/REGISTRY.yaml`-only PR going `CONFLICTING` is expected in that case, not a driver failure.
- User's own direct confirmation of the literal diff obtained via `AskUserQuestion` before editing
  (standing rule for any CLAUDE.md/settings.json change, unrelated to how obviously correct the
  edit looks) — approved as shown.

## Out of Scope

- Re-litigating or re-implementing `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX`'s own mechanism
  — that ticket's design and disclosed residual risks stand; this is a documentation-wording fix
  only.
- Auditing every other CLAUDE.md summary against its source ticket for the same class of
  summarization loss — a reasonable idea raised in discussion, not scoped here.

## Acceptance Criteria

1. CLAUDE.md's `docs/REGISTRY.yaml` merge-driver bullet states explicitly that the driver has no
   effect on GitHub's server-side PR merge-ref computation.
2. No other CLAUDE.md content changed.
3. Tests referencing CLAUDE.md content/shape still pass.

## Related Tickets

- `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX` — the source ticket whose own investigation.md
  already recorded the caveat CLAUDE.md's summary dropped.

## Related Docs

- `CLAUDE.md` (the edited bullet itself).

## Related Stored Artifacts

None (hotfix tier, no staging artifacts required).

## Related Code Areas

None — documentation-only change.

## Assumptions / Open Questions

None.

## Implementation Notes

Read `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX`'s own `tickets/done/` file and its
`investigation.md` before drafting the fix, rather than assuming the gap from agent-working-design's
framing alone — confirmed the underlying fact was already correctly recorded there, narrowing the
actual defect to a summarization-loss in CLAUDE.md's own terse pointer text, not a missing
investigation. Obtained the user's own direct `AskUserQuestion` confirmation of the exact literal
sentence before editing CLAUDE.md, per the standing rule for governing-file edits — approved as
shown, no wording changes requested.

Ran the existing tests that reference CLAUDE.md content/shape
(`test_current_run_sidecar_orchestrator.py`, `test_monitoring_bypass_fix.py`,
`test_delivery_pr_render.py`, `test_generate_registry.py`,
`test_record_hand_orchestrated_closure.py`, `test_done_checker_static.py`,
`test_finalize_knowledge_index_refresh.py`, `test_bash_secret_scan_hook.py`,
`test_kernel_phase_names_consistent.py`, `test_ci_per_directory_steps_documented.py`,
`test_prescan_mandate_instruction_draft.py`, `test_ci_triage_absent_run_branch.py`) before
finalizing, since the edit is purely additive text appended to an existing line rather than
assuming no test could possibly be sensitive to CLAUDE.md's exact content/line count.

## Test Summary

`python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py
tests/tools/test_monitoring_bypass_fix.py tests/tools/test_delivery_pr_render.py
tests/tools/test_generate_registry.py tests/tools/test_record_hand_orchestrated_closure.py
tests/tools/test_done_checker_static.py tests/tools/test_finalize_knowledge_index_refresh.py
tests/tools/test_bash_secret_scan_hook.py tests/docs/test_kernel_phase_names_consistent.py
tests/docs/test_ci_per_directory_steps_documented.py
tests/docs/test_prescan_mandate_instruction_draft.py
tests/docs/test_ci_triage_absent_run_branch.py -q` — **320 passed**, 0 failed, run before closing.

## Files Changed

- `CLAUDE.md` — one clarifying sentence appended to the `docs/REGISTRY.yaml` merge-driver bullet.
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule), picking up this ticket's own `tickets/done/` entry.

## Completion Summary

Appended one sentence to CLAUDE.md's `docs/REGISTRY.yaml` merge-driver bullet, stating explicitly
that `make setup-merge-drivers`'s driver only applies to local `git merge`/rebase/cherry-pick
operations, never GitHub's own server-side PR merge-ref computation, and that a
`docs/REGISTRY.yaml`-only PR going `CONFLICTING` is expected there, not a sign of driver failure.
Checked the source ticket first rather than trusting the framing that surfaced the gap: the fact
itself was already correctly recorded in `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX`'s own
investigation.md, so the actual defect is CLAUDE.md's summary dropping a caveat its own source
ticket already carried, not a missing investigation. Obtained the user's own direct confirmation of
the literal sentence before editing, per the standing rule. Ran all tests referencing CLAUDE.md
content before closing (320 passed) — the edit is purely additive and did not affect any of them.

No known material gap. Documentation-only change; no code or tests touched.
