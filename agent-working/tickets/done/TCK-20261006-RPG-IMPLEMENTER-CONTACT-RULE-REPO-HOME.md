---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-RPG-IMPLEMENTER-CONTACT-RULE-REPO-HOME
phase: done
date: 2026-10-06
tags: [ai, process-improvement, governance]
---

# TCK-20261006-RPG-IMPLEMENTER-CONTACT-RULE-REPO-HOME

## Title
Put the owner's "only the rpg planner contacts rpg implementers" rule in the rpg domain card, and return its memory file to a pointer

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
While closing `TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS` (PR #353), the implementer found
that the memory file `feedback_route_work_via_rpg_feature_planning.md` gained a rule after M1D shortened it to
a pointer. It is quoted from the owner on 2026-10-05: "handoff to the rpg-feature-planning, don't contact
directly to implementers". The file reads: "Even when the work is detailed, I never message rpg implementer
lanes. The planner dispatches them. Parked branches go to the planner as well."

The repo already covers **dispatch**: `registries/session_roles.yaml` gives `rpg-implementer`
`accepts_dispatch_from: [user, rpg-planner]`, and plan 9.3 says "a designer's briefs go to its domain planner,
never straight to an implementer". It does **not** cover the stronger part. The generic designer card still
allows "finding/fyi/ack to anyone", but the owner's rule forbids any message to rpg implementers, and it routes
parked branches through the planner. That part lives only in per-user memory, which breaks M1D's define-once
rule. The owner approved giving it a repo home on 2026-10-06.

## Scope
1. Replace the `## Card` text of `docs/guidelines/session_roles/domains/rpg.md` with the proposed text below.
   It tightens the existing two sentences to make room under the card budget and adds the rule as one sentence.
   - Current:
     > Domain: rpg (simulation product, Bible, parity ledger). `rpg-planner` manages the semantic-control-plane epic and the content of `registries/mechanisms.yaml`. Other domains ask it before changing RPG logic, a test's expected RPG behaviour or Bible and parity semantics.
   - Proposed:
     > Domain: rpg (simulation, Bible, parity ledger). `rpg-planner` owns the semantic-control-plane epic and `mechanisms.yaml` content; ask it before changing RPG logic, RPG test expectations or Bible/parity semantics. Only it messages rpg implementers; send briefs and parked branches to it.
   The owner confirms this literal before/after text before it lands. If the wording changes, the new text
   goes back to the owner.
2. Below `## Card` (rationale, not injected), add one line of provenance: owner rule 2026-10-05, narrows the
   designer template's "finding/fyi/ack to anyone" for the rpg domain; dispatch is already enforced by
   `accepts_dispatch_from`.
3. After merge, shorten the memory file
   `~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/memory/feedback_route_work_via_rpg_feature_planning.md`
   back to a pointer: remove the "Reinforced 2026-10-05" paragraph and point to the card. Before editing, record
   the paragraph verbatim in this ticket. Memory is not in git, so the ticket is the only copy.

## Out of Scope
- Any change to `accepts_dispatch_from`, the routes, or the generic designer/planner/implementer templates.
- Making the rule mechanical (a `role_boundary` check for designer-to-rpg-implementer messages). If it is
  wanted, it is a follow-up and M7 evidence decides it.
- Other memory files.

## Acceptance Criteria
1. The rpg card text equals the confirmed literal, and the owner's confirmation is quoted in Implementation
   Notes.
2. `compose_card` for `rpg-designer`, `rpg-planner` and `rpg-implementer` stays within `CARD_BUDGET_TOKENS`
   (400). Draft estimate with `estimate_tokens`: 398 / 393 / 388, up from 393 / 382 / 377. Record the real
   values. If any card exceeds 400, stop and report; do not raise the budget or trim another template.
3. The session-layer tests pass: `tests/tools/test_session_*.py`.
4. The memory file holds only frontmatter, the pointer, links and no rule text. Its `MEMORY.md` hook still says
   POINTER.
5. A grep of the memory directory for "contact directly to implementers" and "never message rpg implementer"
   finds nothing.

## Related Tickets
- `TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS` (finding recorded under its AC3 in test_plan.md)
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (closed by #353)

## Related Docs
- `docs/guidelines/session_roles/domains/rpg.md`
- `docs/guidelines/session_roles/functions/designer.md`
- `docs/plans/agent_infrastructure/session_layer_working_process.md` 9.3
- `docs/guides/cross_session_messages.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS/test_plan.md`

## Related Code Areas
`tools/sessions/card.py` (`compose_card`, `CARD_BUDGET_TOKENS`, `estimate_tokens`). The card is read at
runtime, so the generated `.claude/agents/session-*.md` files do not contain it and need no regeneration.
Verify this anyway with the generator's drift check.

## Assumptions / Open Questions
- **Ownership gap (finding, not in scope):** `PYTHONPATH=. python3 tools/sessions/route.py
  docs/guidelines/session_roles/domains/rpg.md` returns `status: unowned` on origin/main. The role-card templates
  (`docs/guidelines/session_roles/**`) belong to no domain's `owns`, but they are session-layer config and so
  agent-working's in practice. Adding that glob is a registry change for a separate ticket; this ticket only
  notes it.
- If #353 has not merged when this starts, branch from `origin/main` anyway. The two touch no common file.

## Implementation Notes
Drafted by agent-working-design (interim planner), 2026-10-06. Owner approved a repo home on 2026-10-06.
Owner confirmed the literal card text on 2026-10-06, answering "Can this text become the rpg domain card?"
with "Confirm as written". The confirmed text is the Scope 1 "Proposed" block, verbatim.

Implementation (agent-working-implementer, 2026-10-06): card text applied as confirmed; provenance sits under its own
`## Provenance` heading, because `_card_section` injects everything up to the next heading (a first attempt with the
line directly under `## Card` measured 448/436/431 and was corrected before commit). Contrary to the ticket's Related
Code Areas note, the generated `.claude/agents/session-rpg-*.md` files embed the card, so they were regenerated with
`generate_agents.py`.

Memory paragraph, verbatim, for Scope 3 (memory is not in git; this is the only copy). From
`feedback_route_work_via_rpg_feature_planning.md`:

> **Reinforced 2026-10-05:** "handoff to the rpg-feature-planning, don't contact directly to implementers". Even
> when the work is detailed, I never message rpg implementer lanes. The planner dispatches them. Parked branches go
> to the planner as well.

## Test Summary
- `estimate_tokens` of `compose_card`: rpg-designer 398, rpg-planner 386, rpg-implementer 382 (budget 400).
- `generate_agents.py --check`: 0 drift after regeneration.
- `tests/tools/test_session_*.py`: 354 passed.

## Files Changed
- `docs/guidelines/session_roles/domains/rpg.md`
- `.claude/agents/session-rpg-{designer,planner,implementer}.md` (regenerated)
- this ticket

## Completion Summary
Scopes 1 and 2 done; ACs 1-3 met (see Test Summary). Scope 3 and ACs 4-5 (memory file back to a pointer, grep of the memory directory) are post-merge and stay with the implementer: do them after the PR merges, then report the result to agent-working-design.
