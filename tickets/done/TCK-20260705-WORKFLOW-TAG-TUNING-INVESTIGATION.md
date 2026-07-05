---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION
phase: done
date: 2026-07-05
tags: [investigation, ai, workflows, tagging]
---

# TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION

## Title
Investigate skill usage per workflow step (by tag) and whether the ticket workflow needs tag/tier-driven tuning

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Two related investigation questions from the user:
1. Map which skills are used/suggested at each step of the ticket workflow (`create-tickets`,
   `implement-ticket`, `implement-epic`), based on the `Process/Skill-signal` tag mechanism shipped in
   `TCK-20260705-TAG-SKILL-SUGGEST`/`TCK-20260705-TAG-REGISTRY-QUERY`.
2. Investigate whether the ticket workflow needs tuning for different tasks/purposes — e.g., whether
   `implement-ticket` should skip or change phases based on ticket tier, tags, or suggested skill,
   beyond the existing hotfix/standard/epic tier short-circuit.

This is investigation-only — the deliverable is a findings/recommendations report, not automatic
implementation of any tuning. Whether to build any recommended tuning is a decision for the user after
seeing the findings.

## Scope
- Trace the current tag→skill→step wiring exactly: for each of the 4 mapped
  `Process/Skill-signal` tags (`api-design`, `debugging`, `performance`, `security`), confirm which
  step(s) of which workflow(s) currently compute/surface a `suggested_skills` value, and whether that
  suggestion is ever actually *consumed* (auto-invoked, gated on, or purely advisory/logged) anywhere
  downstream.
- Enumerate the current phase-skip logic in `implement-ticket.js`/`implement-epic.js` (today: only the
  `tier` field short-circuits Investigate/Plan/Review for hotfix). Confirm there is no existing
  tag-driven or skill-driven phase-skip/phase-add logic anywhere in the codebase (or find it if it
  exists).
- Identify concrete candidate tunings — e.g.: should a `performance`-tagged ticket auto-run
  `/python-performance-optimization` during Implement instead of just logging a suggestion? Should a
  `security`-tagged ticket require an extra gate (e.g., mandatory `/security-review` before Verify)?
  Should certain `Quality-attribute` or `Phase/Milestone` tags affect Test/Parity phase scope? Should a
  documentation-only ticket (no `Related Code Areas` under `src/`) skip Parity automatically rather than
  running a no-op parity-updater call?
- For each candidate tuning: assess feasibility, risk (does it violate "no silent scope creep" / "hard
  gates" design principles from `docs/ai/system_overview.md`/`docs/ai/README.md`), and whether it's
  worth building now vs. deferring.
- Produce a recommendations report — do not implement any tuning in this ticket.

## Out of Scope
- Actually implementing any recommended tuning (a separate, future ticket per whichever recommendations
  the user selects).
- Re-litigating the already-shipped `TAG-SKILL-SUGGEST`/`TAG-REGISTRY-QUERY` mechanisms themselves.
- Expanding the tag taxonomy or the 4-tag skill mapping (that's `TAG-SKILL-SUGGEST`'s own deferred
  question, not this investigation's).

## Acceptance Criteria
- [x] A clear table/mapping: tag → skill → which workflow phase(s) currently compute/surface it → is it
      consumed downstream or purely advisory. — Satisfied: `investigation.md` Part 1's table; all 4
      tags map to a skill, computed at 3 independent sites (`ticket-scoper.md`, `create-tickets.js`
      Structure, `implement-ticket.js` Scope), consumed nowhere downstream in either workflow —
      independently re-verified via grep (zero hits for `ticketInfo.suggested_skills` outside the one
      log block; zero hits for `ticketInfo.tags` at all).
- [x] Confirmation (with evidence) of whether any tag/skill-driven phase-skip or phase-change logic
      exists today, beyond the tier short-circuit. — Satisfied: `investigation.md` Part 2's exhaustive
      enumeration. Only `tier === 'epic'` (line 218) and `tier !== 'hotfix'` (line 242) drive any
      phase-skip; `implement-epic.js` has none of its own (delegates entirely to `implement-ticket.js`
      per child). No tag/type/priority/layer/Related-Code-Areas conditional found anywhere.
- [x] A list of concrete candidate tunings, each with a feasibility/risk assessment and a recommendation
      (build now / defer / reject), referencing the repo's own design principles. — Satisfied: 4
      candidates in `investigation.md`'s Risks and Open Questions — Candidate 2 (mandatory
      `/security-review` gate for `security`-tagged tickets) and Candidate 3 (skip Parity's agent call
      when post-Implement `files_changed` has no `src/` paths AND `behavior_changed` is false) are
      build-now; Candidate 1 (auto-invoke suggested skill) is defer; Candidate 4 (skip Test phase for
      docs-only tickets) is reject, directly falsified by this session's own
      `TCK-20260705-AI-AGENT-OVERVIEW-DOC` ticket.
- [x] No implementation performed — recommendations only, presented for user decision. — Satisfied:
      zero `.claude/`/`docs/` files touched outside this ticket's own text and staging artifacts;
      confirmed via `git status`. No follow-up ticket file created for any candidate.

## Related Tickets
- TCK-20260705-TAG-SKILL-SUGGEST (shipped the tag→skill suggestion mechanism this investigates)
- TCK-20260705-TAG-REGISTRY-QUERY (sibling, registry search filter — not directly relevant here but same source)
- TCK-20260705-AI-AGENT-OVERVIEW-DOC (the consolidated overview doc — cross-reference, don't duplicate)

## Related Docs
- docs/guides/ticket_tagging.md
- docs/ai/system_overview.md
- docs/ai/ticket-lifecycle.md
- docs/ai/workflows.md
- CLAUDE.md (Tier Routing, Design Principles)

## Related Stored Artifacts
staging_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/ (standard tier)

## Related Code Areas
- .claude/agents/ticket-scoper.md
- .claude/workflows/create-tickets.js
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js

## Assumptions / Open Questions
- Whether any recommended tuning gets built is explicitly left to the user after reviewing this
  investigation's findings — not decided here.

## Implementation Notes
This is an investigation-only ticket — no code or documentation source was written beyond the ticket's
own text and staging artifacts. Findings summary:

**Tag → skill → step mapping (all 4 currently-mapped `Process/Skill-signal` tags):**

| Tag | Suggested skill | Computed at | Consumed downstream? |
|---|---|---|---|
| `api-design` | `/api-design-principles` | `ticket-scoper.md`, `create-tickets.js` Structure, `implement-ticket.js` Scope | No — log only |
| `debugging` | `/debugging-strategies` (or `world-debugger` agent for world-assembly paths) | same 3 sites | No — log only |
| `performance` | `/python-performance-optimization` | same 3 sites | No — log only |
| `security` | `/security-review` | same 3 sites | No — log only |

The mapping table itself exists in 3 independent copies (`ticket-scoper.md`, `docs/guides/ticket_tagging.md`,
`implement-ticket.js`) with no shared source — a pre-existing, disclosed hazard from `TAG-SKILL-SUGGEST`,
not new here. Of the taxonomy's other 3 categories, only Subsystem/Topic has any consumption (a
registry search-filter, `TAG-REGISTRY-QUERY`'s `tools/registry_query.py`) — Phase/Milestone and
Quality-attribute drive zero workflow behavior today.

**Phase-skip logic enumeration:** `implement-ticket.js` has exactly 2 tier-driven branches
(`tier === 'epic'` → Scope-only; `tier !== 'hotfix'` → gates Investigate/Plan/Review) plus 5
content-based gates (unresolved-question, review verdict, test pass, DoD verdict, and the
`behavior_changed`-driven Parity *prompt* softening — which never skips the Parity agent call itself,
only changes its instructions). `implement-epic.js` has no tier/tag logic of its own — it delegates
entirely to `implement-ticket.js` per child ticket, so any future tuning built there applies epic-wide
automatically.

**4 candidate tunings assessed** (full detail in `stored_artifacts/.../investigation.md`):
1. Auto-invoke suggested skill during Implement — **Defer** (no JS-callable skill-invocation primitive
   exists yet; risks the "hard gates" principle since Implement's scope would silently expand past an
   already-approved plan).
2. Mandatory `/security-review` gate for `security`-tagged tickets — **Build now** (reuses the
   `suggested_skills` field already on `TICKET_SCHEMA`; a straight copy of the existing Review-gate
   pattern; additive, never skips anything).
3. Skip Parity's agent call when post-Implement `files_changed` has no `src/` paths AND
   `behavior_changed` is false — **Build now, narrowly** (must gate on authoritative post-Implement
   data, never Scope-time `Related Code Areas` guesses, to avoid a false-negative skip on scope drift).
4. Skip Test phase for docs-only tickets — **Reject** (directly falsified by this session's own
   `TCK-20260705-AI-AGENT-OVERVIEW-DOC` ticket, whose docs-only change legitimately required and passed
   a real `pytest tests/tools/test_validate_frontmatter.py` run — "no `src/`" is not a safe proxy for
   "no test surface").

Every load-bearing claim above was independently re-verified twice: once by the investigator agent via
direct file reads, once by the orchestrating session via direct grep against
`.claude/workflows/implement-ticket.js`/`implement-epic.js`, and a third time by the architecture
reviewer during its own independent spot-check. All three passes agree.

## Test Summary
No code test surface — this ticket touches no `src/`, `tests/`, or workflow/agent files. Verification
was fact-checking, not test execution: every specific claim (compute-site line numbers, phase names,
conditional line numbers) was independently re-derived from the actual `.claude/workflows/*.js` /
`.claude/agents/*.md` files by three separate passes (investigator, orchestrating session, architecture
reviewer) rather than trusted from a single source.

## Files Changed
None outside this ticket's own file and its staging artifacts
(`stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/{investigation.md,plan.md,test_plan.md}`
after Finalize). No `.claude/` or `docs/` source file was modified.

## Completion Summary
Investigated the current tag→skill→step wiring and confirmed `suggested_skills` (computed for all 4
mapped `Process/Skill-signal` tags at 3 independent sites) is purely advisory — logged but never
consumed by any later workflow phase. Confirmed the only existing phase-skip/phase-change logic in the
entire workflow layer is the `tier` short-circuit (hotfix/standard/epic); no tag, type, priority, or
`Related Code Areas` content changes phase execution anywhere today. Assessed 4 concrete candidate
tunings against the repo's own "hard gates"/"no silent scope creep" design principles: **recommend
building** a mandatory `/security-review` gate for `security`-tagged tickets (Candidate 2) and a
narrowly-scoped Parity-phase skip gated on authoritative post-Implement data (Candidate 3); **recommend
deferring** auto-invocation of suggested skills (Candidate 1, needs a skill-invocation primitive first);
**recommend rejecting** a Test-phase skip for docs-only tickets (Candidate 4, directly falsified by this
session's own evidence). No tuning was implemented and no follow-up ticket was filed — building any of
the recommended candidates is a decision left to the user.
