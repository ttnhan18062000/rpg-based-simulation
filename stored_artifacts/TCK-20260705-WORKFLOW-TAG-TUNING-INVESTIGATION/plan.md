---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION
artifact_type: plan
tags: [investigation, ai, workflows, tagging]
---

# Plan — TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION

## Summary

This is an investigation-only ticket with no code change. `investigation.md` already produced a
complete Part 1 (tag→skill→step wiring, with the key finding that `suggested_skills` is computed in 3
places but consumed nowhere downstream — purely a log line) and Part 2 (exhaustive phase-skip logic
enumeration — only `tier` drives any phase-skip today) and Part 3 (4 candidate tunings, each with a
trigger/change/feasibility/risk/recommendation, independently re-verified by the orchestrating session
against the actual `.claude/workflows/*.js` files: Candidate 2 build-now, Candidate 3 build-now
narrowly, Candidate 1 defer, Candidate 4 reject).

This ticket's own deliverable is the investigation and recommendations, not any implementation. The
Plan phase here is lightweight: finalize the ticket's own text with the findings/recommendation
summary so a future reader (and the user, who explicitly asked to "help me investigate" rather than
"implement") has a clear, self-contained record — no wiring, no new ticket files created for the
candidates (that's an explicit future decision, per this ticket's own Out of Scope).

## Steps

### Step 1 — Finalize the ticket's own text with the findings summary
- **Files:** `tickets/inprogress/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION.md`.
- **Do:**
  - Check off all 4 Acceptance Criteria with their disposition, citing `investigation.md`'s specific
    sections.
  - Fill `Implementation Notes` with the tag→skill→step mapping table and the phase-skip enumeration
    summary.
  - Fill `Test Summary` noting this is investigation-only — no code test surface; note the independent
    re-verification the orchestrating session performed (grep-confirmed every key claim).
  - Fill `Files Changed`: none (investigation-only); artifacts path only.
  - Fill `Completion Summary`: the 4 candidates and their recommendations (build-now/defer/reject), with
    an explicit statement that no ticket was filed for any candidate — that decision is left to the
    user.
- **Do NOT touch:** any `.claude/workflows/*.js`, `.claude/agents/*.md`, or other doc file — this
  ticket's Out of Scope forbids implementing any tuning.
- **Verify:** manual diff read; confirm the ticket's own text doesn't imply anything was wired.

### Step 2 — Cleanup pass (Definition of Done housekeeping)
- **Files:** `data/runs/*`, `reports/release_proof/*` if present.
- **Do:** confirm empty (expected no-op — this ticket generates no simulation run data).
- **Verify:** `git status` shows no stray untracked run artifacts.

### Step 3 — Final verification pass
- **Files:** none (read-only).
- **Do:** re-confirm the 3 grep-based claims independently re-verified in this session (suggested_skills
  log-only, tags absent from TICKET_SCHEMA, tier conditional line numbers) still hold — no code changed
  in the interim, so this is a formality, not a re-investigation.
- **Verify:** matches investigation.md exactly.

## Scope Guards

- No implementation of any of the 4 candidate tunings.
- No new ticket file created for any candidate — recommendation only, decision left to the user.
- No edit to any `.claude/` or `docs/` file beyond this ticket's own text and its staging artifacts.

## Dependency Map

- Step 1 depends on investigation.md's findings (already complete).
- Steps 2-3 are independent verification/cleanup, run after Step 1.

## Acceptance Criteria Map

| AC | Original wording | Disposition | Verified by |
|---|---|---|---|
| AC1 | Clear tag→skill→phase→consumed table | Satisfied — investigation.md Part 1's table, independently re-verified via grep | Direct grep of `implement-ticket.js`/`create-tickets.js` |
| AC2 | Confirmation of existing tag/skill-driven phase logic | Satisfied — Part 2's exhaustive enumeration: none exists beyond `tier` | Direct grep for `tier ===`/`tier !==`/`tags`/`suggested_skills` |
| AC3 | List of candidate tunings with feasibility/risk/recommendation | Satisfied — 4 candidates in Part 3, each independently re-verified | investigation.md Risks and Open Questions section |
| AC4 | No implementation performed | Satisfied — zero files outside `staging_artifacts/`/ticket text touched | `git status` |

## Anti-Drift Notes

- Do not let "investigation complete" read as "tunings decided" — the ticket's Completion Summary must
  make clear that Candidates 2 and 3 are recommended, not yet approved for building; the user decides
  whether/when to file a follow-up implementation ticket.
- Do not create a follow-up ticket file as part of this ticket's Finalize — that would contradict this
  ticket's own Out of Scope and the established "recommend, don't auto-create" pattern from this
  session's other investigation tickets (SIX-SKILLS-INVESTIGATION, WORKING-LOG-BACKFILL).
