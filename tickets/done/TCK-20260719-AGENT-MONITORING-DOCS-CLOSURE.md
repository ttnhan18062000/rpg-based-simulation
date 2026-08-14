---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-AGENT-MONITORING-DOCS-CLOSURE
phase: open
date: 2026-07-19
tags: [agent-monitoring, observability, documentation]
---

# TCK-20260719-AGENT-MONITORING-DOCS-CLOSURE

## Title
Archive shipped agent-monitoring-data-quality/live-phase-label planning docs and correct dependent doc claims

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
User asked to "update all related documents, add new if needed" after the
`agent-monitoring-data-quality` epic (5 tickets) and `TCK-20260719-LIVE-PHASE-AGENT-LABEL` both
shipped and were committed. Self-evident documentation housekeeping: apply this repo's established
archiving convention to the two now-shipped planning docs, and — since a live-phase-labeling ticket
partially, not fully, shipped its source idea's stated goal — correct two dependent docs
(`docs/guides/agent_ops_dashboard.md`, `docs/observability/agent_ops_dashboard_contract.md`) whose
"Known Limitation" sections made a claim that is now half-true rather than fully true.

## Scope
- Move `docs/plans/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md` and
  `docs/plans/agent_infrastructure/proposal_agent_monitoring_data_quality.md` to their respective
  `docs/plans/archive/` subfolders (`git mv`), with `maturity: shipped` + `archived: 2026-07-19`
  frontmatter and an accurate "Archived:" summary line citing real shipping ticket IDs.
- The live-phase-label archive note explicitly states this was a **partial** ship: the
  data-producing half (nullable `phase`/`agent` fields now on `tools.jsonl`) shipped; the
  dashboard-consumption half the idea doc was ultimately for (a live "Implement (implementer)
  running" indicator) did not, and remains a real, unticketed follow-up — not silently dropped.
- Fixed 6 cross-references in `docs/plans/archive/agent_ops_dashboard/idea_agent_ops_dashboard.md`
  (paths + partial-ship annotations) and one stale "Relationship to Planned Tickets" section that
  predated an earlier archiving pass and still said "None yet" despite the doc's own header already
  listing 5 shipped tickets.
- Corrected `docs/guides/agent_ops_dashboard.md`'s and `docs/observability/agent_ops_dashboard_contract.md`'s
  "Known Limitation" sections: both previously claimed the underlying `tools.jsonl`/`RawToolCall`
  data has no `phase`/`agent` field at all. That's now only half true — the raw JSONL data exists
  (as of `TCK-20260719-LIVE-PHASE-AGENT-LABEL`), but the dashboard's own `RawToolCall` model and
  Replay Timeline view were confirmed (via direct code read) still unwired to it, so the visible
  "phase unknown" caption is unchanged — only the underlying reason shifted. Removed the stale
  `MONITORING_INSTRUMENTATION_GAP` reference (that idea doc no longer exists under that name).
- Added 2 missing rows ("Phase Status Distribution", "Outliers") to `docs/guides/agent_monitoring.md`'s
  Report Sections table, and the missing `make agent-monitoring-weight-check` line to its Makefile
  Targets section — both were real gaps left by `TCK-20260719-PHASE-AGENT-CASE-FOLD`,
  `TCK-20260719-RETRO-OUTLIER-FLAGS`, and `TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE`, none of which
  updated this particular guide (they updated `docs/agent-monitoring/schema.md`/`README.md`
  instead, which are field/tool references, not the report-section walkthrough this guide is).
- Fixed one stale self-referential footer line in the archived data-quality proposal doc.
- Regenerated `docs/REGISTRY.yaml` and the knowledge search index.

## Out of Scope
- Wiring the Agent Ops Dashboard's `RawToolCall`/Replay Timeline to actually consume the new
  `phase`/`agent` fields — confirmed real, identified, unticketed follow-up work; explicitly not
  done here, only accurately documented as still-open.
- `docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md` — confirmed still
  genuinely unimplemented (4 draft tickets remain queued, untouched, in
  `tickets/todos/agent-monitoring-derived-index/`); not archived.
- Any code change — pure documentation/comment housekeeping.

## Acceptance Criteria
- [x] Both docs moved to `docs/plans/archive/{topic}/` via `git mv`, frontmatter and archived-note
      content accurate against real shipping ticket IDs (verified via `tickets/working_log.csv`
      and each ticket's own `## Files Changed`).
- [x] The live-phase-label archive note precisely distinguishes shipped (data) vs. unshipped
      (dashboard consumption) — not overclaimed as fully shipped.
- [x] `docs/guides/agent_ops_dashboard.md` and `docs/observability/agent_ops_dashboard_contract.md`'s
      Known Limitation sections corrected, verified against a direct read of
      `src/api/agent_ops_dashboard/models.py::RawToolCall` (confirmed unchanged, no `phase`/`agent`
      field) — not asserted from the ticket's own report alone.
- [x] `docs/guides/agent_monitoring.md`'s Report Sections table and Makefile Targets section cover
      all report sections/targets that exist in `tools/agent-monitoring/generate_retro.py`'s actual
      output and the `Makefile`'s actual targets, verified by direct grep against both.
- [x] `python3 tools/validate_frontmatter.py --content-type doc <each touched file>` passes clean.
- [x] `make docs-registry` regenerates cleanly with 0 occurrences of the old paths.
- [x] `make knowledge-index-update` runs clean.
- [x] Repo-wide grep for both old doc paths turns up only expected historical-record hits (closed
      tickets, stored_artifacts, `agent-monitoring/tools.jsonl`).

## Related Tickets
TCK-20260719-PHASE-AGENT-CASE-FOLD, TCK-20260719-COST-PROXY-WRITE-PATH,
TCK-20260719-RETRO-OUTLIER-FLAGS, TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE,
TCK-20260719-COST-PROXY-CALIBRATION-NOTE, TCK-20260719-LIVE-PHASE-AGENT-LABEL,
TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE (the prior, structurally identical doc-closure ticket
this one directly follows the same convention from)

## Related Docs
- docs/plans/archive/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md (archived)
- docs/plans/archive/agent_infrastructure/proposal_agent_monitoring_data_quality.md (archived)
- docs/plans/archive/agent_ops_dashboard/idea_agent_ops_dashboard.md (cross-refs fixed)
- docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md (Known
  Limitation corrected)
- docs/guides/agent_monitoring.md (Report Sections + Makefile Targets gaps filled)

## Related Stored Artifacts
None — hotfix tier, self-evident doc-housekeeping intent captured directly in this ticket.

## Related Code Areas
- docs/plans/agent_ops_dashboard/, docs/plans/agent_infrastructure/, docs/plans/archive/
- docs/guides/agent_ops_dashboard.md, docs/guides/agent_monitoring.md
- docs/observability/agent_ops_dashboard_contract.md
- docs/REGISTRY.yaml (regenerated)

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Verified the "Known Limitation" correction's precision by reading `src/api/agent_ops_dashboard/models.py`
directly rather than trusting either ticket's own self-report: `RawToolCall` genuinely still has no
`phase`/`agent` field (confirmed unchanged), so the doc correction states the visible dashboard
behavior is unchanged while only the underlying *reason* shifted — avoids the failure mode of
over-claiming a fix that only partially landed.

Followed the exact archiving convention established earlier this session
(`TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE`) and, before that, its own precedent
(`docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md`).

## Test Summary
- `python3 tools/validate_frontmatter.py --content-type doc <each of the 6 touched docs>` — all
  pass clean.
- `make docs-registry` — 1458 entries; confirmed 0 occurrences of both old doc paths.
- `make knowledge-index-update` — 18 files changed/new, 2 deleted, clean incremental update.
- Repo-wide `grep -rl` sweep for both old doc paths — remaining hits are exclusively closed
  tickets, stored_artifacts, and `agent-monitoring/tools.jsonl`, matching established precedent.

## Files Changed
- docs/plans/archive/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md (moved + archived)
- docs/plans/archive/agent_infrastructure/proposal_agent_monitoring_data_quality.md (moved + archived)
- docs/plans/archive/agent_ops_dashboard/idea_agent_ops_dashboard.md (6 cross-refs + 1 stale section fixed)
- docs/guides/agent_ops_dashboard.md (Known Limitation corrected)
- docs/observability/agent_ops_dashboard_contract.md (Known Limitation corrected)
- docs/guides/agent_monitoring.md (2 new Report Sections rows, 1 new Makefile Targets line)
- docs/REGISTRY.yaml (regenerated)

## Completion Summary
Both fully-shipped agent-monitoring planning docs are now archived with accurate, precisely-scoped
shipping citations — including an explicit, non-overclaiming note that the live-phase-label idea
only partially shipped (data-producing half only; dashboard-consumption half remains real, open,
unticketed work). Two dependent docs' "Known Limitation" claims were corrected to match this same
precise reality, verified against a direct read of the dashboard's own Pydantic model rather than
trusted from either shipping ticket's self-report. Two real documentation gaps (missing retro
report-section rows, missing Makefile target reference) left by three of the epic's tickets were
filled. `docs/REGISTRY.yaml` and the knowledge index were regenerated; a repo-wide sweep confirmed
no live doc or code cross-reference was left pointing at a stale path.
