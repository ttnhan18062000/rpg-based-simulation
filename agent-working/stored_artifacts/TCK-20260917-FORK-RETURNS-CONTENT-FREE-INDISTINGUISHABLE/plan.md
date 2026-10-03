# Plan — TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE

The plan changed mid-ticket once the premise was checked against live evidence. Both stages are
recorded here.

## Original plan (as scoped, before the premise check)

1. Confirm the real shape of `tool_response` for an `Agent` tool call (string, dict, or
   content-block list) — stated as unverified in the ticket's own Assumptions.
2. If confirmed, add a size/emptiness signal to the record `post_tool_hook.py` writes for `Agent`
   rows, using existing data already received at the hook (no new plumbing).
3. Surface the signal in the retro or the advisory sweep.
4. Add tests proving a planted empty return is distinguishable and a planted substantive return is
   not flagged.
5. Restate the ticket's own known limitation (neither non-empty failure shape is covered) in
   code/docs.

## Actual plan (after step 1 falsified the premise)

Step 1 (confirm the real shape) surfaced that the data needed for step 2 never reaches
`post_tool_hook.py` at all for the dispatch shape (forks) this ticket's own incidents involve — see
`investigation.md`. Steps 2-5 as scoped became inapplicable to the actual failure class. Revised
plan:

1. Report the finding to the user before writing any hook code, with the options this changes the
   ticket into: build a narrower, incident-non-covering version anyway (B), pursue a differently
   shaped orchestrator-side mechanism (C), or close with findings recorded (A).
2. User decided A (2026-09-19, direct).
3. Correct the ticket's own Scope premise in place (superseded, not deleted) so the record shows
   both the original claim and what replaced it.
4. Mark every Acceptance Criterion explicitly unmet with a reason, rather than N/A, so the closed
   ticket cannot be misread as delivered.
5. Record the three real findings, the decision and its rejected alternatives, and the three
   mitigations that remain the actual defense, as the ticket's conclusion.
6. Verify `post_tool_hook.py` is byte-identical to `origin/main` before closing, since it runs on
   every tool call in every session and was the file temporarily instrumented for the probes.
7. Close via the standard hand-orchestrated path: `stored_artifacts/`, `record_hand_orchestrated_
   closure.py`, `docs/REGISTRY.yaml` regeneration.
