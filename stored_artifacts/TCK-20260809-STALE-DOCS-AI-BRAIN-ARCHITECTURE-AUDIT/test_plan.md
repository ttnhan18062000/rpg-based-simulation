---
status: active
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT
phase: test
date: 2026-08-10
tags: [documentation, cognition]
---

# Test Plan — TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT

## Scope

Doc-only ticket, no `pytest` suite applies. Verification is: (1) symbol-level cross-checks against
real `src/`, (2) link-integrity sweep across `docs/`, `.claude/`, `.agents/`, (3) confirming
`search_docs` behavior post-fix.

## Normal flow

- Every one of the 8 archived files' cited `src/` symbols independently confirmed non-existent
  via direct `grep -rn`/`find`/`ls` before archival (not assumed).
- The 2 kept-in-place files (`faction_contract.md`, `strategic_cognition.md`) independently
  confirmed current: `strategic_cognition.md`'s `DirectiveState`/`ObjectiveState`/`ProjectState`
  all found real in `src/core/strategic.py`.

## Edge cases

- Frontmatter-only heuristic (`status: active` + no `last_verified` → stale) correctly flagged 7/8
  archived files but incorrectly would have flagged `strategic_cognition.md` too — caught by
  requiring direct symbol verification per file, not a shortcut on the heuristic alone.
- Initial investigation pass concluded no current replacement existed for
  `buildings_and_economy.md`/`world_generation.md`; a dedicated cross-reference sweep (grep across
  all of `docs/` for live links to the archived paths, not just symbol names) found 2 real,
  `last_verified`-dated authoritative docs (`docs/simulation/town_contract.md`,
  `docs/world/generator_contract.md`) that the narrower symbol-only sweep missed. Corrected before
  finalizing rather than shipping the incomplete conclusion.

## Failure modes / regression-prone paths

- Link-integrity sweep found 5 real live references to the archived paths that needed updating
  (not just the directory's own `README.md`): `docs/simulation/town_contract.md`,
  `docs/world/generator_contract.md`, `docs/guides/diagram_index.md`,
  `.claude/skills/systems-economy/SKILL.md`, `.agents/skills/systems-economy/SKILL.md` — all
  fixed. Historical `stored_artifacts/*/investigation.md`/`plan.md` references to the old paths
  were deliberately left untouched (frozen historical record of already-closed tickets, not
  live guidance — matches this repo's own convention of never retroactively editing closed
  ticket artifacts).

## Result

- `docs/REGISTRY.yaml` regenerated: active doc count 243→235 (exactly -8, matching the 8 archived
  files — `docs/archive/` is a load-bearing skip-directory in `tools/generate_registry.py` by
  existing design, confirmed via direct source read, not a gap introduced by this ticket).
- `make knowledge-index-update`: 4 changed files re-embedded (the 4 live docs edited), 8 deleted
  (the 8 archived files — confirms the knowledge-search index also excludes `docs/archive/`,
  matching the registry's own policy).
- Direct `search_docs` query for `"AIBrain state machine STATE_HANDLERS flee decision
  architecture"` post-fix: zero hits from the archived content (previously surfaced
  `state_machines.md` as an apparently-current result, per the ticket's own Request Summary) —
  the exact risk this ticket was filed to close is confirmed closed.
