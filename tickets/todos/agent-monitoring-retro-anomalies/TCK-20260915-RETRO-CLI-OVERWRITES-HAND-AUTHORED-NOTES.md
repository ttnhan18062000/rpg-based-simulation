---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES
phase: open
date: 2026-09-15
tags: [agent-monitoring, reporting, process-improvement]
---

# TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES

## Title
`generate_retro.py` unconditionally overwrites its own report, destroying the hand-written `## Notes` the project's own retro skill instructs a session to add

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found the hard way on 2026-09-15 by `agent-working-implementer` while verifying the
`DUPLICATE-RUN-RECORDS` fix: re-running `python3 tools/agent-monitoring/generate_retro.py --days 14`
to check a corrected figure **rewrote `agent-monitoring/retro/RETRO-LAST14D.md` from scratch**,
deleting every hand-authored section in it. Confirmed with a real `git diff` showing **177 deleted
lines** before it was reverted. The verification had to be completed instead by importing
`_load_runs_and_events()` / `compute_retro_metrics()` / `generate()` directly and calling them
without touching `RETRO_DIR`.

**This is an instruction-level trap, not just an ergonomic wart.** The project's own skill,
`.claude/skills/agent-monitoring-retro/SKILL.md`, explicitly tells a session to:

> Fills in the `## Notes` section of the report with concrete findings and one proposed action per
> issue found, then leaves the report ready to commit.

and

> Commit the filled-in report. Do not discard the notes — they are the institutional memory of
> agent behavior over time.

So the documented workflow is: generate, hand-write analysis into the report, commit it. And the
same tool's next invocation destroys exactly that. A session following both instructions in order
loses its own work — structurally identical to the `append_working_log_row()` +
`record_hand_orchestrated_closure.py` double-write that
`TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` fixed: two correct
instructions that combine into a defect.

The risk is not hypothetical or one-off. `RETRO-LAST14D.md` currently carries a ~200-line deep
review plus an index-defect addendum; the weekly `RETRO-<week>.md` files are the skill's normal
output and are meant to accumulate notes over time. Any regeneration silently discards them, and
because the file is rewritten rather than appended to, nothing warns and nothing fails.

## Scope
- Make regeneration non-destructive with respect to hand-authored content. The mechanism is the
  implementer's choice; the constraint is that content a human or agent wrote must not be silently
  discarded. Reasonable shapes:
  - **Refuse** to overwrite a report that contains content outside the generated sections, unless
    an explicit `--force` is passed.
  - **Preserve** a delimited region (e.g. everything from `## Notes` onward) across regeneration.
  - **Write elsewhere** by default, leaving the existing file untouched.
- Whichever is chosen, a regeneration that *would* discard content must say so rather than doing it
  quietly.
- If the chosen shape changes the documented workflow, update
  `.claude/skills/agent-monitoring-retro/SKILL.md` in the same change so the skill and the tool stop
  disagreeing.

## Out of Scope
- `_update_index`'s zero-reporting defect — that is `TCK-20260915-RETRO-INDEX-REPORTS-ZERO`, a
  separate bug in the same file.
- Restoring any previously-lost notes. The 177-line loss was caught and reverted; whether earlier
  regenerations destroyed notes nobody noticed is unknown and not investigated here.
- Changing the report's generated sections or format.

## Acceptance Criteria
- [ ] Running the generator against an existing report containing hand-authored content either
      preserves that content or refuses with a clear message naming what it would have destroyed.
      Silent overwrite is not an acceptable end state.
- [ ] A test plants hand-authored content in a report, regenerates, and asserts the content
      survives (or that the command failed loudly). The test must assert on **observable output or
      file content**, not merely a return code — the failure mode here is silence.
- [ ] `--force` (or equivalent) still allows a deliberate full rewrite, so the tool stays usable.
- [ ] `.claude/skills/agent-monitoring-retro/SKILL.md` and the tool agree about what regeneration
      does to notes.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-RETRO-INDEX-REPORTS-ZERO` — sibling defect in the same module
- `TCK-20260915-DUPLICATE-RUN-RECORDS` (done) — the ticket whose verification hit this hazard
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` (done) — the same
  "two correct instructions combine into a defect" shape

## Related Docs
- `.claude/skills/agent-monitoring-retro/SKILL.md` — the instruction half of the trap
- `agent-monitoring/retro/RETRO-LAST14D.md` — records the hazard in its own correction note
- `docs/guides/agent_monitoring.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-DUPLICATE-RUN-RECORDS/` — where the hazard was hit

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` — `main()`, `generate()`, and the `RETRO_DIR` write path
- `.claude/skills/agent-monitoring-retro/SKILL.md`
- `Makefile` (`agent-monitoring-retro` target)

## Assumptions / Open Questions
- Whether any past regeneration already destroyed notes is **unknown**. Git history would show it,
  but that search is deliberately out of scope here — flagged in case it is worth its own look.
- The weekly reports may be more exposed than the period reports, since the skill's documented
  cadence regenerates them routinely.

## Implementation Notes
Reproduce safely: copy a report with hand-authored content to a scratch path, point the generator
at it, and diff. Do **not** reproduce against `RETRO-LAST14D.md` in place — it currently holds the
deep review and the index addendum, and that is precisely the content at risk.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
