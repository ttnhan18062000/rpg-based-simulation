---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-HOST-LEAD-PLANNER-U24
artifact_type: plan
tags: [ai, governance, process-improvement]
---

# plan — TCK-20261013-HOST-LEAD-PLANNER-U24

1. Roster: `lead-planner-u24` (domain lead, planner, main-checkout launch, `owns` override = its page, `may_write` = drafts, monitoring, REGISTRY); `lead-planner` gains a role-level `owns_not` for that page and a `card_note`.
2. `roster.py`: optional string `card_note` on a role (non-string is a `RosterError`); `card.compose_card` appends it after the domain text, before the authority line, inside the same 400-token estimate.
3. `boundary.py`: `_sibling_crossing`. A role that overrides `owns_not` or `owns` is one of several seats in its domain, so the domain-wide exemption does not apply to it. This is needed: `check_edit` otherwise exempts any path owned by the caller's own domain, and both leads are in domain `lead`, so neither would have been flagged writing the other's file, nor would u24 editing `Makefile`. Roles that override neither keep the old behaviour.
4. Host page skeleton, guide and plan rows, epic lines, regenerated `.claude/agents`, tests, issue for the ubuntu lead.
