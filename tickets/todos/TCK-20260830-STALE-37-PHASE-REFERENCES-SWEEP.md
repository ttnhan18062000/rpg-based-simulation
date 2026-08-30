---
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260830-STALE-37-PHASE-REFERENCES-SWEEP
phase: open
date: 2026-08-30
tags: [architecture]
---

# TCK-20260830-STALE-37-PHASE-REFERENCES-SWEEP

## Title
Sweep Remaining Stale "37-phase" References Across Live Docs/Skills (Now 39)

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Filed from `TCK-20260830-HOTFIX-AGENTS-MD-37-TO-39-PHASE-COUNT-DRIFT`, which fixed the one
CI-blocking instance (`AGENTS.md`/its generator). `docs/engine/authoritative_pipeline.md` is the
authoritative source of truth and correctly reads "39 phases" — several other live docs/skills
still say "37-phase", a stale figure:

- `CLAUDE.md` (line ~291, the engine-contracts table row)
- `.claude/skills/cognition-strategy/SKILL.md`
- `.claude/skills/debugging-strategies/SKILL.md`
- `.claude/skills/combat-mechanics/SKILL.md`
- `.claude/skills/python-performance-optimization/SKILL.md`
- `.claude/skills/systems-economy/SKILL.md`
- `.agents/skills/{cognition-strategy,debugging-strategies,combat-mechanics,systems-economy,python-performance-optimization}/SKILL.md`
  (the `.agents/skills/` mirror of the above — check whether these are hand-maintained or
  generated from `.claude/skills/`; if generated, fix at the source and regenerate)
- `docs/engine/README.md`
- `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`
- `docs/plans/design_enhancement/design_enhancement_roadmap.md`

None of these are covered by a test assertion (confirmed via
`grep -rln "37-phase\|37 phase" tests/` returning nothing after the CI-blocking fix), so this is
pure doc-staleness cleanup, not a hard error — deliberately deferred out of the CI-unblocking
hotfix.

## Scope
- Update each live doc/skill listed above from "37-phase"/"37 phases" to "39-phase"/"39 phases".
- Do NOT touch `tickets/done/`, `stored_artifacts/`, or any other archived/historical file that
  references "37-phase" as a historical record of what was true at the time (e.g. closed tickets
  documenting the 17→37 transition) — those are correct as archival record, not live prose.
- If `.agents/skills/*/SKILL.md` files are generated from `.claude/skills/*/SKILL.md`, fix the
  source and regenerate rather than hand-editing both independently.

## Out of Scope
- Any other phase-count-adjacent claim beyond the literal "37-phase"/"37 phases" string
  (e.g. don't audit phase *names* or *ordering* — just the count).

## Acceptance Criteria
- `grep -rln "37-phase\|37 phase" CLAUDE.md .claude/skills/ .agents/skills/ docs/engine/ docs/plans/design_enhancement/`
  returns nothing.
- No archived/historical file is modified.

## Related Tickets
- TCK-20260830-HOTFIX-AGENTS-MD-37-TO-39-PHASE-COUNT-DRIFT (fixed the CI-blocking instance)
- TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT (precedent for this exact drift class)

## Related Docs
See Scope section for the full file list.

## Assumptions / Open Questions
Whether `.agents/skills/*/SKILL.md` is generated or hand-maintained — to be confirmed during
implementation.

## Implementation Notes
(Not yet implemented — filed and deferred.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
