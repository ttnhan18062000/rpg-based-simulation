---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER
phase: done
date: 2026-08-19
tags: [observability, determinism]
---

# TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER

## Title
Fix bare `import random` in observability backoff-jitter code, violating the repo-wide RNG boundary law (INFRA-118)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on PR #23 (`codebase-resilience-p1-p2-batch`), 2 jobs:
- `Integration`: `tests/integration/kernel/test_phase2_determinism.py::TestRNGBoundaryEnforcement::test_rng_module_is_only_random_user` — "Law: Only `src/platform/rng.py` may use `import random`."
- `Unit · core / world`: `tests/unit/platform/test_rng_hygiene.py::test_rng_hygiene_no_global_random_in_src` — same law, separate implementation (regex-based, with an explicit non-gameplay exception list vs. the other test's AST-based whole-`src/` scan with only `rng.py` excluded).

Both flag the same 2 files: `src/observability/stream/consumer.py:4` and
`src/observability/alerts/sinks.py:2`, both `import random` at module level, added by
`TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` and `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC`
respectively (both already closed/merged-to-branch before this was caught — neither ticket's
scoped Test-phase pytest command included `tests/integration/kernel/` or `tests/unit/platform/`,
and neither Review/Architecture-Verify pass checked this specific repo-wide RNG-boundary rule).

**Root cause, not just symptom:** both files' `_compute_backoff_delay(attempt, rng=None)` methods
use the pattern `r = rng or random; return ... r.uniform(...)` — i.e. the *module itself* (which
exposes `random.uniform` etc. as module-level functions matching `random.Random`'s instance API)
is the production-path fallback default whenever no `rng` is explicitly injected. Tests always
inject an explicit seeded `random.Random(seed)`, so the fallback path is never exercised by
existing tests, but the module-level `import random` needed to reach that fallback is what both
guard tests correctly flag.

**Why this is not a gameplay-determinism bug:** this randomness is retry-backoff jitter for
network operations (Redis reconnect delay, webhook HTTP retry delay) — it never touches
simulation state, entity behavior, or replay-critical computation. It does not need to be
seed-reproducible; it exists purely to avoid thundering-herd retry synchronization. `DeterministicRNG`
(`src/platform/rng.py`) is the wrong tool here regardless of the import-boundary question — its
API is tightly coupled to gameplay semantics (`Domain` enum, simulation `tick`, `entity_id`
composite seeding), and fabricating meaningless `Domain`/`tick`/`entity_id` arguments for a plain
network-retry delay would be a semantic misuse, not a fix.

**Fix (not a rule exception, a real refactor):** route both files' RNG-instance construction
through `src/platform/rng.py` — the one file the law already designates as the sole legitimate
`import random` site — via a new small factory function, rather than adding either file to a
test's exception list. This satisfies the letter and the spirit of both guard tests with zero
edits to either test, and has a side benefit: constructing a fresh `random.Random()` per fallback
call (instead of sharing the `random` module's single global instance) removes a latent
shared-mutable-state concern in `WebhookAlertSink`, which dispatches via a `ThreadPoolExecutor`.

## Scope
- `src/platform/rng.py`: add `new_random_source() -> random.Random`, a documented factory for
  non-deterministic, non-replay-critical `Random` instances (explicitly distinct from
  `DeterministicRNG`, which remains the only sanctioned source of seed-reproducible gameplay RNG).
- `src/observability/stream/consumer.py`: remove `import random`; import
  `new_random_source` from `src.platform.rng`; change the `_compute_backoff_delay` fallback from
  `rng or random` to `rng or new_random_source()`.
- `src/observability/alerts/sinks.py`: same change.
- No test file changes expected — both `tests/unit/observability/test_stream_consumer_resilience.py`
  and `tests/unit/observability/test_webhook_alert_sink.py` already always pass an explicit
  `rng=random.Random(seed)`, never exercising the fallback branch being changed.

## Out of Scope
- `DeterministicRNG` itself — untouched, remains the sole gameplay/replay-critical RNG.
- Either determinism guard test (`test_rng_hygiene.py`, `test_phase2_determinism.py`) — untouched;
  this ticket makes the source code comply with the existing law rather than relaxing the law.
- Any other file using `import random` — out of scope; this ticket is scoped to the 2 files this
  specific CI failure flagged.

## Acceptance Criteria
- [x] `tests/integration/kernel/test_phase2_determinism.py::TestRNGBoundaryEnforcement::test_rng_module_is_only_random_user` passes.
- [x] `tests/unit/platform/test_rng_hygiene.py::test_rng_hygiene_no_global_random_in_src` passes.
- [x] Full `tests/unit/observability/` and `tests/integration/observability/` regression suite
      (the two files' own direct test coverage) still passes unmodified.
- [x] `src/observability/stream/consumer.py` and `src/observability/alerts/sinks.py` no longer
      contain `import random` anywhere in the file.

## Related Tickets
- TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC (introduced `consumer.py`'s violation)
- TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC (introduced `sinks.py`'s violation)

## Related Docs
- `docs/guidelines/README.md` — Document-Update phase found this genuinely stale: Contribution
  Rule #2 said unscoped "Use `DeterministicRNG` for all stochastic logic," which the new
  `new_random_source()` carve-out rendered inaccurate. Rewritten to scope the rule to
  gameplay/simulation logic and cite `new_random_source()` for non-gameplay uses (INFRA-118).
- `docs/parity_ledger/infrastructure.yaml` (INFRA-118) — Parity phase filled this P0 entry's
  previously-null `test_path` with the 2 real guard tests that caught this violation, and replaced
  its vague `v2_evidence` with a concrete description of `new_random_source()` and the fix.

## Related Stored Artifacts
None (hotfix tier — no staging artifacts required).

## Related Code Areas
- `src/platform/rng.py`
- `src/observability/stream/consumer.py`
- `src/observability/alerts/sinks.py`

## Assumptions / Open Questions
None — this is a mechanical, evidence-backed fix; the two candidate approaches (misuse
`DeterministicRNG`'s gameplay-scoped API, or add both files to the guard tests' exception lists)
were both considered and rejected in favor of routing RNG-instance construction through
`src/platform/rng.py` itself, which requires no judgment call about what counts as a legitimate
exception.

## Implementation Notes
Added `new_random_source()` to `src/platform/rng.py` (module-level function, not a
`DeterministicRNG` method — it deliberately does not take `Domain`/`tick`/`entity_id`, since it is
not part of the deterministic/replay-critical API surface). Updated both call sites' fallback
default from the bare `random` module to `new_random_source()`. Removed `import random` from both
`consumer.py` and `sinks.py`; the `Optional["random.Random"]` type-hint string literals remain
valid without a runtime `random` import since they are never evaluated at runtime in this codebase
(no `typing.get_type_hints()` call touches these methods), and the `typecheck` CI job is
informational-only (`|| true`) regardless.

## Test Summary
`.venv/bin/python3 -m pytest tests/integration/kernel/test_phase2_determinism.py tests/unit/platform/test_rng_hygiene.py tests/unit/observability tests/integration/observability -m "not slow and not extra_slow" --tb=short -q`

## Files Changed
- `src/platform/rng.py` — added `new_random_source()` factory function.
- `src/observability/stream/consumer.py` — removed `import random`; use `new_random_source()`.
- `src/observability/alerts/sinks.py` — removed `import random`; use `new_random_source()`.
- `docs/guidelines/README.md` — scoped Contribution Rule #2 to gameplay/simulation logic; added
  `new_random_source()` carve-out (Document-Update phase).
- `docs/parity_ledger/infrastructure.yaml` — INFRA-118 entry: filled previously-null P0
  `test_path`, replaced vague `v2_evidence` with concrete evidence of this fix (Parity phase).

## Completion Summary
Added `new_random_source()` to `src/platform/rng.py` as a module-level factory returning a fresh
`random.Random()` instance for non-gameplay, non-replay-critical uses. Replaced the `r = rng or
random` fallback with `r = rng or new_random_source()` in `_compute_backoff_delay()` in both
`src/observability/stream/consumer.py` and `src/observability/alerts/sinks.py`, and removed
`import random` from both files. Verified `grep -n "import random"` returns no matches in either
file, and the full scoped pytest run (`tests/integration/kernel/test_phase2_determinism.py
tests/unit/platform/test_rng_hygiene.py tests/unit/observability tests/integration/observability
-m "not slow and not extra_slow"`) passed 1160/1160 (6 skipped, 0 failed), including both
previously-failing determinism guard tests individually confirmed passing.
