---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-CODE-CRAFT-SKILL
artifact_type: test_plan
tags: [architecture, skills]
---

# Test plan — TCK-20261004-CODE-CRAFT-SKILL

- `tests/tools/test_code_craft_skill_content.py`: frontmatter (`name: code-craft`, `source: project`); cited rule IDs all exist in the standard and the reviewer set (F1, F2, F4, F5, N1, N4, D2, D3, T2, T3, E2, E3) is present; cited repo paths exist; names `package_registry.jsonl`, `exemplar_modules`, `do_not_imitate`, Section 11, `make code-health`, edit hook; `.agents` mirror equals `build_codex_skill_md` output; implementer pointer sentence appears once under "Code Quality Rules".
- `tests/agent_orchestration/test_skills_catalog.py` and `tests/agent_orchestration_codex_adapter/` unchanged and green.
- Frontmatter validation on the ticket and staging artifacts; `make knowledge-index-update` after the docs change.
