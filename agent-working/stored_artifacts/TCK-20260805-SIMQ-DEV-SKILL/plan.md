---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-DEV-SKILL
artifact_type: plan
tags: [skills, simulation-quality]
---

# Plan — TCK-20260805-SIMQ-DEV-SKILL

## New skill: `.claude/skills/simq-dev/SKILL.md`
`source: project` frontmatter. Sections:
1. **When to use** — adding a new scorer/pillar, adding a scoring rule to an existing pillar,
   debugging why a specific pillar produced an unexpected score. Explicitly not for the audit
   workflow (link to `simq-audit`).
2. **Core data model** — `ScoreRecord`, `ScoringContext`, `PillarAccumulator` state, sourced
   verbatim-in-spirit from §4.1-4.3.
3. **Adding a new pillar** — the real 9-step protocol from §7.1, including the hard "no numeric
   literals" rule.
4. **Adding a scoring rule to an existing pillar** — §7.2's steps.
5. **Conflict detection rules** — §7.3, including the disclosed `EconomyScorer` divergence (stated
   plainly, not hidden).
6. **Debugging a wrong score** — practical steps: which real scorer test files to read/run first
   per pillar, `test_scorer_pillar_binding.py` for weight-lookup issues specifically.

## `docs/ai/skills.md` update
Add to the Project-Level Skill Files table, same format as `observability`'s entry.

## `agent-orchestration/skills.yaml` + `.agents/` mirror
Register `simq-dev` in the contract (required — confirmed by `OBSERVABILITY-SKILL`'s finding that
mirror generation only covers contract-registered skills), then regenerate.

## Tests
New `tests/tools/test_simq_dev_skill_content.py`:
- Skill exists, valid frontmatter, `source: project`.
- Contains the real 9-step "adding a new pillar" protocol markers (enum, `PILLAR_METADATA`,
  `SCORER_REGISTRY`, "no numeric literals").
- Contains the 3 core data model class names (`ScoreRecord`, `ScoringContext`,
  `PillarAccumulator`).
- Contains the disclosed `EconomyScorer`/`paid_info_transaction` divergence (not silently omitted).
- Cites `simq-audit` (cross-reference, not duplication) and does NOT contain `simq-audit`'s own
  audit-workflow-specific strings (`Recalibrate`, `grade anchors`) — a real
  no-content-duplication guard.
- Cites real test file paths that are confirmed to exist on disk.
- `docs/ai/skills.md` lists it; `.agents/` mirror body matches.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (sourced from real contract docs, dev/debug not audit/governance) → sections 2-6, each
  cited to a real §-number in `quality_scoring_contract.md`.
- AC2 (no duplication of simq-audit) → source-text guard test for `simq-audit`'s own
  audit-specific vocabulary.
- AC3 (`docs/ai/skills.md` updated) → Document-Update step.
