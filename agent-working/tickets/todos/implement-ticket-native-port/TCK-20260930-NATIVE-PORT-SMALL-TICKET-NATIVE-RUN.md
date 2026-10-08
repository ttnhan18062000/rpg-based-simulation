---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN
phase: open
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN

## Title
Run one small ticket through the native implement-ticket and verify gate outcomes

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES.

## Scope
Epic AC1 and AC3: no `bash(` in implement-ticket.js and one native run of a small ticket with correct gate outcomes (including a deliberately failing gate). Requires the user's own Workflow opt-in at dispatch time.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. `tools/workflow_bash_sites.py` reports 0 real sites.
2. One native run completes with correct pass and fail outcomes, recorded as evidence in `.jsonl`/`.md`.
3. The orchestrator backstop agrees with the run's gate verdicts.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (parent epic)
- TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN (outcome: adopt for gates only, plus backstop)

## Related Docs
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.md`
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/`
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- None beyond the parent epic's.
- **2026-10-06, blocked by the environment, not run.** The owner approved this run on 2026-10-06 (answering "Run it"). Two attempts never reached Scope: the named workflow resolved the main checkout's `implement-ticket.js` (no attested sites) and returned the old `NATIVE_GATE_SITES_UNPORTED` refusal; a `scriptPath` run of the worktree file died with `agent type 'ticket-scoper' not found`, because the session was launched from `/mnt/data/Working` and the repo's `.claude/agents` were not registered. About 240k tokens were spent; no gate was reached and no repo state changed. A rerun needs a session started in a repo worktree, after the PR that lands `TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES` merges, with `scriptPath` pointing at that tree's `implement-ticket.js`. The refusal run rows stay in the monitoring shard as a true record.

## Implementation Notes
**Run plan (planner, 2026-10-09; owner opt-in for this run given in the planner session 2026-10-09, "go with your recommendations").**
- Precondition (checked 2026-10-09): `tools/workflow_bash_sites.py .claude/workflows/implement-ticket.js` reports 0 sites at main 42ce987b6. Re-check it at the run's base.
- Environment, from the 2026-10-06 failure: the run must start from the `agent-working-implementer` session, which was launched in a repo worktree so `.claude/agents` resolve. Pass `scriptPath` = that worktree's `.claude/workflows/implement-ticket.js`, synced to origin/main. Do not run the named workflow, which resolves the main checkout.
- Vehicle: `TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES`, a real small fix at standard tier so that every gate site is reached.
- Deliberate failing gate (AC2), done in two runs, because a gate that fails also stops the run:
  1. **Fail run.** Add one unregistered tag to the vehicle (e.g. `native-run-probe`; do NOT register it). Run with `ticket_id` = the vehicle. Expected: `Scope:tag_registry.check_tags_registered` FAIL through `shAttested('tag_check')`, return `TAGS_NOT_REGISTERED`, and a monitoring run row; Scope only, so it's cheap. If the scoper drops or rewrites the tag instead of reporting it, stop and report: that is a finding, not something to route around.
  2. **Pass run.** Remove the probe tag and rerun the same `ticket_id`. Expected: every reached gate is PASS, or a real failure handled by the pipeline's own loop, and the run ends DONE.
  Both runs together are the evidence for AC2. The "one native run" wording means one real ticket through the native path, with the failing probe as its first attempt.
- AC3: for each run, compare the orchestrator backstop's re-run verdicts with the run's attested gate verdicts in `gate_verdicts.jsonl`, and record any disagreement.
- Evidence goes into this ticket's Test Summary: run ids, each gate site's outcome, the backstop comparison, and the measured tokens and wall-clock per run.
- Landing: both tickets land on the local batch branch `agent-working-small-fixes-batch`, with no push and no PR (owner, 2026-10-08). Closing this ticket also closes the last child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`; close the epic and move the folder to `done/` per CLAUDE.md.

## Test Summary

## Files Changed

## Completion Summary
