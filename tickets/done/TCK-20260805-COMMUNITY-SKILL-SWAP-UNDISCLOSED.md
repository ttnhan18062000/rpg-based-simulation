---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED
phase: done
date: 2026-08-05
tags: [skills, workflows]
---

# TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED

## Title
Research popular alternatives for backend-testing, python-performance-optimization, python-testing-patterns, debugging-strategies (undisclosed community fingerprint)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child ticket #6 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. 4 skills share an identical
structural fingerprint ("Master X... comprehensive guide", "When to Use This Skill" bullet list,
"Quick Start" code block) matching the 2 disclosed-community skills' shape, but without their
`source: community` frontmatter. `backend-testing` additionally declares
`metadata.platforms: Claude, ChatGPT, Gemini`, confirming cross-platform, non-Claude-specific
origin. `backend-testing` in particular was found actively misleading, not just generic — its
content is 100% Node.js/Express/Jest/Prisma/JWT-auth-registration-flow (`POST /auth/register`,
`db.user.findUnique`, bcrypt-style validation), with one nominal "Python FastAPI" example still
generic SQLAlchemy user-auth CRUD boilerplate unrelated to this repo's actual pattern (a
deterministic-tick simulation engine's read-model/presenter API boundary, enforced by
`tests/architecture/test_api_read_model_guard.py`). Also references 2 dangling sibling skills
(`../authentication/SKILL.md`, `../api-design/SKILL.md`) that don't exist here.

## Scope
- Research whether current, well-maintained popular alternatives exist for each of the 4 skills.
- For `backend-testing` specifically: given the finding that this repo's actual testing convention
  (subprocess+`requests` against a live server, per `tests/api/test_rest_parity.py` — notably NOT
  FastAPI's `TestClient` pattern the skill's own example assumes) and its real architectural
  discipline (the read-model/presenter boundary, `ReadModelCache`'s dirty-set invalidation
  pattern) are genuinely repo-specific, the likely correct outcome is NOT swapping for a different
  popular Jest-family skill, but replacing the content with project-specific material covering
  those real patterns. Confirm or reject this hypothesis with real research rather than assuming
  it.
- Assessment must be per-skill, not blanket, even though kept as one ticket (all 4 share the same
  remediation shape and disclosure finding — splitting further would not change the work).
- Resolve dangling sibling-skill references (`../authentication/`, `../api-design/`) regardless of
  swap decision.
- If a swap or bespoke-replace is adopted: add honest `source: community` (or `source: project`)
  disclosure frontmatter matching the established pattern.

## Out of Scope
- `api-design-principles`, `architecture` — different disclosure status, covered by
  `TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED`.
- `test-driven-development` — a distinct, "moderate candidate" community family (per Investigate's
  classification, different tone/structure) already scored "correctly redundant, deliberately
  diverging" by `TCK-20260705-SIX-SKILLS-INVESTIGATION` (this repo's own pipeline runs Implement
  before Test, opposite of TDD's Iron Law) — a content-quality swap would not change that usage
  verdict, so it stays out of scope here.
- The `debugging-strategies` gate-conversion question — that's `SKILL-GATE-CONVERSION-DECISION`'s
  scope; this ticket only addresses its content quality, not its triggering mechanism.

## Acceptance Criteria
- [x] Per-skill assessment for all 4 skills — `backend-testing`: bespoke-replace;
      `python-testing-patterns`, `python-performance-optimization`, `debugging-strategies`: keep +
      adapt. See `investigation.md`.
- [x] `backend-testing`'s hypothesis confirmed with real research: cross-checked against every
      real file in `tests/api/` (subprocess+`requests`, not `TestClient`), `src/api/presenters/`,
      and `src/api/read_model_cache.py`'s real DirtySet invalidation pattern.
- [x] Dangling sibling-skill references resolved — removed along with the auth-testing section
      they were attached to (this repo has no user-auth flow for that section to describe).
- [x] Disclosure frontmatter: `backend-testing` gets `source: project` (honest — no longer generic
      community content); the other 3 get no new disclosure scheme (never had one, light
      adaptation doesn't warrant inventing one).

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED (sibling, different disclosure status, kept separate)
- TCK-20260805-SKILL-GATE-CONVERSION-DECISION (separate question — triggering mechanism, not content)

## Related Docs
None new.

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `.claude/skills/backend-testing/SKILL.md`
- `.claude/skills/python-performance-optimization/SKILL.md`
- `.claude/skills/python-testing-patterns/SKILL.md`
- `.claude/skills/debugging-strategies/SKILL.md`
- `tests/architecture/test_api_read_model_guard.py` (reference for backend-testing's real repo-specific content, if bespoke-replaced)
- `tests/api/test_rest_parity.py` (reference for this repo's actual e2e testing convention)

## Assumptions / Open Questions
Whether a suitable popular alternative exists for each of the 4 is genuinely open, except
`backend-testing` where a specific hypothesis (bespoke-replace, not swap) is stated but must still
be confirmed by real research, not assumed.

## Implementation Notes
`backend-testing/SKILL.md` fully rewritten with project-native content: the real
subprocess+`requests` live-server API test pattern (cited from `tests/api/test_rest_parity.py`,
`test_live_health_api.py`), the presenter/read-model boundary
(`tests/architecture/test_api_read_model_guard.py`), and `ReadModelCache`'s DirtySet-scoped
invalidation (`src/api/read_model_cache.py`). Removed the entire auth/JWT section — this repo has
no user-auth flow. `source: project` frontmatter added (not `community` — genuinely bespoke now).

The other 3 skills each got a minimal, additive `## In This Repo` section: `python-testing-patterns`
→ the real `slow`/`not slow` marker convention + `test-scoper`; `python-performance-optimization`
→ the real `PerfRegressionGate`/`perf_baseline_policy.md` mechanism + DirtySet hot path;
`debugging-strategies` → the `world-debugger` agent (narrower, for world-assembly failures) +
`docs/engine/kernel.md`. No pre-existing content removed from any of the 3 (line-count floor
tested).

WebSearch (per Scope) found no real, verifiable, clearly-superior alternative for any of the 4 —
`anthropics/skills` has only `webapp-testing` (frontend/browser e2e, not a match for either
backend or Python-testing content). Same negative-research conclusion as
`COMMUNITY-SKILL-SWAP-DISCLOSED`.

`.agents/` Codex mirror regenerated for all 4 (`render_codex_guidance(ROOT, ROOT)`) — same
mechanism established in the sibling ticket.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_undisclosed_skill_swap_adaptation.py` — 9 tests, all passing: zero
Node/Express/Jest fingerprint strings remain in `backend-testing`; zero dangling `../` references;
real repo-pattern citations present; `source: project` frontmatter confirmed; the 3 adapted
skills each contain their new `## In This Repo` section with correct real citations; content only
grew (never shrank) for the 3 adapted skills; all 4 `.agents/` mirror bodies match their `.claude/`
sources exactly. Regression check: `pytest tests/agent_orchestration_codex_adapter/` — 27 passed.
`doc_staleness_check.py` → PASS (no `src/`/`config/`/`.claude/workflows/*.js` touched).
`clean_data_runs_early()` → PASS. `expected_subsystems_for_files()` → `{}` — no parity entry
needed. `run_static_precheck('standard', ...)` — all 7 conditions PASS.

## Files Changed
- `.claude/skills/backend-testing/SKILL.md` — fully rewritten (project-native content).
- `.claude/skills/python-testing-patterns/SKILL.md`,
  `.claude/skills/python-performance-optimization/SKILL.md`,
  `.claude/skills/debugging-strategies/SKILL.md` — each gained an additive `## In This Repo` section.
- `.agents/skills/{backend-testing,python-testing-patterns,python-performance-optimization,debugging-strategies}/SKILL.md`
  — regenerated to match.
- `tests/tools/test_undisclosed_skill_swap_adaptation.py` (new) — 9 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Confirmed the ticket's own stated hypothesis for `backend-testing` (bespoke-replace, not swap)
with real research against this repo's actual test/architecture files, and fully rewrote it with
genuinely project-specific content, removing an actively-misleading auth-testing section this repo
doesn't need. The other 3 skills were assessed individually (not blanket) and found genuinely
applicable but ungrounded in this repo's real mechanisms — each got a minimal, additive
cross-reference rather than a rewrite, matching `COMMUNITY-SKILL-SWAP-DISCLOSED`'s established
"adapt when content is real but ungrounded" pattern. No swap adopted anywhere in this batch — real
WebSearch confirmed no verifiable, superior alternative exists for any of the 4. No known material
gap.
