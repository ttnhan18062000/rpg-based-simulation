---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-SKILL-GATE-CONVERSION-DECISION
artifact_type: investigation
tags: [skills, workflows]
---

# Investigation — TCK-20260805-SKILL-GATE-CONVERSION-DECISION

## Context Search
`mcp__knowledge-search__search_docs` and direct reads confirmed the existing gate precedent
(`WORKFLOW-SECURITY-GATE`, `implement-ticket.js:1228-1279`), the mapping mechanism
(`SKILL-MAPPING-DEDUP`'s `tools/tag_registry.py::get_skill_mapping()`), and the advisory-only
finding (`WORKFLOW-TAG-TUNING-INVESTIGATION`).

## Per-Skill Investigation

### `api-design-principles`
- The one genuinely hard-checkable rule in this domain — API routes must not import
  `AuthoritativeState`/`EntityState` outside `TYPE_CHECKING`, must consume presenters only — is
  **already enforced independently and unconditionally** by
  `tests/architecture/test_api_read_model_guard.py` (an AST-based pytest architecture test, not
  skill-triggered). This runs on every CI pass regardless of whether the skill ever fires.
- The rest of the skill's content (REST conventions, pagination, versioning, error-handling
  style) is soft judgment with no deterministic pass/fail shape.
- `src/api/server.py` currently has near-zero real development activity (0 code tickets touching
  it since 2026-07-05, per this session's earlier backend domain sweep) — low current marginal
  value for any new enforcement mechanism here.
- **Verdict: leave as advisory, do not gate.** The one part that's genuinely checkable is already
  hard-enforced independent of this skill; the rest has no verdict shape a gate could check.

### `debugging-strategies`
- "Did you debug well" has no deterministic pass/fail shape — the skill's own content (Scientific
  Method, Rubber Duck Debugging) describes a *process*, not a *checkable deliverable*.
- Debugging happens implicitly inside nearly every ticket's Investigate phase already — gating it
  would either (a) always pass trivially (no real signal) or (b) become an arbitrary blocker
  disconnected from any real defect.
- **Verdict: leave as advisory, do not gate.** No other fix needed here — the skill's content
  quality (confirmed generic/non-repo-specific earlier this session) is
  `COMMUNITY-SKILL-SWAP-UNDISCLOSED`'s separate scope, not this ticket's.

### `python-performance-optimization`
- **Unlike the other two, a real deterministic verdict shape DOES exist**: `PerfRegressionGate`
  (`src/perf/regression_gate.py`, tested by `tests/unit/perf/test_perf_regression_gate.py`),
  checking p50/p95 tick-latency and memory-stability thresholds against baselines
  (`docs/performance/perf_baseline_policy.md` §3, `docs/testing/regression_policy.md` §8).
- Checked whether this gate is wired into `implement-ticket.js` as a dedicated phase (mirroring
  `Security-Review`) — it is not. Checked whether it's already covered by the **existing** Test
  phase (step 9, `test-scoper` agent) — `tests/unit/perf` is included in CI's own
  `perf-cert-arena` job (`.github/workflows/test.yml:163-176`), so the mechanism already exists
  at the CI level. Whether a given *ticket's own* scoped Test-phase run includes it depends on
  `test-scoper.md`'s file-path-only mapping rule (`src/module/` → `tests/unit/module/`).
- **Real gap found**: `test-scoper.md`'s mapping is purely file-path-driven. A
  performance-motivated change frequently touches files outside `src/perf/` itself (e.g. a
  hot-path optimization in `src/engine/` or `src/world/`) — the naming-convention rule alone would
  not reliably include `tests/unit/perf/`/`tests/perf/` in that ticket's scoped Test-phase run,
  even though the ticket's whole purpose is a performance change the regression gate exists to
  catch.
- **Verdict: do NOT add a new Performance-Review phase mirroring Security-Review** — that would
  duplicate the existing Test-phase gate, which already has the correct mechanism
  (`tests/unit/perf`) available; adding a parallel phase for the same check would be an
  unnecessary duplicate abstraction. **Instead, "some other fix"**: strengthen the existing
  Test-phase gate so it reliably includes the real regression check for performance-tagged
  tickets, by passing `ticketInfo.tags`'s `performance` membership into the test-scoper prompt
  (mirroring `Security-Review`'s own precedent of reading `ticketInfo.tags` directly as ground
  truth) and adding an explicit rule to `test-scoper.md`.

## Asymmetry Explicitly Addressed
The ticket's own central open question — "does `security`'s successful conversion mean all 3
should convert too" — resolves to **no, for different reasons per skill**:
`api-design-principles` and `debugging-strategies` have no checkable verdict shape at all (unlike
`security`'s deterministic injection/auth/secrets checklist); `python-performance-optimization`
does have one, but it was already covered by an existing mechanism once that mechanism's real gap
(test-scoper's file-path-only mapping) was found and closed — so even the one skill with a real
verdict shape did not need a *new* gate, just a fix to make the *existing* one reliable.

## Unresolved Questions
None — the coordination-check AC bullet (re: `FRONTEND-DESIGN-TRIGGER-REOPEN`) is satisfied since
this ticket does not touch CLAUDE.md's "Proactive Tool Use" table at all (no row reinstated or
removed) — no coordination conflict exists.
