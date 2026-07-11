---
status: idea
layer: ai
authority: P2
audience: developer
maturity: idea
date: 2026-07-11
tags: [idea, agent-infrastructure, workflow-orchestration]
---

# Idea: Epic-Tier Scope Phase Leaves an Orphaned Ticket Duplicate in `tickets/inprogress/`

> Raised 2026-07-11 while running `implement-ticket` on an epic-tier ticket
> (`TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC`) as part of continuing the
> `workflow-execution-determinism` batch. Confirmed live, not hypothetical.

## Problem

`.claude/workflows/implement-ticket.js`'s Scope phase runs the same ticket-scoper prompt for every
tier. When a ticket is discovered under `tickets/todos/**/`, Step 1c of that prompt unconditionally
copies it to `tickets/inprogress/{tid}.md` "so it enters the standard workflow location" — this
happens before the tier is even known to the orchestrator (`tier` is read from the agent's return
value one line later, at `implement-ticket.js:141`).

For `hotfix`/`standard` tickets this copy is later reconciled by Finalize (phase 9), which either
moves `tickets/inprogress/{tid}.md` → `tickets/done/{tid}.md` (on `DONE`) or leaves it in
`tickets/inprogress/` deliberately as the live working copy while the ticket is paused
(`NEEDS_HUMAN_INPUT`/`BLOCKED`/etc., pending a future re-run that eventually reaches Finalize).

For `tier === 'epic'`, though, `implement-ticket.js:333-341` returns `EPIC_SCOPED` immediately after
Scope — this is intentional per CLAUDE.md's Tier Routing table ("epic: Scope only — tracks child
tickets; no direct implementation"). But this early return means **Finalize is never reached for an
epic ticket, ever, by design.** Nothing else in the pipeline deletes the `tickets/inprogress/`
copy or reconciles it against the `tickets/todos/` original. The result is a byte-identical
duplicate of the epic ticket that will sit in `tickets/inprogress/` permanently — it does not
self-resolve the way a paused standard/hotfix ticket's duplicate does, because an epic ticket never
has a "later Finalize run" to look forward to.

**Confirmed live:** running `implement-ticket` directly on `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC`
(tier=epic, already fully scoped, both children accounted for) left
`tickets/inprogress/TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC.md` as an exact duplicate of
`tickets/todos/workflow-execution-determinism/TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC.md`
(confirmed via `diff`, zero output). Nothing in the pipeline would have cleaned this up — it was
removed manually in that session. This will recur for **every** epic ticket ever processed through
`implement-ticket.js`'s Scope phase, including epics that were already fully scoped and are just
being re-confirmed (a legitimate, expected use per this repo's own recent practice — e.g. re-running
Scope on an already-scoped epic to confirm its children's current state).

This is a `tickets/` repo-hygiene bug, not a mechanics/engine correctness issue — no durable
simulation state is affected. But it directly contradicts this repo's Definition of Done condition
"Repo state is consistent" and the Workflow Rule's "Verify no leftover staging/temp files remain,"
both of which currently have no automated check that would catch this specific case (an epic-tier
duplicate is not `staging_artifacts/` or `data/runs/`, so existing cleanup steps don't look at it).

## Idea

Two independent, non-exclusive fixes — either alone would close the gap; both together are the most
robust prevention-plus-detection combination the existing `gate_checks` precedent shape supports:

1. **Prevention — skip the inprogress copy for epic tier.** The ticket-scoper's Step 1c copy
   instruction currently runs unconditionally at Scope time, before tier is known. The simplest fix:
   read the `## Tier` field as part of the *existing* Step 1c/Step 2 read (the prompt already reads
   the file at that point to extract Tier at Step 2 — this ordering could be swapped so Tier is known
   before deciding whether to copy), and skip the `cp` if tier is `epic`. This keeps `ticket_path`
   pointing at the `tickets/todos/` original for epic tickets specifically, matching the fact that no
   further phase will ever write to or move that path.
2. **Detection — a static self-check.** Mirroring `tools/gate_checks/done_checker_static.py`'s
   existing precedent shape (e.g. `run_finalize_selfcheck`), a small check that scans
   `tickets/inprogress/*.md` for any file whose frontmatter or `## Tier` reads `epic` and flags it —
   an epic ticket should never legitimately be a resident of `tickets/inprogress/` for more than the
   duration of a single Scope-phase agent call, so any epic ticket found there at rest is itself
   evidence of this bug (or a stale leftover from before this fix landed). Useful as a one-time sweep
   for any pre-existing orphans plus an ongoing regression guard, independent of whether fix 1 is also
   applied.

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `.claude/workflows/implement-ticket.js`'s Scope-phase agent prompt (Step 1c, ~line 61-63) | The unconditional copy instruction that needs the tier-aware guard |
| `tools/gate_checks/done_checker_static.py` | Existing static-check module/precedent shape a new epic-orphan sweep would mirror |
| CLAUDE.md's Definition of Done ("Repo state is consistent") | The DoD condition this bug currently has no automated coverage for |

## Open Questions

- Should the fix be a one-line prompt-ordering change (read Tier before deciding to copy), or does it
  need the orchestrator itself to pass a hint (harder, since `tier` genuinely isn't known to the
  orchestrator until the Scope agent returns)? Leaning toward the prompt-ordering fix since Step 2
  already reads the same file to extract Tier — no new file read is needed, just resequencing.
- Is a dedicated detection script (idea 2) worth building for a bug whose prevention (idea 1) is a
  one-line change, or is prevention alone sufficient? Given epic tickets are created relatively rarely
  compared to standard/hotfix tickets, the ongoing regression risk may not justify a dedicated script
  — but a one-time sweep to find and clean any *pre-existing* orphans (created before this fix lands)
  is likely still worth doing once, even if not kept as a permanent gate.
- Are there other pre-existing orphaned epic-ticket duplicates already sitting in
  `tickets/inprogress/` from before this was noticed? Not checked as part of raising this idea —
  `tickets/inprogress/` currently contains only `.gitkeep` at time of writing, but this should be
  verified as part of whichever ticket picks this up, not assumed clean.

---

*Raised: 2026-07-11, discovered live while processing an already-fully-scoped epic ticket through
`implement-ticket.js` as part of continuing the `workflow-execution-determinism` folder batch.*
