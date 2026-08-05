---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-COGNITION-STRATEGY-SKILL
phase: open
date: 2026-08-05
tags: [skills, strategy]
---

# TCK-20260805-COGNITION-STRATEGY-SKILL

## Title
Author a bespoke skill for working in src/cognition/, src/strategy/, src/ai/goals/ — the highest-value domain gap found

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Domain-coverage sweep child ticket, from `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`,
flagged as the highest-value of the 6 confirmed gaps. `docs/cognition/README.md` explicitly warns
"What the cognition subsystem is NOT — Not strategy (`src/strategy/`, bounded cognition capacity
management) reads the self-model produced here but does not live here; Not domain decision..." —
a subtle, repo-specific boundary between `src/cognition/`, `src/strategy/`, and `src/ai/goals/`
that a generic community skill would get actively wrong, not just fail to help with.
`docs/strategy/bounded_cognition_decision_flow.md` (with Mermaid diagrams, cataloged in
`docs/guides/diagram_index.md`) documents the real cognitive pipeline used by
`BoundedStrategicAppraisalService`. Zero skill or agent coverage exists. Governed by
`docs/mechanics/04_strategic_cognition.md` (goal hierarchy, interruption resistance, knowledge
management, perception).

## Scope
- Author `.claude/skills/cognition-strategy/SKILL.md` (or similar — Plan decides exact naming),
  sourced from `docs/cognition/README.md`, `docs/strategy/bounded_cognition_decision_flow.md`, and
  `docs/mechanics/04_strategic_cognition.md`.
- The skill's primary value-add must be the boundary clarification itself (cognition vs. strategy
  vs. domain decision-making) — this is the specific trap a generic skill would fall into, so it
  should be foregrounded, not buried.
- Must correctly reference the authoritative pipeline's `self_model`, `information_belief`,
  `information_intent_execution`, `strategic_intelligence` phases (`docs/engine/authoritative_pipeline.md`)
  and the "Cognitive Refinement" section's interruption-resistance rule.
- Cover: goal hierarchy, interruption resistance formula, knowledge/belief assimilation, and
  perception — citing `docs/mechanics/04_strategic_cognition.md` directly.

## Out of Scope
- Building new cognition/strategy code or fixing any real bug found while authoring the skill —
  file a separate ticket if one is found.
- `src/ai/` broadly (only `src/ai/goals/` is in scope, per the sweep's own domain boundary).

## Acceptance Criteria
- [x] New skill (`.claude/skills/cognition-strategy/SKILL.md`) authored, sourced from
      `docs/cognition/README.md` + `04_strategic_cognition.md` +
      `bounded_cognition_decision_flow.md`, with the boundary as the structurally-first `##`
      section (tested by position, not just substring presence).
- [x] Correctly cross-references `self_model`/`information_belief`/
      `information_intent_execution`/`strategic_intelligence` with their real flags/Compliance ID.
- [x] `docs/ai/skills.md` updated to list the new skill.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-COMBAT-SKILL, TCK-20260805-SYSTEMS-SKILL, TCK-20260805-PROGRESSION-ENTITIES-SKILL (sibling domain-gap tickets)

## Related Docs
- `docs/cognition/README.md`
- `docs/strategy/bounded_cognition_decision_flow.md`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/engine/authoritative_pipeline.md` (self_model/information_belief/information_intent_execution/strategic_intelligence phases)
- `docs/guides/diagram_index.md` (Mermaid diagram catalog for this domain)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `src/cognition/`
- `src/strategy/`
- `src/ai/goals/`
- `.claude/skills/` (new skill target)

## Assumptions / Open Questions
Exact skill naming — Plan phase decides.

## Implementation Notes
Authored `.claude/skills/cognition-strategy/SKILL.md`, `source: project`, with "The Boundary —
Read This First" as the literal first `##` section, per the ticket's explicit instruction (tested
structurally, not just for presence). Grounded in 4 real docs: the full IS/NOT list from
`docs/cognition/README.md` (cross-checked against `authoritative_pipeline.md`'s own "Cognitive
Refinement" section, which independently confirms `intelligence.py` backs `strategic_intelligence`
— the two docs agree, this isn't asserted from one source alone); the real 4-step
`SelfModelUpdatePhase` pipeline with real service/file names; the real goal-hierarchy tiers and
interruption-resistance formula (including the "not a hardcoded 30.0" caveat — a real, easy
misconception); the 6 real `BlockerKind` values; perception radius (10.0 units) with its real
15.0-unit non-perception-radius caveat; the real `BoundedStrategicAppraisalService` 7-stage
pipeline with 3 exact scoring formulas; and all 4 real authoritative-pipeline phases with real
flags/Compliance ID.

Applied the now-established mechanism directly: registered `cognition-strategy` in
`agent-orchestration/skills.yaml`, used `layer: strategy` (already registered) for staging
artifacts, regenerated the `.agents/` Codex mirror.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_cognition_strategy_skill_content.py` — 8 tests, all passing: valid
frontmatter with `source: project`; a structural test parsing the file's `##` sections and
asserting the boundary section is literally first (not just present); all 4 real NOT-statements
present; the interruption-resistance formula + "not a hardcoded 30.0" caveat present; all 3 real
scoring formulas present verbatim; all 4 real pipeline phases + their real flags/Compliance ID
present; `docs/ai/skills.md` lists it; `.agents/` mirror body matches. Regression check:
`pytest tests/agent_orchestration_codex_adapter/` — 27 passed. `doc_staleness_check.py` → PASS.
`clean_data_runs_early()` → PASS. `expected_subsystems_for_files()` → `{}` — no parity entry
needed. `run_static_precheck('standard', ...)` — all 7 conditions PASS, first pass clean.

## Files Changed
- `.claude/skills/cognition-strategy/SKILL.md` (new) — the skill.
- `.agents/skills/cognition-strategy/SKILL.md` (new) — Codex mirror.
- `agent-orchestration/skills.yaml` — registered the new skill in the contract.
- `docs/ai/skills.md` — added to the Project-Level Skill Files table.
- `tests/tools/test_cognition_strategy_skill_content.py` (new) — 8 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Delivered the epic's own flagged highest-value skill — its entire value proposition is a
repo-specific boundary a generic community skill would get actively wrong (conflating "cognition"
with general AI decision-making), so that boundary is the first thing the skill says, verified by
a structural test rather than just a substring check. Every formula, constant, and phase citation
grounded in real docs, with one cross-doc consistency check performed explicitly rather than
trusted from a single source. No known material gap.
