---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED
phase: open
date: 2026-08-05
tags: [skills, workflows]
---

# TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED

## Title
Research popular alternatives for api-design-principles and architecture (both disclosed source: community)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child ticket #5 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. `api-design-principles` and
`architecture` both carry explicit, honest `source: community` / `risk: unknown` frontmatter
(confirmed via direct grep of all 16 `.claude/skills/*/SKILL.md` files — the only 2 with this
disclosure shape). `architecture` additionally references 3 sibling skills
(`@[skills/database-design]`, `@[skills/api-patterns]`, `@[skills/deployment-procedures]`) that do
not exist anywhere in this repo — a strong signal of unmodified, pasted-in community content, not
project-adapted. Per the user's explicit preference: prefer adopting an established, popular
skill (as-is or lightly modified) over authoring bespoke content.

## Scope
- Research whether a current, well-maintained popular alternative exists for each of the 2 skills
  (via WebSearch — never guess/fabricate a URL).
- For `architecture`: also decide whether the dangling `@[skills/...]` references should simply be
  removed/corrected regardless of the swap decision, or whether adopting a different popular
  skill naturally resolves them.
- Produce a per-skill assessment: keep as-is / swap for a specific found alternative / adapt with
  minor project-specific modification — with reasoning.
- If swapped: preserve the honest `source: community` disclosure pattern (update citation/version
  if the new source differs from the old).

## Out of Scope
- `backend-testing`, `python-performance-optimization`, `python-testing-patterns`,
  `debugging-strategies` — different disclosure status (undisclosed fingerprint), covered by
  `TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED`.
- Deciding the swap unilaterally before this ticket's own Plan/Implement phases — the epic's
  Investigate explicitly reserved this research for the child ticket itself, not pre-decided.

## Acceptance Criteria
- [x] Per-skill assessment (keep / swap / adapt) for `api-design-principles` and `architecture`,
      with reasoning — both: **adapt**. WebSearch found no verifiably real, clearly-superior
      alternative (Anthropic's own official repo has no api-design/architecture skill; a
      requesting GitHub issue is open, unmerged). No fabricated URL adopted.
- [x] `architecture`'s dangling sibling-skill references resolved — replaced with real in-repo
      pointers (`architecture-reviewer` agent, `docs/architecture/`, CLAUDE.md's Architecture Rule).
- [x] `source: community` disclosure frontmatter preserved byte-identical on both (confirmed by
      test), correct since neither skill was swapped.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED (sibling, different disclosure status, kept separate)

## Related Docs
None new.

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `.claude/skills/api-design-principles/SKILL.md`
- `.claude/skills/architecture/SKILL.md`

## Assumptions / Open Questions
Whether a suitable popular alternative actually exists for either skill is genuinely open —
resolved by this ticket's own research, not assumed.

## Implementation Notes
Real WebSearch run (3 queries, see `investigation.md`) found no verifiably real, clearly-superior
alternative for either skill — Anthropic's own `github.com/anthropics/skills` has no
`api-design`/`architecture` skill (a GitHub issue requesting one is open, unmerged). Confirmed
`api-design-principles`'s `assets/rest-api-template.py` is genuinely FastAPI-based, matching this
repo's real stack (`src/api/server.py` imports FastAPI directly) — not misleading, unlike
`backend-testing`'s confirmed Node/Express mismatch (separate ticket). Decision for both: **adapt**,
not swap.

- `api-design-principles/SKILL.md`: added `## In This Repo`, cross-referencing the real
  presenters-only API-boundary rule (`tests/architecture/test_api_read_model_guard.py`, CLAUDE.md's
  "Do not expose raw domain models from APIs").
- `architecture/SKILL.md`: replaced the 3 confirmed-dangling `@[skills/database-design]`/
  `@[skills/api-patterns]`/`@[skills/deployment-procedures]` rows with real in-repo pointers
  (`architecture-reviewer` agent, `docs/architecture/`, CLAUDE.md's Architecture Rule, and the
  adjacent `api-design-principles` skill — named in plain prose, not `@[skills/...]` bracket
  syntax, since that syntax itself was never a real resolution mechanism in this repo).

**Real finding mid-investigation**: `.agents/skills/<id>/SKILL.md` is a generated Codex-provider
mirror of `.claude/skills/<id>/SKILL.md` (`tools/agent_orchestration_codex_adapter/generator.py`,
"Do not hand-edit — regenerate instead"). Ran `render_codex_guidance(ROOT, ROOT)` after editing
both `.claude/` sources. This also caught up 4 OTHER skills' mirrors (`brainstorming`,
`create-tickets`, `implement-epic`, `implement-ticket`) that had silently drifted from earlier
tickets THIS session (the hotfix/dangling-crossref fixes to `implement-ticket/SKILL.md` and
`brainstorming/SKILL.md`) never regenerating their Codex mirror — plus `AGENTS.md` itself, which
was missing the `Document-Update` phase and `doc-updater` role from an earlier, already-landed
contract update. Disclosed here rather than silently included: this is a mechanical,
fully-deterministic side effect of using the one correct regeneration tool, not manual scope
creep — leaving those mirrors stale would itself be a data-integrity bug.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_disclosed_skill_swap_adaptation.py` — 6 tests, all passing: the new
`## In This Repo` section exists and cites the real test file; `architecture/SKILL.md` has zero
remaining dangling `@[skills/...]` references; its Related Skills table names real in-repo
pointers; both skills' `risk`/`source`/`date_added` frontmatter lines are byte-identical to before
(disclosure preserved, not silently dropped); both `.agents/` mirror bodies match their `.claude/`
source bodies exactly (confirms regeneration succeeded, not stale); `.agents/` mirror frontmatter
correctly stays minimal (no `risk`/`source` — by design, not a bug, per the Codex contract's own
schema). Regression check: `pytest tests/agent_orchestration_codex_adapter/` — 27 passed,
confirming the regeneration didn't break the contract/write-guard mechanism.
`doc_staleness_check.py` → PASS (no `src/`/`config/`/`.claude/workflows/*.js` path touched, so no
`docs/` update required). `clean_data_runs_early()` → PASS. `expected_subsystems_for_files()` →
`{}` — no parity entry needed. `run_static_precheck('standard', ...)` — all 7 conditions PASS.

## Files Changed
- `.claude/skills/api-design-principles/SKILL.md` — added `## In This Repo` section.
- `.claude/skills/architecture/SKILL.md` — replaced 3 dangling references with real pointers.
- `.agents/skills/api-design-principles/SKILL.md`, `.agents/skills/architecture/SKILL.md` —
  regenerated to match.
- `.agents/skills/brainstorming/SKILL.md`, `.agents/skills/create-tickets/SKILL.md`,
  `.agents/skills/implement-epic/SKILL.md`, `.agents/skills/implement-ticket/SKILL.md`, `AGENTS.md`
  — regenerated as a mechanical side effect of running the one shared regeneration tool (see
  Implementation Notes; these were already stale from earlier tickets, not new edits by this one).
- `tests/tools/test_disclosed_skill_swap_adaptation.py` (new) — 6 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Researched real popular alternatives via WebSearch (no fabricated URLs) and found none clearly
superior — Anthropic's own official skills repo has no equivalent for either domain. Both skills
adapted with a minor, honest, project-specific cross-reference to this repo's own real
hard-enforced rules (API presenter boundary; `architecture-reviewer` agent) rather than swapped,
and `architecture`'s 3 confirmed-dangling references were resolved regardless. Preserved the
honest `source: community`/`risk: unknown` disclosure on both, unchanged. Incidentally discovered
and fixed a real, previously-unflagged staleness class in this session's own work: the `.agents/`
Codex mirror silently drifting from `.claude/` sources after earlier tickets' edits — caught up via
the one correct regeneration tool, disclosed transparently rather than hidden. No known material
gap.
