---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED
artifact_type: investigation
tags: [skills, workflows]
---

# Investigation — TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED

## Content Read
Read both skills in full, including all companion files:
- `api-design-principles/`: `SKILL.md`, `resources/implementation-playbook.md` (513 lines),
  `references/graphql-schema-design.md` (583 lines), `references/rest-best-practices.md`
  (408 lines), `assets/api-design-checklist.md` (155 lines), `assets/rest-api-template.py`
  (182 lines).
- `architecture/`: `SKILL.md`, `pattern-selection.md`, `examples.md`,
  `patterns-reference.md`, `trade-off-analysis.md`, `context-discovery.md`.

## Real Finding: a Codex mirror exists (`.agents/skills/`)
Discovered mid-investigation, not previously flagged in this session: `.agents/skills/<id>/` is a
generated Codex-provider mirror of `.claude/skills/<id>/`, built by
`tools/agent_orchestration_codex_adapter/generator.py::render_codex_guidance()` (confirmed via
`search_docs` → `TCK-20260727-CODEX-SKILL-COMPANION-ASSETS`, `TCK-20260721-AGENTS-DIR-DISPOSITION`).
The mirror's frontmatter is deliberately minimal (`name`/`description` only, sourced from the
`agent-orchestration/` contract, not `risk`/`source`/`date_added` — Codex's schema has no
equivalent fields, this is by design, not staleness). The **body**, however, is supposed to be
byte-identical to `.claude/`'s body (`build_codex_skill_md`'s `_body(source.read_text())`). Any
body edit made here must be followed by regenerating `.agents/skills/<id>/SKILL.md` via
`render_codex_guidance()`, or the two surfaces silently diverge — "Do not hand-edit — regenerate
instead" per `build_agents_md()`'s own header comment.

## WebSearch — popular alternative research (real queries run, no fabricated URLs)
1. `"Claude Code skill anthropic-plugins "api-design" OR "architecture" SKILL.md github community skill"`
2. `"site:github.com/anthropics/skills api design OR architecture OR system-design"`
3. `""awesome-claude-skills" OR "claude-plugins-official" api-design skill SKILL.md"`

**Findings:**
- `github.com/anthropics/skills` (the official Anthropic repo — confirmed by this repo's own
  `frontend-design` skill matching it, per this session's earlier `COMMUNITY-SKILL-SWAP-DISCLOSED`
  precedent research pattern) does **not** ship an `api-design` or `architecture` skill.
  `anthropics/skills` issue #626 ("System Architecture Skill for Claude Code and Cursor") is an
  **open, unmerged request** — not a real, adoptable skill.
- Community aggregators (`awesome-claude-skills`, `claude-plugins-official`) surfaced only
  general-purpose directory/marketplace pages, not one specific, verifiable, well-maintained
  single-skill source clearly superior to what's already here. Per this session's own standing
  rule (never adopt a skill without confirming its real content first), no swap candidate could be
  confirmed — adopting an unverified aggregator link would violate that rule, not satisfy it.

## Content Quality Assessment (why "adapt", not "swap" or "leave untouched")
- `api-design-principles`'s `assets/rest-api-template.py` is genuinely **FastAPI-based** — checked
  against this repo's real stack (`src/api/server.py` imports `from fastapi import FastAPI,
  Request, Depends`, confirmed via grep) — **stack-correct**, unlike `backend-testing`'s confirmed
  100% Node/Express/Jest/Prisma mismatch (a different ticket's finding, different disclosure
  category). The rest of the content (REST/GraphQL principles, pagination, versioning, error
  handling) is coherent, well-structured generic guidance, not misleading.
- **Real gap**: neither skill cross-references this repo's own actual, hard-enforced boundary
  rules — `api-design-principles` never mentions the presenters-only API-boundary rule
  (`tests/architecture/test_api_read_model_guard.py`, CLAUDE.md's "Do not expose raw domain models
  from APIs" Hard Rule); `architecture` never mentions `architecture-reviewer` (the real, gated
  agent already doing much of this skill's job today) or `docs/architecture/`'s real ADR
  convention (used by the `brainstorming` skill's `docs/architecture/YYYY-MM-DD-<topic>-design.md`
  flow). Generic guidance applied without this cross-reference risks an agent following the
  skill's soft REST conventions into a pattern this repo's own hard rule forbids (e.g. returning a
  raw domain object because the generic playbook doesn't say not to).
- `architecture`'s 3 dangling `@[skills/database-design]`/`@[skills/api-patterns]`/
  `@[skills/deployment-procedures]` references are unmistakably unadapted paste-in — confirmed
  none of the 3 exist anywhere in `.claude/skills/` or `.agents/skills/`.

## Decision
**Both skills: adapt with minor project-specific modification.** Not "swap" (no verifiably real,
clearly-superior alternative found — see WebSearch findings above). Not "leave as-is" (both have a
real, fixable gap: missing cross-reference to this repo's own hard-enforced rules;
`architecture` additionally has 3 confirmed-dangling references that must be resolved regardless
of the swap/keep/adapt decision, per this ticket's own Scope).
