---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-E6B-THROWAWAY-REPO-GITHUB-BEHAVIOURS
phase: open
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-E6B-THROWAWAY-REPO-GITHUB-BEHAVIOURS

## Title
The GitHub behaviours the merge and credential design depends on are tested on a throwaway public repo.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
E6b (plan section 27a) is approved as a test by #715 6529263880. It comes first among the authority work because OD-3's M1 is subject to it. Creating the repo still needs its own owner ask. No production settings are touched.

## Scope
1. Ask the owner, through lead-planner, to create the throwaway repo. Nothing else starts before that.
2. Run the section 27a E6b list: M1 bypass merge with red checks; author self-approval; `POST /git/refs` on an existing ref and under a race; a same-named job in a PR against a failing check; a deleted-and-replaced gate job; bypass actor types on a personal repo; skipped matrix legs; `--match-head-commit` against a late push, and browser merge behaviour; tag ruleset against the machine user; classic PAT without `workflow` scope on workflow files; automatic head-branch deletion and stacked PR retargeting.
3. Record each result as confirmed, refuted or not tested, with its evidence, in a committed artifact. Report to agent-working-designer whether M1 holds.

## Out of Scope
- Any change to the production repo's settings, rulesets or credentials.
- Deciding OD-3 again or OD-13: the results are inputs.
- Keeping the repo: its removal is the owner's, and is named in the handoff.

## Acceptance Criteria
1. Every question in the E6b list has a result, or a stated reason it was not tested.
2. The artifact has no credential value or host credential detail.
3. The M1 verdict is stated, and the plan's E6b-dependent claims are listed as held or changed.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- none in the repo; external throwaway repo
- agent-working/stored_artifacts/ (result record)

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- OPEN, raised with agent-working-designer: several E6b questions need a second identity (self-approval, the machine user against a tag ruleset, a PAT without `workflow`). The machine user does not exist yet and creating it is its own ask. Either the owner provides a test identity, or those rows are recorded as not tested until Phase 1.
- OPEN: which identity runs the test while owner credentials are the only ones on the hosts; part of the owner ask.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
