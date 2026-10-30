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
- Interpreter guard (added 2026-10-29, perf-planner): the first two v0002 series ran under `/usr/bin/python3` and fingerprinted `deps-v1:e4a1cd0c` (29, stale system stack) instead of the synced venv's `deps-v1:e71fd726` (30); both were discarded. `tools/perf/rerun_baselines.py` `record` and `measure` now refuse to run outside a virtualenv (`sys.prefix == sys.base_prefix`) with a clear error, and every `record` summary prints `sys.executable` and the candidate's `dependency_fingerprint` (also stored in `summary.json`). No override flag: the callers (`_profiling_common` imports `load_corpus_state` only; the unit tests call `main` in-process) need none. Records are taken with `.venv/bin/python`; after run 1 of each record the fingerprint must read `deps-v1:e71fd726...` (30) or the series stops.
- CPU affinity (added 2026-10-30, perf-planner; owner's split #715 6515978105 / 6516066857: Docker on vCPUs 0-3, perf pinned to 4-5): `Runtime.cpu_affinity` (canonical range string of the sorted `os.sched_getaffinity(0)`, `src/perf/cpu_affinity.py`), blocking, schema 1.5; `logical_cores` and `hardware_class` read the host and are not affected by pinning (stated in the 1.5 history clause).
- Quiet-window gate (perf-planner, 2026-10-30; `tools/perf/quiet_gate.py`, used by `rerun_baselines record` before EACH run): a process pinned to a strict subset of the host CPUs needs every allowed CPU below 10 % busy over 5 s (`/proc/stat`); an unpinned process keeps loadavg1 < 1.5. Always: `MemAvailable >= 3 GB` (raised from 2.5) and `pswpin`/`pswpout` unchanged over the same 5 s. A failure before run 1 refuses (exit 1); before a later run it stops the series, names the failed check and writes no candidate. The readings are printed per run and stored in `summary.json` (`gates`).
- In-run foreign-load check, pinned runs only (perf-planner, 2026-10-30): busy jiffies of the allowed CPUs and this process's cgroup `usage_usec` (`cpu.stat` of the cgroup in `/proc/self/cgroup`, the `systemd-run` scope the measure children inherit) are read at the start and end of each run; foreign share = (busy on allowed CPUs - own usage) / (len(allowed) x run wall seconds), clamped at 0. A share >= 10 % stops the series (no candidate, exit 1, message names the run and the share); each run's share is recorded in `summary.json`. Unpinned runs skip it; an unreadable cgroup file refuses the pinned series rather than skipping the check. In-run swap check (perf-planner, 2026-10-30, after the first pinned window): `RunWatch` also reads `pswpin`/`pswpout` at the start and end of each pinned run; any change stops the series (no candidate, exit 1, the message names the run and the page counts); unreadable `/proc/vmstat` refuses the series; the delta is stored in `summary.json` (`gates[].swap_delta`). Host-wide load: a pinned run's pre-run gate also requires loadavg1 < 1.5, in addition to the per-CPU check. Host-speed probe (host-specific protocol setting, not a contract value): `record --max-probe-ms N` (default off) makes a pinned run wait, up to `--wait-s`, until the host-speed probe taken just before it is <= N (35 ms for the overnight window; quiet on this host reads 27-33 ms); both probes of every run and the limit are recorded in `summary.json` as data, with no post-run stop (an after-probe spike does not touch the timed span). Own-scope guard: a pinned series is refused unless the cgroup basename from `/proc/self/cgroup` matches `run-*.scope` (a transient `systemd-run --scope` unit), otherwise `usage_usec` would belong to a larger cgroup and the share be understated. Unreadable readings fail the gate by name ("available memory unreadable", "swap counters unreadable"); the clock tick is `os.sysconf("SC_CLK_TCK")` (100 only if sysconf raises). `systemd-run --user -p AllowedCPUs=` does not pin here (no cpuset delegation to the user manager): the window command is `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 .venv/bin/python tools/perf/rerun_baselines.py record ...`.
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
- [ ] `rerun_baselines.py record` and `measure` refuse a non-virtualenv interpreter with a clear error (unit test), and each record summary prints the interpreter and the candidate's `dependency_fingerprint`.
- [ ] `Runtime.cpu_affinity` is recorded, blocking, documented (field table, JSON schema, section 4 table, 1.5 history clause with the host-fields note); unit tests: an affinity difference is `INCONCLUSIVE` with `check == "blocking_fields"`, an old record without the field loads as `unknown`, the range helper is canonical.
- [ ] `record`'s quiet window is the pinned/unpinned gate above (memory >= 3 GB, no swap activity), refuses before run 1 or stops the series naming the check, and prints and stores the readings per run; unit-tested with injected `/proc` readers and no real sleep.
- [ ] The in-run swap check stops a pinned series on any `pswpin`/`pswpout` change (naming the run and the pages) and refuses on unreadable counters; a pinned run also needs loadavg1 < 1.5; `--max-probe-ms` makes a pinned run wait for a quiet before-probe and records both probes; all unit-tested with injected readers.
- [ ] The in-run foreign-load check stops a pinned series at a share >= 10 % (no candidate), records every run's share, skips unpinned runs and refuses a pinned series whose cgroup file is missing or unreadable or whose cgroup is not a `run-*.scope`; unit-tested with injected `/proc` and cgroup readers.
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

### Evidence: why the protocol changed (2026-10-29 / 10-30 pinned windows; text only, no candidate JSON)

Setup of both tables: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 .venv/bin/python tools/perf/rerun_baselines.py record <name> --wait-s 1800` at `ea08a48a6`; host ubuntu, i5-11400H, 6 vCPU; fingerprint `deps-v1:e71fd7267597388a9cf4f55773d8d95cffdbae01581544075d54ffabb6e82066` (30) and `cpu_affinity` "4-5" on every run. Probe = the median of 5 host-speed spins (ms, higher = slower host moment), taken by the measure child before the state build and after the timed span. Gate columns are as read at each run start; swap in+out pages were 0 at every start; foreign share of the allowed CPUs is in the last column. v0001 fingerprint = unknown.

**Pinned `idle_100_local` (2026-10-30; unpromoted evidence, 13.7 % over the middle 3 of 5, 53.5 % over all 5; the tool picked run 1)**

| run | avg_ms | probe before -> after | wall_s | host load1 | MemAvailable MB | busy cpu4/cpu5 % | host swap used MB | foreign share |
|---|---|---|---|---|---|---|---|---|
| 1 | 45.7 | 35.6 -> 30.8 | 5.0 | 2.29 | 3410 | 4.4 / 2.1 | 3272 | 0.0 % |
| 2 | 50.5 | 39.9 -> 31.0 | 3.9 | 3.26 | 3616 | 5.9 / 4.7 | 3269 | 0.0 % |
| 3 | 58.6 | 40.7 -> 51.0 | 4.7 | 2.98 | 3560 | 2.1 / 1.6 | 3269 | 0.0 % |
| 4 | 44.4 | 30.8 -> 32.7 | 3.6 | 1.80 | 3496 | 3.3 / 1.7 | 3273 | 0.0 % |
| 5 | 38.2 | 32.9 -> 57.6 | 4.1 | 2.59 | 3169 | 4.8 / 1.0 | 3458 | 0.0 % |

**Pinned `movement_100_local` series A (2026-10-30; NOISY, 19.0 % over the middle 3 of 5, 42.6 % over all 5; discarded)**

| run | avg_ms | probe before -> after | wall_s | host load1 | MemAvailable MB | busy cpu4/cpu5 % | host swap used MB | foreign share |
|---|---|---|---|---|---|---|---|---|
| 1 | 121.5 | 49.1 -> 42.5 | 9.8 | 2.20 | 3216 | 6.1 / 8.1 | 3466 | 0.1 % |
| 2 | 102.1 | 26.8 -> 34.4 | 7.2 | 1.80 | 3112 | 7.5 / 4.3 | 3484 | 0.0 % |
| 3 | 90.8 | 29.0 -> 38.2 | 6.4 | 1.00 | 3151 | 4.2 / 3.6 | 3488 | 0.0 % |
| 4 | 129.5 | 46.2 -> 34.6 | 8.4 | 0.92 | 3183 | 4.4 / 1.7 | 3496 | 0.0 % |
| 5 | 105.3 | 53.0 -> 57.2 | 8.1 | 0.74 | 4361 | 1.0 / 1.0 | 4024 | 0.0 % |

Reading (five points per series; a correlation, not a cause): in both series the before-probe sorts the averages and nothing else gated on does. Movement: the two fastest runs (2 and 3) have the quietest before-probes (26.8 and 29.0 ms), and the three slowest (1, 4, 5) have 46 to 53 ms, while host load1 was only 0.92 and 0.74 on slow runs 4 and 5. Idle: the slowest runs (3 and 2) have the slowest before-probes (40.7 and 39.9 ms) and the fastest (5) a quiet one (32.9 ms). Foreign share was at most 0.1 % everywhere, so the noise is not other processes on CPUs 4-5 during a run; it is host-speed variation the 5 s busy sample does not see. After-probe spikes (idle runs 3 and 5: 51.0 and 57.6 ms) fell after the timed span and did not touch the run's own average, which is why the probe gate is pre-run only. Host swap in use rose during both windows (3.27 to 3.46 GB during idle; 3.47 to 4.02 GB during movement) while pswpin/pswpout stayed 0 at every start; the record's own processes were swap-capped, the source was not diagnosed. The earlier unpinned series (2026-10-29, `/usr/bin/python3` and the first `.venv` series) are not evidence: the first two fingerprinted the stale system stack (`deps-v1:e4a1cd0c`, 29), the third ran unpinned.

## Test Summary

## Files Changed

## Completion Summary
