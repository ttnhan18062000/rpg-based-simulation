---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES
phase: open
date: 2026-10-25
tags: [performance, determinism]
---

# TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES

## Title
A benchmark record's identity pins the installed runtime dependency set; then re-record idle_100_local and movement_100_local as v0002

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
On 2026-10-25 both local venvs were synced to `uv.lock` (owner, #715 issuecomment-6387278967): pydantic moved 2.12.5 -> 2.14.1 and pydantic-core 2.41.5 -> 2.50.1. A `BenchmarkRecord` (`src/perf/benchmark_record.py`) records the interpreter (`identity.runtime.python_version`) but not the installed packages: on main there is no lock hash and no package version anywhere in it. So `compare()` treats a pre-sync record and a post-sync run as compatible. A change of the installed stack is invisible to the tripwire, which is how the stale venvs went unnoticed behind the 10-24 local reading (#593 issuecomment-6385558358).

Owner decision (2026-10-25, option A, #715 issuecomment-6387497480):
1. Add a dependency fingerprint to the record's runtime identity, blocking: a mismatch reads `INCONCLUSIVE` with a named reason. It is a schema MINOR bump.
2. Then one heavy slot re-records `idle_100_local` and `movement_100_local` as `v0002` under it. The owner promotes them in this PR.

## Scope
**Part 1: the field** (src/perf only, perf-owned, no lift):
- Add `Runtime.dependency_fingerprint: str = UNKNOWN` to `src/perf/benchmark_record.py`. It is the sha256 of the **installed runtime dependency closure**, not of `uv.lock` (see Assumptions):
  - Start from `[project].dependencies` in `pyproject.toml`. Requirements with extras (`uvicorn[standard]`) bring in those extras' requirements.
  - Walk each installed distribution's `importlib.metadata` `requires`. Evaluate environment markers for the running interpreter with `extra` set only for the extras actually requested.
  - Canonicalise names (PEP 503) and emit sorted `name==version` lines.
  - A required distribution that is not installed is emitted as `name==MISSING`, so an incomplete venv changes the fingerprint and does not silently match.
  - The value is prefixed with a scheme tag (e.g. `deps-v1:<hex>`), so a later change to the method is itself a visible mismatch.
- Also record `Runtime.dependency_count: Optional[int]` (the number of lines hashed) as a recorded-only diagnostic, not blocking.
- Fill both fields wherever `Runtime` is built for a real run (the capture path that fills `python_version` today). Put the closure walk in one small `src/perf/` helper, not inlined.
- Add `identity.runtime.dependency_fingerprint` to `_BLOCKING`. When the two sides differ, `compare()` returns `INCONCLUSIVE` through `_check_blocking_fields`, naming the field and both values. `UNKNOWN` on both sides behaves like the other unknown blocking fields: it is listed as unverified identity and is not a mismatch.
- `SCHEMA_VERSION`: MINOR bump over whatever main has at the time (1.4 after #735). Update `docs/performance/benchmark_identity_schema.md` (status line, field table, JSON schema) and every pinned version assert. Also `docs/parity_ledger/infrastructure.yaml` INFRA-430, whose text says "schema 1.4" after #626. That file is rpg's: the edit needs an rpg-planner-ubuntu (or rpg-planner) OK in the PR. No test pins it. INFRA-431 states a count, not a version.
- A record without the field loads (`from_dict` default `UNKNOWN`). Against a head that has one, it reads `INCONCLUSIVE` (blocking field differs). That is intended: every pre-2026-10-25 local record is from the stale stack.

**Part 2: the re-record** (needs a heavy-run slot from lead-planner, and the owner's promotion approval in this PR):
- Re-record `tests/perf/baselines/idle_100_local` and `movement_100_local` as `*.v0002.json` on the synced venv, through the baseline lifecycle T05 defines. Use the same protocol, profile and seed as v0001.
- Retire v0001 as that lifecycle says. Do not delete or hand-edit records outside it.
- Run constraints: foreground, one at a time, `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, and check loadavg1 < 1.5 and >= 2.5 GB available before each run.
- In the PR, state host, CPU, both fingerprints (v0001 = unknown, v0002 = value) and the run IDs.

## Out of Scope
- The `_concurrent` references, `mixed_200_*`, `strategic_100_*` and the simq corpus references. They are not re-recorded here; their next re-record picks the field up.
- Changing the tripwire threshold (owner-final, PERF-M2-T06).
- Making any perf check blocking (OD-8).
- Hashing `uv.lock` bytes, dev/extra groups, or tool versions (pytest, ruff).
- The CI paired tripwire: both arms run under head's environment, so their fingerprints match by construction. No CI change.

## Acceptance Criteria
- [ ] `Runtime` has `dependency_fingerprint` (default `UNKNOWN`) and `dependency_count`. A real capture fills both, and the fingerprint is stable across two captures in one environment.
- [ ] A unit test with a fake metadata provider shows four cases:
  - changing the version of a runtime-closure package changes the fingerprint;
  - adding, removing or bumping a package outside the closure (a dev-only or extra-only package not requested) does not;
  - an uninstalled required package yields a `MISSING` line;
  - a requested extra's requirements are included.
- [ ] `compare()` on two records differing only in `dependency_fingerprint` returns `INCONCLUSIVE`, with `check == "blocking_fields"` (T06's `Outcome.check`) and a reason naming `identity.runtime.dependency_fingerprint`.
- [ ] An old record without the field loads. Compared against a fingerprinted head, it is `INCONCLUSIVE`, not PASS.
- [ ] Schema MINOR bump; `benchmark_identity_schema.md` documents the field and the closure method; pinned version asserts are updated.
- [ ] `idle_100_local.v0002.json` and `movement_100_local.v0002.json` exist with a non-`UNKNOWN` fingerprint, recorded under the run constraints above. The owner's promotion approval is recorded in the PR (and on #715) before merge.
- [ ] The nightly lane (`tests/perf/test_perf_regression_baseline.py -m 'perf and slow' -k idle_100_local` and `-k movement_100_local`) runs against v0002 on the same host, and the PR reports the outcome.

## Related Tickets
- TCK-20261010-PERF-M2-T02B-RECORD (BenchmarkRecord)
- TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE (promotion and retirement)
- TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE (`Outcome.check`; schema 1.4; PR #735, must merge first)
- TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (v0001)
- TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS (F1: its hash-scheme change will force another re-record)

## Related Docs
- docs/performance/benchmark_identity_schema.md
- docs/engine/performance_contract.md (read only; no edit)

## Related Stored Artifacts
None.

## Related Code Areas
- src/perf/benchmark_record.py (`Runtime`, `_BLOCKING`, `SCHEMA_VERSION`)
- the Runtime capture path in src/perf/
- tests/perf/baselines/
- tests/unit/perf/

## Assumptions / Open Questions
- **Why the installed closure and not `sha256(uv.lock)`:** this was lead-planner's refinement, which perf adopted (#715 issuecomment-6387497480).
  - A whole-file lock hash changes when any dev-only or extra-only package moves. The in-flight `TCK-20261024-UV-LOCK-SECURITY-BUMPS` changes torch, mcp and pyjwt, and none of those can affect a tick. A lock hash would make every local reference `INCONCLUSIVE` for nothing.
  - A lock hash also describes the lock, not what is installed. The 10-24 failure was an installed venv lagging the lock, which a lock hash would not have caught.
  - The installed runtime closure moves exactly when a package the engine can import moves.
- **Known blind spot:** a package the engine imports that is not reachable from `[project].dependencies` (for example, imported only through an extra or a dev group) is not in the fingerprint. The schema doc must state this.
- Sequencing: dispatch after #735 merges (one open PR per track; both bump the schema). Part 2 waits for a slot from lead-planner.
- The fingerprint is host-independent: the same packages give the same value on any host. Hardware is already pinned by the existing `runtime.*` fields.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
