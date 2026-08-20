---
status: historical
layer: ai
authority: P1
audience: agent
maturity: shipped
archived: 2026-08-20
tags: [ai, process-improvement]
---

# Epic Plan — Epic-Staleness Hook: Status-Aware Before Flagging

**Tracking ticket:** `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §F; `docs/audits/D24_codebase_health_observatory.md` §A, §H (full case study)
**Priority:** P1 — small, precisely scoped, and a live false positive rather than a hypothetical one.

## Status
Resolved by `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC`. The Problem section below now
describes pre-fix history, not current state: `tools/agent-monitoring/epic_staleness_check.py`
reads each candidate epic's body `## Status` field at discovery time (`EpicCandidate.status`), and
`is_epic_blocked()` routes any candidate whose status is `BLOCKED` into a third classification
bucket that `find_stale_epics` (the hook fire-trigger) never returns and that
`compute_stale_epics_report` surfaces separately under "Informational: BLOCKED epics (not stale —
deliberately parked):" — resolving this doc's open "disappear entirely vs. informational list"
question in favor of the informational list. `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` no
longer appears under "Stale epics" while its `BLOCKED` status stands; a genuinely stale,
non-`BLOCKED` epic is still flagged exactly as before (regression-guarded by
`test_genuinely_stale_non_blocked_epic_still_flagged_regression_guard`). Left in place (not
archived) per this repo's convention that whole-epic archival is a separate human decision.

## Problem

`make agent-monitoring-epic-staleness` measures file-mtime idleness only. It has flagged
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` as idle past its 5-day staleness window throughout
this entire session — while that ticket's own frontmatter states `phase: blocked` and its body
carries a dated, explicit deferral rationale ("2026-08-02 decision: temporarily defer live Codex
activation... This epic remains BLOCKED... resumption requires a new explicit owner decision").
This is a deliberately governed pause, fully documented, one `cat` away from being understood —
not ambiguous ownership or silent neglect. The hook has no way to read that; it fired again while
this very roadmap and its epics were being written, and will keep firing on any correctly-parked
`BLOCKED` epic until it's taught to check ticket status.

## Scope for the eventual `create-tickets` pass

- Teach the staleness-check script/hook to read the target ticket's `## Status` body field before
  flagging, and skip (or flag with a different, non-actionable label) any ticket whose status is
  `BLOCKED` with a stated rationale.
- Decide whether `BLOCKED` tickets should still surface in the report (e.g. as an informational
  "parked" list) rather than disappear entirely — losing visibility into genuinely-blocked work
  is its own risk; the fix is to stop treating "blocked and stale" as identical to "forgotten and
  stale," not to stop tracking blocked work.

## Out of scope

- Any change to the epic-staleness threshold (5 days) itself.
- Broader agent-monitoring tooling changes beyond this one hook's status-awareness.

## Acceptance signal for this epic (not yet broken into child tickets)

- Running the staleness check against `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` in its current
  `BLOCKED` state no longer produces the same undifferentiated "stale" flag it does today.
- A genuinely stale, non-`BLOCKED` epic still gets flagged correctly (the fix must not weaken the
  hook's real usefulness).

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic E)
- `docs/audits/D24_codebase_health_observatory.md` (§H, full worked case study; §M Phase 3 item 9)
