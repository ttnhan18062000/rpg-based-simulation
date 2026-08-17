---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, process-improvement]
---

# Epic Plan — Epic-Staleness Hook: Status-Aware Before Flagging

**Tracking ticket:** `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §F; `docs/audits/D24_codebase_health_observatory.md` §A, §H (full case study)
**Priority:** P1 — small, precisely scoped, and a live false positive rather than a hypothetical one.

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
