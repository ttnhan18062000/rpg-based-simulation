---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-DOCS-CONSISTENCY-PASS
phase: done
date: 2026-07-06
tags: [documentation, workflows, agent-monitoring]
---

# TCK-20260706-DOCS-CONSISTENCY-PASS

## Title
Sync remaining docs (system_overview.md, agents.md, agent_monitoring.md) with the tag-registry/reason_code work

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
User asked to update related documents after the tag-registry/reason_code/Scope-gate work
(4 prior tickets today). Audited every doc referencing the gate/status vocabulary or the
`suggested_skills`/tag mechanisms this session touched, to find genuinely stale content (not just
places that could theoretically mention the new work).

## Scope
- **`docs/ai/system_overview.md`**: Structure-phase description gains the tag-registry-check
  sentence; Scope-phase description gains the `TAGS_NOT_REGISTERED` gate; the explicit
  gate/return-status vocabulary list (a claimed-exhaustive list, now genuinely stale without this
  fix) gains `TAGS_NOT_REGISTERED` plus a note on `reason_code`.
- **`docs/ai/agents.md`**: `ticket-scoper`'s "What it does" list gains one bullet noting the
  orchestrator-side registry check and pointing at `tools/tag_registry.py list`.
- **`docs/guides/agent_monitoring.md`**: "Report Sections" table — a claimed-complete section
  list — gains the "Reason Codes" row `generate_retro.py` now sometimes renders, with
  interpretation guidance.
- `make docs-registry` + `make knowledge-index-update`.

## Out of Scope
- `docs/ai/skills.md`'s Tag-Based Skill Suggestions section — describes `suggested_skills`, a
  different mechanism from the registry check; not stale for what it actually describes, so left
  untouched rather than conflating two mechanisms in one section.
- `docs/ai/agent_infrastructure_audit.md`'s "seven structured statuses" claim — already
  imprecise before today's work (its own list omits `SECURITY_BLOCKED`/`NEEDS_HUMAN_INPUT`/
  `FINALIZE_INCOMPLETE` too, using an illustrative "…" rather than an exhaustive list) — a
  pre-existing accuracy gap unrelated to today's changes, disclosed here rather than silently
  left, but not fixed as part of a narrowly-scoped hotfix.

## Acceptance Criteria
- [ ] `system_overview.md`'s gate vocabulary list and phase descriptions are accurate against the
      live `.claude/workflows/*.js` files.
- [ ] `agents.md`'s `ticket-scoper` entry mentions the registry check.
- [ ] `agent_monitoring.md`'s Report Sections table lists "Reason Codes".
- [ ] `validate_frontmatter.py` passes on all touched docs; `docs-registry`/`knowledge-index-update`
      run successfully.

## Related Tickets
- TCK-20260706-TAG-REGISTRY-DATA, TCK-20260706-MONITORING-REASON-CODE,
  TCK-20260706-SCOPE-TAG-REGISTRY-CHECK, TCK-20260706-CREATE-TICKETS-TAG-CHECK (the work this
  ticket's doc updates keep in sync)

## Related Docs
- docs/ai/system_overview.md, docs/ai/agents.md, docs/guides/agent_monitoring.md

## Related Stored Artifacts
None (hotfix tier — no staging artifacts).

## Related Code Areas
None — documentation-only.

## Assumptions / Open Questions
- `docs/ai/agent_infrastructure_audit.md`'s pre-existing "seven statuses" imprecision is disclosed,
  not fixed — flagged as an existing, unrelated accuracy gap for a future pass if ever prioritized.

## Implementation Notes
Audited via grep for every doc mentioning `CONFLICTS_DETECTED` (a reliable proxy for "documents the
gate vocabulary") and every doc mentioning `suggested_skills`/tag-based skills (a proxy for "documents
the tag-driven mechanisms"), then read each candidate to distinguish genuine staleness (a claimed-
exhaustive list now missing an entry) from doc scope that simply doesn't need updating (narrative/
audit docs using illustrative, non-exhaustive examples). Found and fixed 3: `system_overview.md`
(exhaustive vocabulary list + 2 phase descriptions), `agents.md` (ticket-scoper's role description),
`agent_monitoring.md` (Report Sections table). Explicitly did not touch `skills.md` (different
mechanism, not stale) or `agent_infrastructure_audit.md` (pre-existing, unrelated imprecision).

## Test Summary
Documentation-only. `validate_frontmatter.py` passed on all 3 touched files. `make docs-registry`
(256 docs indexed) and `make knowledge-index-update` (6 files re-embedded) both completed
successfully.

## Files Changed
- `docs/ai/system_overview.md`
- `docs/ai/agents.md`
- `docs/guides/agent_monitoring.md`
- `docs/REGISTRY.yaml` (regenerated)
- `tickets/inprogress/TCK-20260706-DOCS-CONSISTENCY-PASS.md` → `tickets/done/...`

## Completion Summary
Closed the gap between "documents that claim to exhaustively list the gate/report vocabulary" and
the actual vocabulary after today's 4 tickets: `system_overview.md`'s gate-status list and 2 phase
descriptions, `agents.md`'s ticket-scoper entry, and `agent_monitoring.md`'s Report Sections table
are now all accurate. Two candidates were deliberately left alone after reading them, not just
skipped: `skills.md` (describes a genuinely different mechanism, not stale) and
`agent_infrastructure_audit.md` (a pre-existing, unrelated imprecision, disclosed not fixed).
