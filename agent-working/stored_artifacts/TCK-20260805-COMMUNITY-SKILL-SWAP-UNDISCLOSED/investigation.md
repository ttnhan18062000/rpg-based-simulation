---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED
artifact_type: investigation
tags: [skills, workflows]
---

# Investigation — TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED

## Content Read (all 4, in full or to sufficient depth to assess)
- `backend-testing/SKILL.md` (845 lines) — read in full.
- `python-testing-patterns/SKILL.md` (1028 lines) — read in full.
- `python-performance-optimization/SKILL.md` (851 lines) — sampled core sections.
- `debugging-strategies/SKILL.md` (527 lines) — already confirmed generic earlier this session
  (Scientific Method / Rubber Duck Debugging, zero mention of ticks/DirtySet/observability).

## Fingerprint Confirmation
Only `backend-testing` carries the cross-platform origin fingerprint
(`metadata.platforms: Claude, ChatGPT, Gemini`, `metadata.tags`). The other 3 share the same
structural shape ("Master X... comprehensive guide", "When to Use This Skill", "Quick Start") but
without that explicit metadata block. None of the 3 (`python-testing-patterns`,
`python-performance-optimization`, `debugging-strategies`) contain dangling `../` sibling-skill
references — only `backend-testing` does (`../api-design/SKILL.md`, `../authentication/SKILL.md`).

## `backend-testing` — hypothesis CONFIRMED
Content is 100% Node.js/Express/Jest/Supertest/Prisma (`jest.config.js`, `db.user.findUnique`,
`bcrypt`-style password validation, JWT `POST /auth/register`/`POST /auth/login`). The single
nominal "Python FastAPI" example (`## Examples > Example 1`) still uses FastAPI's in-process
`TestClient` + SQLAlchemy generic CRUD — checked against this repo's real API test convention
(`tests/api/test_rest_parity.py`, `tests/api/test_live_health_api.py`, and every other file in
`tests/api/`): **all of them** use `subprocess.Popen(["python3", "-m", "src", "serve", "--port",
...])` + real HTTP calls via `requests` against `http://127.0.0.1:{port}` + `try/finally:
server.terminate()` — a live-process integration pattern, not `TestClient`'s in-process mock. The
skill's one "Python" example is generic boilerplate that would actively mislead an agent writing a
real test for this repo. This repo also has no user-auth/JWT/registration flow at all — the entire
auth-testing section (Step 4, ~100 lines) describes a domain that doesn't exist here.
Cross-referenced this repo's real architectural discipline: `src/api/presenters/*.py` (the
read-model shaping layer `tests/architecture/test_api_read_model_guard.py` enforces routes must
go through) and `src/api/read_model_cache.py`'s `ReadModelCache`/`ReadModelInvalidationPolicy`
(dirty-set-scoped cache invalidation, genuinely load-bearing and genuinely repo-specific).
**Verdict: bespoke-replace**, not swap — no generic Jest/pytest skill would ever encode
subprocess-launched live-server testing or dirty-set cache invalidation; this needs project-native
content, matching this session's standing preference for popular-over-bespoke only when a
genuinely-fitting popular alternative exists (it doesn't here — see WebSearch below).

## `python-testing-patterns` — assessment: KEEP, adapt
Genuinely Python/pytest-native (not a stack mismatch like `backend-testing`) — fixtures, mocking,
parameterization, async testing, CI config (`pytest.ini`/`pyproject.toml`) all real, applicable
pytest patterns this repo's own 1600+ tests already use in spirit. No dangling references. Real
gap: never cross-references this repo's own actual pytest conventions — the `slow`/`not slow`
marker convention and "never output bare `pytest tests/`, always scope" rule (CLAUDE.md's Testing
Rule, `test-scoper` agent). **Verdict: adapt with an `## In This Repo` cross-reference, matching
`api-design-principles`'s precedent from the sibling ticket.**

## `python-performance-optimization` — assessment: KEEP, adapt
Genuine cProfile/memory-profiler/optimization-strategy content, real and applicable. Real gap:
never mentions the real, already-existing regression-gate mechanism this repo has
(`PerfRegressionGate`, `docs/performance/perf_baseline_policy.md` §3 — established in this
session's `TCK-20260805-SKILL-GATE-CONVERSION-DECISION`) or this repo's actual hot paths (the
32-phase `AuthoritativeApplyPipeline`, `DirtySet`). **Verdict: adapt with an `## In This Repo`
cross-reference** to the real regression gate and the real tick-pipeline hot path, so a profiling
session gets pointed at the actual bottleneck-prone code, not generic advice alone.

## `debugging-strategies` — assessment: KEEP, adapt
Confirmed by this session's earlier domain-coverage sweep: generic (Scientific Method, Rubber Duck
Debugging), applicable to "any codebase," zero repo-specific grounding. `SKILL-GATE-CONVERSION-DECISION`
already decided its triggering mechanism stays advisory (out of this ticket's scope — content
only). **Verdict: adapt with an `## In This Repo` cross-reference** to `world-debugger` (the
narrower, more specific agent for world-assembly/content-resolution failures, per CLAUDE.md's own
Proactive Tool Use table) and `docs/engine/kernel.md` (the real tick-lifecycle doc), so generic
debugging methodology gets a starting point for this repo's actual deterministic-tick failure
surface.

## WebSearch — popular alternative research (real queries, no fabricated URLs)
`"site:github.com/anthropics/skills python testing OR performance OR debugging skill"` — found
only `webapp-testing` (frontend/browser e2e testing, not backend/pytest — not a real match for
either `backend-testing` or `python-testing-patterns`) and `skill-creator` (unrelated). No official
Python-testing, performance, or debugging skill exists in Anthropic's own repo. Combined with
`TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED`'s prior finding (community aggregators surface no
single, verifiable, clearly-superior source), **no swap candidate exists for any of the 4** — same
negative-research conclusion as the disclosed pair, now confirmed for the undisclosed 4 too.

## Unresolved Questions
None — all 4 assessments and the stated hypothesis are grounded in real content reads and real
cross-references, not assumed.
