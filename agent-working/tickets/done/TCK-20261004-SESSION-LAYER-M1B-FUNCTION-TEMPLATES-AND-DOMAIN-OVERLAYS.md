---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1B-FUNCTION-TEMPLATES-AND-DOMAIN-OVERLAYS
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M1B-FUNCTION-TEMPLATES-AND-DOMAIN-OVERLAYS

## Title
Session-layer M1b: function templates and domain overlays (role card source)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Write the prose that composes a role card: three function templates (designer, planner/reviewer, implementer) and three domain overlays (rpg, agent-working, testing), each within the card budget, so M2 can inject a card of at most ~400 tokens.

Child of `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M1). Hold rule met: M-1 merged (#289) and M0 recorded ADJUST (#307).

## Scope
- `docs/guidelines/session_roles/functions/{designer,planner,implementer}.md`: authority defaults (plan section 10 table), reset boundaries per function (plan section 6), handover contract, routing rule pointers.
- `docs/guidelines/session_roles/domains/{rpg,agent-working,testing}.md`: ownership, routes, domain-specific rules currently held in memory (define once: each fact lands here and the memory file becomes a pointer in M1d).
- A card-composition check (function + overlay + role entry <= ~400 tokens) as a test or validator rule.
- Frontmatter per `docs/guidelines/frontmatter_schema.md`; registered in the knowledge index.

## Out of Scope
- Manifest schema (M1a). Generated agent files (M1c). Hook injection (M2). Changing any role's actual authority (the templates restate the current practice).

## Acceptance Criteria
1. Three function and three domain files exist, valid frontmatter, indexed (`make knowledge-index-update`).
2. Every composed card (9 seats) is within budget by a measured token count, shown in the Test Summary.
3. No fact is stated in two places: each rule appears once, in a template, an overlay or the manifest, and the others point to it (define-once; checked by review against the memory list in M1d).
4. Authority text matches `session_authority.yaml` from M1a (a test compares the `needs_user` classes).
5. `docs/REGISTRY.yaml` regenerated; scoped tests green.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (parent), `TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE` (done)
- Depends on `TCK-20261004-SESSION-LAYER-M1A-MANIFEST-SCHEMA-AND-VALIDATOR`.

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 3, 4, 5, 10, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0 record; ADJUST 5, 6.1, 10)
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M1B-FUNCTION-TEMPLATES-AND-DOMAIN-OVERLAYS/` (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- `docs/guidelines/session_roles/` (new), `tests/tools/` (card budget).

## Assumptions / Open Questions
- Depends on M1a for the role entries; may be drafted in parallel and merged in the same PR.
- Token counting uses the repo's existing estimator if one exists; otherwise a documented character-based bound.

## Implementation Notes
Only each file's `## Card` section is injected. Ownership, routes, handover and authority classes are generated from the manifest and authority file, so templates restate none of them (a test fails if a template names an authority class). Measured composed-card size with the conservative estimator ceil(chars/3.5) (no tokenizer is installed), final: rpg-designer 392, rpg-planner 376, rpg-implementer 362, agent-working-designer 391, agent-working-planner 392, agent-working-implementer 382, testing-designer 356, testing-planner 331, testing-implementer 317 (budget 400; a test enforces it). The estimator over-counts prose, so real token counts are lower. Cards sit at the budget: any new card sentence needs one removed. Define-once review against the memory list is in the M1D migration map; three rules have no repo home yet (listed there as GAP).

## Test Summary
tests/tools/test_session_cards.py (25 tests): Three function templates and three domain overlays; composed card of every seat measured against the budget. Also run: the 11 other test files that scan `.claude/agents` (72 passed), and tests/docs.

## Files Changed
- `docs/guidelines/session_roles/functions/designer.md`
- `docs/guidelines/session_roles/functions/planner.md`
- `docs/guidelines/session_roles/functions/implementer.md`
- `docs/guidelines/session_roles/domains/rpg.md`
- `docs/guidelines/session_roles/domains/agent-working.md`
- `docs/guidelines/session_roles/domains/testing.md`
- `tools/sessions/card.py`
- `tests/tools/test_session_cards.py`

## Completion Summary
Done. Three function templates and three domain overlays; composed card of every seat measured against the budget.