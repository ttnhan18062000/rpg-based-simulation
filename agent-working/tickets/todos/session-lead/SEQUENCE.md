# Implementation Sequence — session-lead

Epic E children (`TCK-20261009-EPIC-SESSION-LEAD-PLANNER`), filed by agent-working-planner. E1 landed in #476.
Batch 2 of the agent-working queue (2026-10-11) carries items 1-2, together with
`session-layer-followups/SEQUENCE.md` items 1-2. E2, E3, E5 and E6 are not filed yet.

## Order

1. TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD  (E4b; no deps; standard; manifest edit, edits cross_session_messages.md)
2. TCK-20261011-SESSION-START-FOR-ROLE-ISSUES  (E4a; depends on: 1 for the shared guide edit; standard; issue #492)
3. TCK-20261013-HOST-LEAD-PLANNER-U24  (E4 addition, owner request 2026-10-13; no deps; standard; rides on PR #522; manifest edit, owner confirms)
4. TCK-20261013-PLATFORM-DOMAIN-SEATS  (owner decision 2026-10-13, spec from PR #537; no deps; standard; manifest edit, literal diff in the ticket, owner confirms on the PR)

## Proposed re-sequence (2026-10-18, PROPOSAL, awaiting owner confirmation)

From agent-working-planner (u24) on #634, 2026-10-18; recorded on the owner's instruction, not yet decided:

1. E6, tech-stack governance (the tech_stack registry).
2. E2, fleet view, merged with session-layer M6b.
3. E3, cross-host heartbeat.
- E5 (measurement hook-in) becomes an acceptance criterion of E2 instead of its own item.
- Session-layer M7 is not due before 2026-11-04.
