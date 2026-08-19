---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC
phase: done
date: 2026-08-17
tags: [ai, process-improvement]
---

# TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC

## Title
Teach the epic-staleness hook to check ticket ## Status before flagging BLOCKED epics as stale

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`make agent-monitoring-epic-staleness` measures file-mtime idleness only. It has flagged
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` as idle throughout this entire session, despite that
ticket's frontmatter literally stating `phase: blocked` and its body carrying a dated, explicit
deferral rationale. This is a deliberately governed pause, fully documented — not ambiguous
ownership or silent neglect — and it has fired repeatedly in this session's own tool output while
this exact ticket was being written. Small, precisely scoped, high-value fix: teach the hook to
read ticket status before flagging.

## Scope
Full findings are in `docs/plans/epic_staleness_status_aware_epic.md`. Concrete scope:
- Teach the staleness-check script (`tools/agent-monitoring/`) to read the target ticket's
  `## Status` body field before flagging, and skip (or flag with a different, non-actionable
  label) any ticket whose status is `BLOCKED` with a stated rationale.
- Decide whether `BLOCKED` tickets should still surface in the report as an informational
  "parked" list, rather than disappear entirely.

## Out of Scope
- Any change to the 5-day staleness threshold itself.
- Broader agent-monitoring tooling changes beyond this one hook's status-awareness.

## Acceptance Criteria
- [x] Running the staleness check against `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` in its
      current `BLOCKED` state no longer produces the same undifferentiated "stale" flag it does today.
      Evidence: live run of `python3 tools/agent-monitoring/epic_staleness_check.py` now lists it
      under "Informational: BLOCKED epics (not stale — deliberately parked):", not under
      "Stale epics:"; `test_real_codex_runtime_activation_epic_is_status_aware` asserts the same
      against a copy of the real ticket file, read-only.
- [x] A genuinely stale, non-`BLOCKED` epic still gets flagged correctly (the fix must not weaken
      the hook's real usefulness).
      Evidence: `test_epic_with_all_children_stale` (pre-existing) and the new
      `test_genuinely_stale_non_blocked_epic_still_flagged_regression_guard` both pass; the live
      run above still flags `FOLDER-tickets-todos-codex-runtime-activation` as stale.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (the concrete false-positive case study)

## Related Docs
- docs/plans/epic_staleness_status_aware_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/ (the epic-staleness check script)

## Assumptions / Open Questions
- Whether BLOCKED epics should still appear in the report as an informational "parked" list, or
  disappear entirely, is an open decision to resolve during implementation.
- **Downgraded from epic to hotfix tier (2026-08-18):** the most clear-cut miscall of the 10
  sub-epics created under `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC` — this ticket's own
  Request Summary already described the fix as "small, precisely scoped," which was never
  epic-shaped to begin with. Hotfix tier needs no staging artifacts, per Tier Routing.

## Implementation Notes
Made `tools/agent-monitoring/epic_staleness_check.py` read each candidate epic ticket's body
`## Status` field, mirroring the existing `_section_body(text, "Tier")` pattern already used for
`EpicCandidate.mode` detection:

1. Added `status: Optional[str] = None` to `EpicCandidate`, populated at discovery time in
   `discover_candidate_epics` — both the `inprogress_dir` (`epic_id` mode) branch and the
   `todos_dir` (`folder` mode) branch, upper-cased for case-insensitive comparison. In the
   folder-mode "no epic_ticket_file found" case (`epic_id = FOLDER-tickets-todos-{subdir.name}`,
   synthesized with no backing ticket file to read), `status` is left `None` rather than raising —
   there is genuinely no body to read `## Status` from.
2. Added `is_epic_blocked(candidate)` — `True` iff `candidate.status` upper-cases to `"BLOCKED"`.
3. `is_epic_stale` now returns `False` immediately for a blocked candidate, ahead of its existing
   child-idle checks — belt-and-suspenders alongside the classification routing below, so any
   direct caller of `is_epic_stale` (not just `_classify_candidates`) gets the same guard.
4. `_classify_candidates` now returns a third bucket, `blocked` (list of `(candidate,
   most_recent_activity)` tuples), and routes a candidate into it *before* the stale/never-started
   checks — a BLOCKED candidate is classified only as blocked, never double-counted into either
   other bucket regardless of how idle or fresh its children's activity is.
5. `find_stale_epics` (the hook's actual fire-trigger) unpacks the new 3-tuple but is otherwise
   unchanged — it still returns only the `stale` list, which by construction (step 4) can never
   contain a BLOCKED candidate.
6. `compute_stale_epics_report` gained a new, clearly-labeled "Informational: BLOCKED epics (not
   stale — deliberately parked):" section, formatted with the file's existing `_format_epic_line`
   convention plus either "`N days idle`" or "`no child activity recorded`" — resolving the
   ticket's open question in favor of tracking blocked work with visibility rather than dropping it
   silently, per the ticket's own Assumptions section and `docs/plans/epic_staleness_status_aware_epic.md`.
7. Updated the module's own docstring with a new paragraph documenting this behavior, per this
   repo's convention of keeping the file's self-documentation accurate.

No changes to `DEFAULT_STALENESS_WINDOW_DAYS`, to any other agent-monitoring hook
(`retro_nudge_hook.py` untouched), or to the never-started bucket's existing semantics.

Deviation from ticket wording: the ticket's Scope line says "skip (or flag with a different,
non-actionable label) any ticket whose status is `BLOCKED` **with a stated rationale**." The
implementation does not additionally require/parse a "stated rationale" substring — it treats any
`## Status` value of `BLOCKED` as sufficient, matching the more precise 5-step "Implementation
guidance" in the ticket body (which says nothing about rationale-text parsing) and the design
doc's Scope section (same). Requiring a rationale to be present and parseable would add a fragile,
free-text-dependent check for no real benefit — the ticket-authoring convention already requires
`## Status: BLOCKED` to carry a rationale in the ticket body (as `TCK-20260730-CODEX-RUNTIME-
ACTIVATION-EPIC` does), so the body status value alone is a reliable, durable signal.

## Test Summary
Extended `tests/tools/test_epic_staleness_check.py` (pre-existing file, 10 test-group pattern) with
a new group 11 (7 new test functions, 20 total in the file, all passing via `.venv/bin/python3 -m
pytest tests/tools/test_epic_staleness_check.py -v`):
- `test_blocked_epic_with_stale_looking_activity_is_never_in_find_stale_epics` — synthetic BLOCKED
  epic with genuinely idle (8-day) child activity; confirms absence from `find_stale_epics()` and
  presence in the new informational/blocked report section.
- `test_blocked_epic_does_not_land_in_never_started_bucket` — synthetic BLOCKED epic with zero
  child activity; confirms it lands in the blocked bucket, not the never-started bucket.
- `test_genuinely_stale_non_blocked_epic_still_flagged_regression_guard` — acceptance-critical
  regression guard: a non-BLOCKED epic with the same idle shape is still flagged stale.
- `test_is_epic_blocked_reads_status_field` — unit-level coverage of the new predicate across
  BLOCKED / OPEN / unknown (`None`) status values.
- `test_folder_mode_no_epic_ticket_file_leaves_status_none_not_crash` — the folder-mode
  no-epic-ticket-file edge case explicitly called out in the implementation guidance; confirms
  `status is None` and no crash.
- `test_real_codex_runtime_activation_epic_is_status_aware` — integration-style confirmation
  against a read-only copy of the real `tickets/inprogress/TCK-20260730-CODEX-RUNTIME-ACTIVATION-
  EPIC.md` file (copied into a tmp_path fixture rather than pointed at the live tree, to stay
  independent of unrelated future repo changes), with synthetic idle child activity reproducing
  the exact false-positive shape this ticket was filed against.

Also ran the dependent test files that import `_section_body` from this module
(`tests/tools/test_epic_scope_orphan_check.py`, `tests/tools/test_status_drift_check.py`) — 24
passed, no regressions, confirming the unchanged `_section_body`/`_frontmatter_field` helpers were
not disturbed.

Ran the live hook report against the real repo state
(`.venv/bin/python3 tools/agent-monitoring/epic_staleness_check.py`): confirmed
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` now appears only under "Informational: BLOCKED
epics", not under "Stale epics", while a genuinely stale folder-mode candidate
(`FOLDER-tickets-todos-codex-runtime-activation`, which has no epic ticket file to read a status
from — a pre-existing, out-of-scope discovery-mode edge case, unrelated to this fix) is still
correctly flagged stale, proving the fix did not weaken real detection.

## Files Changed
- `tools/agent-monitoring/epic_staleness_check.py` — status-aware `EpicCandidate`, `is_epic_blocked`,
  three-bucket classification, blocked informational report section, docstring update.
- `tests/tools/test_epic_staleness_check.py` — `_write_ticket` helper gained an optional
  `body_status` parameter; 7 new tests added (group 11).
- `tickets/inprogress/TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC.md` — this file (Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `docs/plans/epic_staleness_status_aware_epic.md` — added `## Status: Resolved` section
  summarizing the fix and the open-question resolution.
- `docs/plans/architecture_resilience_remediation_roadmap.md` — added a `Status: Resolved` line
  under Epic E, matching the precedent already set for Epics A/B.
- `docs/guides/agent_monitoring.md` — added a "Stale vs. BLOCKED" subsection describing the new
  third bucket and updated the hook-nudge description.
- `docs/ai/ticket-lifecycle.md` — updated the epic-staleness-check and hook-nudge descriptions to
  cover the new BLOCKED bucket.

## Completion Summary
Taught `tools/agent-monitoring/epic_staleness_check.py` to read each candidate epic ticket's body
`## Status` field at discovery time, added an `is_epic_blocked` predicate, and routed BLOCKED
candidates into a new third classification bucket that `find_stale_epics` (the hook's fire
trigger) never returns from and that `compute_stale_epics_report` now surfaces separately as an
"Informational: BLOCKED epics (not stale — deliberately parked):" section — so
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` stops being misreported as neglected idle work while
staying visible as deliberately parked, and genuinely stale non-BLOCKED epics are still flagged
exactly as before. Verified via 7 new unit/integration tests (20/20 passing in the file), a live
run against the real repo ticket tree, and a check that dependent test files importing this
module's shared helpers still pass.
