---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE
phase: open
date: 2026-09-15
tags: [observability, testing, data-quality]
---

# TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE

## Title
`test_redis_adapter_async_non_blocking` failed twice in CI on `published_events == 1` while the event itself published correctly — `flush()` appears not to guarantee the health counter is visible on return

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Surfaced during review of `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`
(PR #199), whose own changes touch nothing in this subsystem. Filed so the finding is tracked
rather than left in a review transcript — the "findings die in prose" failure recorded as Finding 7
in `docs/plans/agent_infrastructure/reachability_verification_findings.md`.

`tests/unit/observability/test_redis_stream_adapter.py::test_redis_adapter_async_non_blocking`
publishes one event through `RedisStreamAdapter` (with `redis` mocked), calls `adapter.flush()`,
then asserts both that the event reached Redis and that the adapter's own health counters reflect
it:

```python
adapter.publish(event)
adapter.flush()

assert mock_client.xadd.call_count == 1      # passed in CI
...
health = adapter.health()
assert health["status"] == "healthy"
assert health["published_events"] == 1       # FAILED in CI: assert 0 == 1
```

**The failure is specifically the counter, not the publish.** The CI log for the first occurrence
shows the `xadd` assertions passing and only `published_events` failing as `assert 0 == 1`. So the
event genuinely reached the (mocked) Redis client, and the background worker had done its actual
work — what had not happened by the time `health()` was read was the counter increment. That points
at a real ordering gap between `flush()` returning and the worker thread publishing its own
bookkeeping, i.e. `flush()`'s completeness contract, rather than at a mock or wiring problem.

## Scope
- Determine what `flush()` is actually supposed to guarantee on return. If it is meant to mean "all
  queued events are fully processed, bookkeeping included", then the counter update is inside the
  contract and the adapter has an ordering bug. If it only means "the queue is drained to the
  client", then the contract is narrower than the test assumes and the *test* is over-asserting —
  but that must then be stated explicitly in `flush()`'s own docstring, not left implicit.
- Fix whichever side the answer implicates, in the way that preserves the test's discriminating
  power. If the adapter is at fault, make the counter update happen-before `flush()` returns. If the
  contract is narrower, the test must still verify the counter — via a deterministic wait on the
  adapter's own state, not by deleting the assertion.
- Add a regression test that would fail against today's code if the ordering gap is real, rather
  than only passing once the fix is in.

## Out of Scope
- Weakening, deleting, or adding a blanket retry/sleep to the existing assertion to make CI green.
  Per the Gate Integrity rule this is explicitly forbidden, and this ticket exists because the
  failure is believed to be real information, not noise.
- Any change to `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` / PR #199.
  That PR does not touch this subsystem; the two are unrelated beyond the failure surfacing there.
- The wider `Perf / cert / arena` redness on `main` observed across every merge on 2026-09-14.
  Different job, different subsystem, separately tracked.

## Acceptance Criteria
- [ ] `flush()`'s guarantee is stated explicitly in its docstring, whichever way the investigation
      resolves it.
- [ ] A test exists that fails against the current implementation if the ordering gap is real
      (not merely one that passes after a fix).
- [ ] `test_redis_adapter_async_non_blocking` still asserts `published_events == 1` — the counter
      remains verified, by whatever mechanism the fix chooses.
- [ ] The disposition is recorded even if the conclusion is "test over-asserted, contract is
      narrower" — that is a legitimate outcome, but it must be written down rather than silently
      relaxing the test.

## Related Tickets
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` (PR #199) — where this
  surfaced; unrelated in substance.
- `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` (done) — prior work on this adapter (DLQ, PEL reclaim,
  reconnect backoff). Worth reading for the adapter's threading model before changing `flush()`.
- `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` (open) — the interpreter-parity hazard that made this
  investigation slower than it should have been; see Implementation Notes.

## Related Docs
- `docs/testing/regression_policy.md` — consulted; this test is **not** covered by any
  environment-dependent/flaky category there. The only near-match row is the live-server API test
  file set, and that row explicitly records two prior tickets misdiagnosing failures by stretching
  its generic label. Do not stretch it to cover this file.

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tests/unit/observability/test_redis_stream_adapter.py` (lines 21-56; assertion at line 54)
- `src/observability/` — `RedisStreamAdapter`, its `publish()`, `flush()`, `health()` and worker
  thread

## Assumptions / Open Questions
- **The second failure's test identity is unverified and may never be recoverable.** Two CI runs of
  `Unit · infra / observability` failed (`109b88e90`, then `0ea4a0e51`). The *first* was positively
  identified from its log as this test. The *second* could not be identified by either session that
  tried: the raw log redirect to `productionresultssa0.blob.core.windows.net` fails TLS against a
  `Fortinet SDNS Blocked Page` certificate, the check-run annotations carry only
  `Process completed with exit code 1`, the check-run `output` field is empty, and the run produced
  zero artifacts. So "the same test failed twice" is **plausible but unproven** — that lane runs
  ~2684 tests across 17 directories.
- What *is* established for the second failure: it failed at step 5 (`Run`, the pytest step), with
  a step profile byte-identical to the first (`pip install`, `checkout`, `setup-python` and
  `Job summary` all green). So it is a genuine test failure, not an infrastructure step failing and
  merely looking the same at check-run level.
- The lane is green on `main` and green locally. See Implementation Notes for exactly how green.

## Implementation Notes
- **Local runs cannot currently reproduce this**, under either interpreter:
  - Python 3.12.3 (`.venv/bin/python3`): full 17-path lane, CI's markers — 2684 passed, 1 skipped.
  - Python 3.13.14 (`.venv313/bin/python3`, matching CI's declared `python-version: "3.13"`): the
    same lane — 2684 passed, 1 skipped; and this test alone in a repeat loop — 8/8 passed.
- **Read that interpreter detail carefully, because it invalidated earlier reasoning on this very
  failure.** Two sessions independently ran the lane on `.venv` (3.12) and reported it "green,
  matching CI" — it was not matching CI, which runs 3.13. The version gap was only excluded once
  `.venv313` was used deliberately. `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` documents this exact
  trap, written the day before both sessions fell into it.
- A timing-sensitive failure that never reproduces locally may need a stress/repeat harness or
  artificial scheduler pressure to surface. Do not conclude "not reproducible, therefore not real"
  from a clean local run — the whole point of this failure class is that it appears under load.
- If a third CI run of this lane passes, that is evidence toward flake but still does not explain
  a counter reading 0 immediately after `flush()` returned. The ordering question stands on its own
  and is answerable by reading the adapter's code, independent of any CI run.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_To be completed by the implementer._
