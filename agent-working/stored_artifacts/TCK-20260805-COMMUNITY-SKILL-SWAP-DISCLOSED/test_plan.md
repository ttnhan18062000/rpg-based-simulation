---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED
artifact_type: test_plan
tags: [skills, workflows]
---

# Test Plan — TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED

## Normal Flow
- Both `SKILL.md` files still parse as valid frontmatter + Markdown after editing.
- `api-design-principles/SKILL.md`'s new `## In This Repo` section is present and cites the real
  test file and CLAUDE.md rule.
- `architecture/SKILL.md`'s Related Skills table names real in-repo pointers only.

## Edge Cases
- `.agents/` mirror regeneration must not silently fail or leave a partially-written file — verify
  both `.agents/skills/api-design-principles/SKILL.md` and `.agents/skills/architecture/SKILL.md`
  exist and their bodies match `.claude/`'s post-edit bodies exactly (byte comparison of the body,
  excluding the deliberately-different minimal Codex frontmatter).

## Failure Modes
- If the 3 dangling `@[skills/...]` strings are removed but accidentally leave the table
  malformed (e.g. a dangling `|` row), a Markdown-table-shape check catches it.

## Regression-Prone Paths
- `source: community` / `risk: unknown` frontmatter lines must be byte-identical before and after
  — a diff-based test, not just "field present," catches an accidental accidental rewrite that
  changes wording without changing meaning.
- Existing Codex-adapter tests (`tests/agent_orchestration_codex_adapter/`) must still pass after
  regeneration — confirms the regeneration didn't break the contract/write-guard mechanism.
