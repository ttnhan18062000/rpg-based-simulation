---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED
artifact_type: plan
tags: [skills, workflows]
---

# Plan — TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED

## `backend-testing/SKILL.md` — full bespoke-replace
Rewrite entirely with project-native content:
- Real e2e API test pattern: `subprocess.Popen(["python3", "-m", "src", "serve", "--port", N])` +
  `requests` against `http://127.0.0.1:{port}` + `try/finally: server.terminate()`, cited from
  `tests/api/test_rest_parity.py` and `tests/api/test_live_health_api.py`.
- The read-model/presenter boundary: routes consume `src/api/presenters/*.py`, never raw
  `AuthoritativeState`/`EntityState`, enforced by `tests/architecture/test_api_read_model_guard.py`.
- `ReadModelCache`/`ReadModelInvalidationPolicy` (`src/api/read_model_cache.py`) — DirtySet-scoped
  cache invalidation ("M12 Law: Invalidation must be conservative and driven by DirtySet domain
  tracking"), a genuinely repo-specific pattern no generic skill would encode.
- No auth/JWT/registration section — this repo has none; would mislead if kept.
- Frontmatter: `source: project` (not `community`) — honest, since the content is no longer
  generic community material; `risk` field dropped (only meaningful for unvetted external content).
- Resolve both dangling `../api-design/SKILL.md` / `../authentication/SKILL.md` references by
  removing the "Related skills" section entirely (the auth-testing content it pointed to is gone).

## `python-testing-patterns/SKILL.md` — adapt
Add `## In This Repo` section: this repo's real pytest conventions — `slow`/`not slow` markers,
never bare `pytest tests/` (always scope), `test-scoper` agent as the mechanism that builds the
scoped command. No frontmatter change (no existing disclosure fields to preserve/add — this skill
never had them, and adding a new disclosure scheme for a lightly-adapted skill isn't warranted).

## `python-performance-optimization/SKILL.md` — adapt
Add `## In This Repo` section: the real regression-gate mechanism (`PerfRegressionGate`,
`docs/performance/perf_baseline_policy.md` §3) and the real hot-path pipeline (32-phase
`AuthoritativeApplyPipeline`, `DirtySet`) this repo's performance work actually targets.

## `debugging-strategies/SKILL.md` — adapt
Add `## In This Repo` section: `world-debugger` agent (narrower, for world-assembly/content-
resolution failures) and `docs/engine/kernel.md` (the real tick-lifecycle doc) as starting points
for this repo's actual deterministic-tick failure surface.

## `.agents/` mirror regeneration
All 4 `.claude/skills/*/SKILL.md` bodies change — run `render_codex_guidance(ROOT, ROOT)`
afterward, same as `COMMUNITY-SKILL-SWAP-DISCLOSED`.

## Tests
New `tests/tools/test_undisclosed_skill_swap_adaptation.py`:
- `backend-testing/SKILL.md` contains zero Node/Express/Jest-specific strings (`jest.config`,
  `Supertest`, `db.user.findUnique`); contains the real subprocess+requests pattern; contains
  `ReadModelCache`; contains no dangling `../` references; frontmatter reads `source: project`.
- The other 3 each contain their new `## In This Repo` section with the correct real citation.
- No pre-existing content was deleted from the 3 adapted skills beyond what Plan specifies (a
  line-count floor check — the section-add should only grow the file, not shrink it).
- `.agents/` mirror bodies match `.claude/` sources for all 4.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (per-skill assessment) → investigation.md's 4 per-skill sections.
- AC2 (backend-testing hypothesis confirmed/rejected with real research) → confirmed, with direct
  citations to `tests/api/*.py`'s real pattern and `src/api/read_model_cache.py`.
- AC3 (dangling references resolved) → backend-testing's 2 references removed along with the
  section that housed them (the content they pointed to, auth testing, doesn't apply here anyway).
- AC4 (disclosure frontmatter added/updated honestly) → `backend-testing` gets `source: project`;
  the other 3 get no new disclosure scheme (they never had one, and a light adaptation doesn't
  warrant inventing one now).
