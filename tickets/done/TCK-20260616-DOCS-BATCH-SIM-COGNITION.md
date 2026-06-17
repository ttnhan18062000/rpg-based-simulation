---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-BATCH-SIM-COGNITION
phase: open
date: 2026-06-16
tags: [documentation, readability, phase-language-removal, simulation, cognition]
---

# TCK-20260616-DOCS-BATCH-SIM-COGNITION

## Title
Readability Batch: docs/simulation/, docs/cognition/, docs/ai/, docs/strategy/

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
Apply the approved readability rewrite rule (TCK-20260616-DOCS-READABILITY-PILOT) to the social/cognition/strategy domain contract docs.

## Scope
`docs/simulation/town_contract.md`, `docs/simulation/lab_contract.md`, `docs/simulation/social_systems_contract.md`, `docs/simulation/domains/*.md` (optimization, world_emergence, commitment, combat_engagement, time, perception, memory, cooperation, motivation, emotion, progression, information, domain_ownership_map, adventure — 13 files), `docs/cognition/README.md`, `docs/cognition/capability_and_knowledge_contract.md`, `docs/cognition/self_model_contract.md`, `docs/cognition/need_interpretation_contract.md`, `docs/ai/ticket-lifecycle.md`, `docs/ai/workflows.md`, `docs/strategy/strategic_appraisal_test_matrix.md`, `docs/strategy/bounded_cognition_contract.md`, `docs/strategy/world_capability_design.md`, `docs/strategy/bounded_cognition_initial_test_matrix.md`, `docs/strategy/bounded_cognition_decision_flow.md`.

Note: `docs/simulation/domains/campaigns_contract.md` and `docs/simulation/quest_contract.md` already done in the pilot — skip.

## Out of Scope
Everything else (separate batch tickets).

## Acceptance Criteria
- Zero numbered phase/milestone matches remain
- Genuine architecture concepts (Cognitive Pipeline stages, bounded-cognition decision-flow stages if applicable) preserved by name
- No broken incoming links

## Related Tickets
TCK-20260616-DOCS-READABILITY-EPIC (parent), TCK-20260616-DOCS-READABILITY-PILOT (style source)

## Implementation Notes
Applied the 4-rule rewrite policy from the pilot to all in-scope files. No files were historical. All edits removed bare numbered phase/milestone dev-tracking labels; named cognition pipeline stages (`SelfModelUpdatePhase`, named gate steps) were preserved. One additional hit found in `docs/simulation/domains/memory_contract.md` ("Memory is Phase 13") — fixed to "Memory runs after perception."

`docs/ai/ticket-lifecycle.md` had the highest hit density (24 hits): "Phase N — Name" workflow step headings became bare names; "Phase 28" example references replaced with ticket-ID or "example task" language. `docs/ai/workflows.md` had 6 hits all replaced via rename of example placeholder paths.

## Test Summary
Documentation only — no code changed. Verification: zero numbered phase/milestone matches in all in-scope directories after completion.

## Files Changed
**docs/cognition/:** README.md, capability_and_knowledge_contract.md, self_model_contract.md, need_interpretation_contract.md (4 files)

**docs/ai/:** ticket-lifecycle.md, workflows.md (2 files)

**docs/strategy/:** strategic_appraisal_test_matrix.md, bounded_cognition_contract.md, bounded_cognition_initial_test_matrix.md, world_capability_design.md, bounded_cognition_decision_flow.md (5 files)

**docs/simulation/domains/:** memory_contract.md (1 file — residual hit found and fixed during sweep)

## Completion Summary
All 12 files updated. Zero residual numbered phase/milestone matches in docs/simulation/, docs/cognition/, docs/ai/, docs/strategy/.
