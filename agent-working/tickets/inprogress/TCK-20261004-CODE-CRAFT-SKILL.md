---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-CODE-CRAFT-SKILL
phase: inprogress
date: 2026-10-04
tags: [architecture, skills]
---

# TCK-20261004-CODE-CRAFT-SKILL

## Title
M6d: `code-craft` skill and the implementer pointer

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
A `code-craft` skill carrying the standard's reviewer rules with bad/good pairs and the workflow (ratchet, edit hook, package registry exemplars, rubric), plus one pointer line in `implementer.md`.

## Scope
- `.claude/skills/code-craft/SKILL.md`: reviewer rules (F1, F2, F4, F5, N1, N4 trailing digit, D2, D3, T2, T3, E2 justification, E3 forms ast-grep misses), each with a short bad/good pair; rule ID plus one line only, the standard stays the source
- Workflow: `make code-health` or staged ratchet before commit; meaning of the edit-hook message; imitate `exemplar_modules`, never `do_not_imitate`; rubric for reviewers
- Add to `agent-working/agent-orchestration/skills.yaml`; satisfy `test_skills_catalog.py` and the Codex generator (regenerate, never hand-edit generated files)
- `.claude/agents/implementer.md`: one pointer line in "Code Quality Rules", nothing else; owner confirms the literal diff via AskUserQuestion BEFORE commit
- Tests: content test (rule IDs exist in the standard, cited paths exist), catalog test, implementer-pointer pin

## Out of Scope
- `safe-refactor` skill (M7)
- `CLAUDE.md`
- Other agent files

## Acceptance Criteria
- [ ] Skill present and catalogued; catalog test and content test pass
- [ ] Owner confirmed the implementer.md diff before commit
- [ ] Implementer pointer pinned by a test
- [ ] No generated file hand-edited
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-EXEMPLAR-MODULES
- TCK-20261004-REVIEW-RUBRIC
- TCK-20261004-EDIT-RATCHET-HOOK

## Related Docs
- docs/plans/codebase_health/python_code_craft_m6_agent_integration_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/skills/code-craft/ (owned by agent-working)
- .claude/agents/implementer.md (owned by agent-working)
- agent-working/agent-orchestration/skills.yaml
- tests/tools/

## Assumptions / Open Questions
- Owner decision 8.17 (2026-10-04): codebase implements M6 although `.claude/**` is agent-working's territory; the PR body names agent-working as owner of those paths
- Nothing here blocks a PR or tool call; M4 and M5 soaks are not disturbed

## Implementation Notes
`.claude/skills/code-craft/SKILL.md` (no counts, precise trigger: src/ or tools/ Python, not docs/YAML/test-only), catalog entry, Codex mirror generated with `render_codex_guidance` (the only change it caused beyond the new mirror was the required `code-craft` line in `AGENTS.md`; no unrelated drift), `docs/ai/skills.md` row. E3 example uses `except Exception: return None` around a parse step and says handling (`except KeyError: return default`) is not a swallow. One pointer line added to `.claude/agents/implementer.md` after the owner confirmed the literal diff (AskUserQuestion, 2026-10-04).

## Test Summary
`tests/tools/test_code_craft_skill_content.py` plus `tests/agent_orchestration` and `tests/agent_orchestration_codex_adapter`: 106 passed (with the settings wiring tests).

## Files Changed
.claude/skills/code-craft/SKILL.md (new), .claude/agents/implementer.md (agent-working's), .agents/skills/code-craft/SKILL.md (generated), AGENTS.md (generated), agent-working/agent-orchestration/skills.yaml, docs/ai/skills.md, tests/tools/test_code_craft_skill_content.py (new), ticket and staging artifacts

## Completion Summary
