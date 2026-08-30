---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260830-STALE-37-PHASE-REFERENCES-SWEEP
phase: done
date: 2026-08-30
tags: [architecture]
---

# TCK-20260830-STALE-37-PHASE-REFERENCES-SWEEP

## Title
Sweep Remaining Stale "37-phase" References Across Live Docs/Skills (Now 39)

## Status
DONE

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
Ran `grep -n "37-phase\|37 phase"` against the 9 files named in Scope, confirmed exact matches,
then replaced "37-phase"→"39-phase" and "37 phase"→"39 phase" (literal substring only, no other
edits) in `CLAUDE.md` and the 4 remaining `.claude/skills/*/SKILL.md` files plus the 2
`docs/plans/design_enhancement/*` files and `docs/engine/README.md`.

Confirmed `.agents/skills/*/SKILL.md` is generated, not hand-maintained: found
`tools/agent_orchestration_codex_adapter/generator.py::build_codex_skill_md`, which copies the
instructional body verbatim from the matching `.claude/skills/{id}/SKILL.md` source (via
`_body()`) and only prepends its own `name`/`description` frontmatter. Regenerated via
`render_codex_guidance(ROOT, ROOT)` (same function `tests/agent_orchestration_codex_adapter/`
exercises). That call regenerates every skill in the contract, not only the 5 in scope — it
surfaced 2 pre-existing, unrelated drifted mirrors (`implement-epic`, `implement-ticket`, whose
`.claude/` sources had been updated by other work without a corresponding regen). Those 2 were
reverted with `git checkout --` before commit — out of scope for this ticket, left for whoever
owns that drift to fix separately. `AGENTS.md` regenerated identically to its committed content
(zero diff), confirming the earlier sibling hotfix's fix is undisturbed.

## Test Summary
No test asserts this string (ticket's own pre-verified `grep -rln "37-phase\|37 phase" tests/`
returns nothing) — pure doc/skill text, no `src/` or `tools/` file touched, no behavior change.
Ran `pytest tests/agent_orchestration_codex_adapter/ -m "not slow"` (the test suite covering the
`.agents/skills/` generator this ticket exercised) to confirm the regeneration didn't break
generator contracts: all passed. Also re-ran the acceptance-criteria grep after all edits — empty
result, confirming the sweep is complete.

## Files Changed
- `CLAUDE.md`
- `docs/engine/README.md`
- `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`
- `docs/plans/design_enhancement/design_enhancement_roadmap.md`
- `.claude/skills/cognition-strategy/SKILL.md`
- `.claude/skills/debugging-strategies/SKILL.md`
- `.claude/skills/combat-mechanics/SKILL.md`
- `.claude/skills/python-performance-optimization/SKILL.md`
- `.claude/skills/systems-economy/SKILL.md`
- `.agents/skills/cognition-strategy/SKILL.md` (regenerated)
- `.agents/skills/debugging-strategies/SKILL.md` (regenerated)
- `.agents/skills/combat-mechanics/SKILL.md` (regenerated)
- `.agents/skills/python-performance-optimization/SKILL.md` (regenerated)
- `.agents/skills/systems-economy/SKILL.md` (regenerated)

## Completion Summary
Swept every live doc/skill named in Scope from "37-phase"/"37 phase" to "39-phase"/"39 phase",
matching `docs/engine/authoritative_pipeline.md`'s authoritative "39 phases" figure. Confirmed
`.agents/skills/` is generator-produced from `.claude/skills/` and used the real generator to
regenerate the 5 affected mirrors (reverting 2 unrelated pre-existing drifted mirrors the same
regen call incidentally touched). No archived/historical file (`tickets/done/`, `stored_artifacts/`,
`docs/audits/`, older ticket copies) was modified — verified via a repo-wide grep after the fix.
No behavior change; no `src/` file touched; parity ledger and tests unaffected.
