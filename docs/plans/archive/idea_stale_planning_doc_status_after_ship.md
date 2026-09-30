---
status: historical
layer: ai
authority: P2
audience: developer
maturity: shipped
archived: 2026-09-30
date: 2026-09-29
tags: [idea, documentation, process-improvement]
---

> **Shipped 2026-09-30** as `TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR`: a periodic sweep
> (`make planning-doc-staleness-check`), not a close-time prompt. Resolution convention adopted: a
> fully shipped idea doc moves to `docs/plans/archive/` with `status: historical`; a shipped item
> inside an active doc gets an inline dated note. This doc is the first application of it. See
> `docs/ai/ticket-lifecycle.md`.

# Idea: Planning Docs Keep Claiming "idea"/"ready" Status After Their Own Item Already Shipped

## Problem

Several `docs/plans/` planning documents still say an item is open ("idea", "ready — schedule
later") after a real ticket has already shipped exactly that item — nothing currently re-checks a
planning doc's own claimed status against `tickets/done/` once the referenced ticket closes.

**Confirmed on real data, not speculative** — found while looking for a small real proposal to
pilot a tooling change against:

- `docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md` (frontmatter
  `status: idea`, dated 2026-07-28) describes adding an active/idle duration split to
  `generate_retro.py`. This shipped as `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` and
  `TCK-20260822-DASHBOARD-DURATION-GAP-AWARE` (both in `tickets/done/`, folder
  `tickets/done/agent-monitoring-active-duration/`). The idea doc was never updated or moved to
  `docs/plans/archive/` the way a sibling idea in the same doc's own "Natural Integration Points"
  table says shipped ideas should be (it points at
  `../archive/agent_infrastructure/idea_agent_monitoring_pause_resume_seq_collision.md` as the
  precedent for exactly this).
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (frontmatter
  `status: active`, dated 2026-09-04) lists two of its four numbered items as still open
  ("Horizon 2 — ready, schedule later"): item 3, "working_log.csv parser and cleanup", and item 4,
  "Provider-portability conformance test." Both already shipped —
  `TCK-20260904-WORKING-LOG-CSV-PARSER` and `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`
  are both in `tickets/done/`, dated the same day as the planning doc itself.

A reader (human or agent) landing on either doc today would reasonably conclude real, unstarted
work remains — and could duplicate it, exactly the failure mode `create-tickets.js`'s own
duplicate-detection step exists to catch, but only if the investigating agent happens to search
`tickets/done/` for the right keywords rather than trusting the planning doc's own stated status.

## Idea

When a ticket closes and its own `## Related Docs` (or a `docs/plans/` doc's own text) names a
specific planning document as the source of the shipped work, flag that planning doc for a status
update — either as part of ticket close ("After Work" → "Update related docs" already covers this
in principle, but nothing currently prompts *which* planning doc, or verifies it actually got
touched) or as a periodic sweep (similar in spirit to the existing epic-staleness check) that
diffs each `docs/plans/*idea*.md` / "ready, schedule later" item against `tickets/done/` for an
obvious title/keyword match and flags a mismatch for a human or agent to resolve — never
auto-edits the doc, since only a person can judge whether the shipped ticket actually covers the
full idea or just part of it.

## Open Questions

- Sweep vs. close-time prompt: a close-time prompt only catches the doc if the closing agent
  correctly identifies which planning doc the ticket traces back to (not always explicit); a
  periodic sweep catches drift regardless of traceability at close time but costs a standing tool
  to build and run. Which is worth it depends on how often this actually recurs — this doc only
  has two confirmed instances so far, both found incidentally, not from a systematic search.
- Should a "shipped" planning doc move to `docs/plans/archive/` (mirroring the existing convention
  for done ideas), get an inline status-frontmatter flip to `status: historical`, or just get a
  dated note appended in place? The existing repo convention has done both in different places —
  worth picking one and applying it consistently rather than deciding per-doc.

---

*Raised: 2026-09-29, found incidentally while picking a real, small, not-yet-ticketed proposal to
pilot `create-tickets.js`'s first native `Workflow`-tool run against
(`TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT`) — not a synthetic test input.*
