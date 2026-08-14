---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260805-COGNITION-STRATEGY-SKILL
artifact_type: plan
tags: [skills, strategy]
---

# Plan — TCK-20260805-COGNITION-STRATEGY-SKILL

## New skill: `.claude/skills/cognition-strategy/SKILL.md`
`source: project` frontmatter. Sections, in this order (boundary FIRST, per the ticket's explicit
instruction):
1. **The boundary — read this first** — the full IS/NOT list from `docs/cognition/README.md`,
   verbatim in spirit, with the cross-check against `authoritative_pipeline.md`'s Cognitive
   Refinement section noted.
2. **`SelfModelUpdatePhase`'s 4-step pipeline** — real service/file names.
3. **Goal hierarchy** — 4 tiers.
4. **Interruption resistance** — the real formula, including the "not hardcoded 30.0" caveat.
5. **Leads, Blockers, Project Lifecycle** — 6 real `BlockerKind` values, 4-level lifecycle.
6. **Perception & info decay** — real radius/tick constants, the 15.0-unit non-perception-radius
   caveat.
7. **`BoundedStrategicAppraisalService`'s 7-stage pipeline** — real scoring formulas, slice
   limits, hysteresis.
8. **The authoritative pipeline phases** — 4 real phases with real Compliance IDs/flags.

## `docs/ai/skills.md` + contract registration + `.agents/` mirror
Same mechanism as the prior domain-skill tickets.

## Tests
New `tests/tools/test_cognition_strategy_skill_content.py`:
- The boundary section is literally the first `##` section in the file (structural test, not just
  presence — per the ticket's explicit "foregrounded, not buried" requirement).
- All 4 NOT-statements present.
- Real interruption-resistance formula + the "not hardcoded 30.0" caveat present.
- All 3 real scoring formulas present verbatim.
- All 4 real pipeline phase names + flags/Compliance ID present.
- `docs/ai/skills.md` lists it; `.agents/` mirror matches.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (boundary foregrounded, not buried) → structural test asserting section order, not just
  content presence.
- AC2 (cross-references pipeline phases) → section 8, each cited to a real phase/flag/Compliance ID.
- AC3 (`docs/ai/skills.md` updated) → Document-Update step.
