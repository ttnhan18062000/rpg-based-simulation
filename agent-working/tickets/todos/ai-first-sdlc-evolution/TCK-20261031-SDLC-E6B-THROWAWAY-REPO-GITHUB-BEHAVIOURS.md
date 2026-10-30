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
E6b (plan section 27a) is approved as a test by #715 6529263880. It comes first among the authority work because OD-3's M1 is subject to it. The owner creates the repo and the machine account; no agent does either. No production settings are touched.

## Scope
1. Owner's steps, as their own ask through lead-planner, before anything else starts: (a) create the machine account, the one free machine account Phase 1 will also use; (b) create the throwaway public repo; (c) add the account as a collaborator on that repo only, with a token that cannot reach this repo. The account stays out of this repo until the Phase 1 ask. Handing the token to the test run is agreed with the owner in that ask, and its value appears nowhere.
2. Primary rows, which M1 rests on: a non-admin collaborator is refused merge and push to main under the `update` rule; the owner's bypass merge works, including with red checks; `--match-head-commit` refuses a late push, and how a browser merge behaves.
   Then the rest of the section 27a list: author self-approval (mainly M2's concern); `POST /git/refs` on an existing ref and under a race; a same-named job in a PR against a failing check; a deleted-and-replaced gate job; bypass actor types on a personal repo; skipped matrix legs; tag ruleset against the machine user; classic PAT without `workflow` scope on workflow files; automatic head-branch deletion and stacked PR retargeting.
3. Record each result as confirmed, refuted or not tested, with its evidence, in a committed artifact. Report to agent-working-designer whether M1 holds.

## Out of Scope
- Any change to the production repo's settings, rulesets or credentials.
- Deciding OD-3 again or OD-13: the results are inputs.
- Keeping the repo: its removal is the owner's, and is named in the handoff.
- Any access for the machine account to this repo (the Phase 1 ask).

## Acceptance Criteria
1. Every question in the E6b list has a result, or a stated reason it was not tested.
2. The artifact has no credential value or host credential detail.
3. The M1 verdict is stated from the primary rows, and the plan's E6b-dependent claims are listed as held or changed.

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
- Owner ruling, given in the designer's terminal, lead-planner logging it on #715: the owner creates the account and the repo.
- OPEN: how the test run gets the account's token without its value entering a transcript or shard; part of the owner's ask.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
