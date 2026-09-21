---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP
phase: open
date: 2026-09-21
tags: [ai, registry, process-improvement, workflows]
---

# TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP

## Title
An epic ticket closed via the CLAUDE.md folder-move rule (`tickets/done/{folder}/`) disappears
from `docs/REGISTRY.yaml`, and its `done_checker_static.py` finalize checks fail — a pre-existing
gap, deferred, not this batch's problem to fix

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found while closing `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (2026-09-21) via CLAUDE.md's
own written rule: "When all tickets in the folder are done, move the entire folder to
`tickets/done/{folder}/`." `tools/generate_registry.py` (its own docstring, lines 355-365) walks
`tickets/done/*.md` **flat only** — it never recurses into `tickets/done/{folder}/`, so an epic
ticket closed this way is invisible to the registry, even though it is genuinely closed and its own
file genuinely exists under `tickets/done/`. `tools/gate_checks/done_checker_static.py`'s finalize
conditions (`migration_complete`, `ticket_finalized`, `registry_entry_regenerated`) have the same
flat-path assumption and FAIL for the same reason — not because anything is actually wrong with the
closure, but because the checker looks for the ticket file at a flat `tickets/done/{id}.md` path
that a folder-closed epic never uses.

**Confirmed on two independent real closures, not a one-off:**
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (closed 2026-09-15, already accepted, living at
  `tickets/done/agent-monitoring-retro-anomalies/`) — 0 entries in `docs/REGISTRY.yaml`, same 3
  `done_checker_static.py --tier epic --part finalize` conditions FAIL when re-run against it today.
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (closed 2026-09-21, living at
  `tickets/done/headroom-context-compression-trial/`) — `grep -c` confirms 1 entry on `origin/main`
  (indexed while the ticket lived in `tickets/todos/`) dropping to 0 once moved into the folder on
  `tickets/done/`; same 3 finalize conditions FAIL identically.

Child tickets closed at the flat `tickets/done/` root (matching CLAUDE.md's own note that individual
children move out of the folder as they close, leaving only the epic + `SEQUENCE.md` behind) remain
correctly indexed — only the folder-nested epic ticket itself is affected.

## Scope
When picked up:
- Either make `generate_registry.py` recurse into one level of `tickets/done/{folder}/` (matching
  how it already must handle `tickets/todos/{folder}/` for open epics, if it does — verify first
  rather than assume), or give folder-closed epics a documented, deliberate registry-visibility
  workaround.
- Make `done_checker_static.py`'s finalize path lookups folder-aware for epic-tier tickets closed
  via the CLAUDE.md folder-move rule, so a legitimate folder closure doesn't read as 3 failed
  conditions.
- Decide whether the fix should be scoped to epic-tier tickets specifically, or any ticket that
  ends up in a `tickets/done/{folder}/` path for any reason.

## Out of Scope
- **Not implemented in this ticket.** Filed to record the gap with real evidence, not to fix it —
  per the user's own defer-minor-effect rule: this rides along unbuilt until someone picks it up
  deliberately, since it affects registry completeness/search convenience and a manual
  `done_checker_static.py` re-run's readability, not correctness of the actual closure or any
  blocking gate.
- Changing the CLAUDE.md folder-move rule itself, or how epics are closed. The rule is correct;
  the tooling around it hasn't caught up.
- Any change to `docs/REGISTRY.yaml`'s schema or `done_checker_static.py`'s non-finalize conditions.

## Acceptance Criteria
- [ ] `generate_registry.py` includes an entry for a folder-closed epic ticket (or an equivalent,
      deliberately-chosen visibility mechanism is in place and documented).
- [ ] `done_checker_static.py --tier epic --part finalize`, run against a real folder-closed epic,
      reports PASS for `migration_complete`/`ticket_finalized`/`registry_entry_regenerated`
      (adjusted to whatever the real evidence requirements become once folder-awareness is added).
- [ ] Re-run against both real precedents named above (`TCK-20260915-MONITORING-ANOMALY-DETECTION-
      EPIC`, `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`) to confirm the fix generalizes, not
      just fixes whichever epic prompted the ticket.
- [ ] No blocking gate is introduced — this stays report/index tooling, matching the existing
      report-only convention for `docs/REGISTRY.yaml` regeneration and `done_checker_static.py`'s
      own advisory-when-hand-orchestrated shape.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (done) — where this was found.
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (done) — the independent precedent confirming
  this isn't a one-off.
- `TCK-20260709-REGISTRY-REGEN-ON-CLOSE` (done) — established the "regenerate unconditionally at
  close" convention this gap quietly undermines for folder-closed epics specifically.

## Related Docs
- `CLAUDE.md`'s "After Work" section — the folder-move rule this gap interacts with.

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/generate_registry.py` (docstring lines 355-365 describe the flat-only `tickets/done/*.md`
  walk)
- `tools/gate_checks/done_checker_static.py` (`migration_complete`, `ticket_finalized`,
  `registry_entry_regenerated` finalize conditions)

## Assumptions / Open Questions
- Whether `generate_registry.py` already has special handling for `tickets/todos/{folder}/` (open
  epics) that could be mirrored for `tickets/done/{folder}/` (closed epics), or whether open-epic
  folders have the identical gap on the todos side too. Not checked as part of filing this ticket —
  first thing to verify when picked up.
- Whether the fix belongs in `generate_registry.py`'s walk logic, a small folder-aware helper both
  tools share, or something else entirely. Genuinely open.

## Implementation Notes
Not implemented. Verify both real precedents still reproduce the gap before starting (repo state
may have moved on), and check whether an unrelated, already-in-flight ticket has touched either
tool in the meantime.

## Test Summary
_Not yet — deferred._

## Files Changed
_None — filed, not implemented._

## Completion Summary
_Open. Filed 2026-09-21 with two independent real-closure confirmations rather than a single
anecdote, per the user's defer-minor-effect rule: record now with evidence, fix later when someone
has a reason to prioritize it._
