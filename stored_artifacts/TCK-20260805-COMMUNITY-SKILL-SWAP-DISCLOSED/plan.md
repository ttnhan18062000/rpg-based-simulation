---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED
artifact_type: plan
tags: [skills, workflows]
---

# Plan — TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED

## `api-design-principles/SKILL.md`
Add a new `## In This Repo` section (after `## Instructions`, before `## Resources`) naming the
real, hard-enforced boundary rule this skill's generic REST/GraphQL guidance must not override:
routes consume `src/api/presenters/*.py` only, never raw `AuthoritativeState`/`EntityState`
(enforced by `tests/architecture/test_api_read_model_guard.py`, CLAUDE.md's "Do not expose raw
domain models from APIs"). No other content changes — the rest of the skill (including
`assets/rest-api-template.py`) is confirmed stack-correct (real FastAPI, matches
`src/api/server.py`) and not misleading.

## `architecture/SKILL.md`
Replace the `## 🔗 Related Skills` table's 3 dangling `@[skills/...]` rows with real in-repo
pointers: `architecture-reviewer` agent (the actual gated mechanism already doing plan/diff
architecture review in this repo), `docs/architecture/` (real ADR docs, the same location
`brainstorming`'s spec-writing flow already targets), and CLAUDE.md's own "Architecture Rule"
section (durable-state/API-boundary/strategic-tactical/uncertainty rules). No other content
changes — the rest (Selective Reading Rule, trade-off analysis, pattern selection) is coherent
generic ADR-writing guidance, complementary to (not duplicative of) `architecture-reviewer`'s
gate-enforcement role.

## `.agents/` mirror regeneration
Both `.claude/skills/api-design-principles/SKILL.md` and `.claude/skills/architecture/SKILL.md`
bodies change — per the generator's own "Do not hand-edit — regenerate instead" convention
(`build_agents_md`), run `render_codex_guidance()` afterward so `.agents/skills/api-design-principles/SKILL.md`
and `.agents/skills/architecture/SKILL.md` stay in sync, exactly mirroring how the tests in
`tests/agent_orchestration_codex_adapter/` invoke it.

## `source: community` disclosure frontmatter
Preserved as-is on both — the source genuinely is community-originated content, still true after a
minor adaptation (only a "swap for a different source" would require changing this field; neither
skill is being swapped).

## Tests
New `tests/tools/test_disclosed_skill_swap_adaptation.py`:
- `api-design-principles/SKILL.md` contains the new `## In This Repo` section, citing
  `test_api_read_model_guard.py` by name.
- `architecture/SKILL.md` no longer contains any of the 3 dangling `@[skills/...]` strings.
- `architecture/SKILL.md`'s Related Skills table now names `architecture-reviewer` and
  `docs/architecture/`.
- Both skills' `source: community` / `risk: unknown` frontmatter is unchanged (byte-for-byte on
  those 2 lines) — confirming the disclosure was preserved, not silently dropped during editing.
- `.agents/skills/api-design-principles/SKILL.md` and `.agents/skills/architecture/SKILL.md`
  bodies match `.claude/`'s post-edit bodies (mirror regenerated correctly, not stale).

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (per-skill assessment with reasoning, real cited source if swapped) → `investigation.md`'s
  WebSearch section (no fabricated URL adopted; genuine search run and its negative result
  honestly reported) + Content Quality Assessment section.
- AC2 (architecture's dangling references resolved) → replaced with real in-repo pointers.
- AC3 (disclosure frontmatter preserved/updated honestly) → unchanged on both, confirmed by test.
