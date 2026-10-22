---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, performance, testing]
---

# Draft tickets: faster feature testing (step 1 and step 2 of the execution-modes proposal)

**These are DRAFTS, not filed tickets.** `architecture-planner-u24` is advisory and does not file or dispatch work
outside `docs/plans/architecture/`. Each owning planner decides whether to file a draft, edits it, and moves it into
`agent-working/tickets/` under its own ID. Proposed IDs below are placeholders.

**Freeze: every draft is AFTER v1.** Nothing touching `src/**` lands before the v1 record PR merges.

**Context:**
- the proposal: `engine_execution_modes_proposal.md`, §3, steps 1 and 2;
- the evidence: `docs/performance/tick_cost_growth.md`. Its numbers are PROVISIONAL: one loaded 6-vCPU VM, `py-spy`
  phase shares, pinned contract, `no_replay`. Its §8 says to re-measure on a quiet host before quoting a millisecond;
- the user's pending decision: whether H2, H3 and H4 get fix tickets now or a note on #593 that they wait. These
  drafts carry the evidence for that decision.

**Already owned elsewhere, so not drafted here:**
- H1 hostility per pair: `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`, rpg Lane B;
- H5 `final_integrity` timer: handed to rpg on #593;
- per-run `wall_seconds` and RSS retention: routed by lead-planner-u24 to rpg and testing, after v1;
- incremental hashing: PERF-M5-T04.

| draft | what | measured evidence (share of tick, scenario) | proposed owner |
|---|---|---|---|
| H2 | cooperation candidate enumeration rebuilt per entity per tick | 43 to 61 % of `strategic_100` (365 of 615 ms), 27 % of `mixed_200`, 10 to 27 % of corpus `frontier_extended` / `frontier_marches` | rpg-planner |
| H3 | EventRecorder buffer eviction: re-measure the partial fix, finish or close | 42.5 % of samples in late `frontier_extended` (ticks 604 to 643), **measured before** the 2026-10-19 partial fix | rpg-planner, perf reviews |
| H4 | validated pydantic construction of engine-made events | 2 to 14 % (`pydantic/main.py:250`), plus 1 to 6 % `event_shapers.py`; up to 14 % of `strategic_100` | rpg-planner |
| T1 | count runs, reruns and STOPs per measured step | none recorded: only narrative in the memo and handovers | testing-planner |
| T2 | paired arms off this host (CI or a second machine) | `--jobs 2` cap from host co-tenancy and the reaper; a 5-seed step is about 2 to 3 h `[inferred]` from handover ETAs | testing-planner; lead for host policy |
| T3 | `no_replay` for paired arms (Mode 2), after a perf ruling | phase-7 digest 9.2 % (`strategic_100`) to 27.1 % (`frontier_extended`) when replay is allowed; gate and paired runs have it on | perf-planner rules; rpg or testing implements |

---

## H2: cooperation candidates are enumerated per entity per tick

Proposed ID: `TCK-2026MMDD-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK`. Layer `engine`. Tier `standard`.
Type `refactor`. Priority P2. Tags `[performance, cooperation]`.

**Request summary.**
- `PartnerCandidateProvider.get_candidates` (`src/domains/cooperation/providers.py:33`) loops over every entity in
  `state.entities` for each requesting entity (`:43`), so the scan is O(n²) per tick.
- For each candidate it calls `are_entities_hostile` (`:52-53`), which is also the H1 path.
- `tick_cost_growth.md` §3 H2 measured it, with `identity_resolver.resolve` at 2 to 15 %:
  - 43 to 61 % of `strategic_100`;
  - 27 % of `mixed_200`;
  - 10 to 27 % of corpus worlds;
  - cooperation is 31 % of `frontier_marches` early ticks (§2).
- #394 (`TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK`) fixed only the pending-offer lookup in
  the same phase.

**Scope:**
- Build the candidate source once per tick, e.g. a spatial bucket plus the trusted-social set, and have
  `get_candidates` read it.
- Keep the selection order and the result exactly. Follow the #394 pattern, which used a per-tick index plus a
  differential test against the old scan.

**Out of scope:**
- Hostility semantics (H1, Lane B).
- Changing which partners are chosen.

**Acceptance criteria:**
- [ ] Identical canonical hashes on the corpus under `audit_mode` (`performance_contract.md` §4.1), and a paired
  `--neutral` result of IDENTICAL.
- [ ] A differential test: the old scan and the index give the same candidate tuple on fixed states.
- [ ] Before and after `cooperation` phase cost on `strategic_100` and one corpus world, same host, same method.

**Coordinate with:** H1. Both sit on the `are_entities_hostile` path, and the §3 projection notes "H1 and H2
overlap a little".

---

## H3: EventRecorder eviction: re-measure the partial fix, then finish or close

Proposed ID: `TCK-2026MMDD-EVENT-RECORDER-EVICTION-COST-AFTER-THE-SEVERITY-COUNTS`. Layer `observability`. Tier
`hotfix` if only a re-measure, `standard` if a fix. Type `chore` (`refactor` if it becomes a fix). Priority P3. Tags
`[performance, observability]`.

**Request summary.**
- `tick_cost_growth.md` §3 H3 measured the eviction at 42.5 % of samples in late `frontier_extended` (ticks 604 to
  643). Advancement grew from 16 % to 40 to 45 % of the tick, and the cause was a full buffer scan per recorded event
  once `max_events` (5000) is reached.
- `TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER` (merged in #645, 2026-10-19) has since
  replaced the full scan with per-severity counts (`src/observability/event_recorder.py:250-260`, "the scan stops at
  its first (oldest) event"). That fix shipped after the profile, and nobody has re-measured.
- What remains is `list.pop(index)` and the all-CRITICAL `pop(0)` (`:233`, `:235`). Both are O(n) memmoves over at
  most 5000 references [inferred: small].

**Scope:**
- Re-profile late `frontier_extended` (600 warmup ticks, as `tick_cost_growth.md` §7 item 6 asks) at main.
- If the eviction is still above about 2 % of the tick, replace the list with per-severity deques or a ring buffer,
  covering both paths, as §7 item 1 asks.
- Otherwise record the result and close.

**Acceptance criteria:**
- [ ] The re-measured share of `EventRecorder.record` and `_bound_buffer` in late `frontier_extended`, with method
  and host recorded.
- [ ] If fixed: the event file is unchanged (event counts per 500-tick bucket equal, as the 10-16 ticket proved) and
  the canonical hashes are identical.

---

## H4: engine-made events are constructed with full pydantic validation

Proposed ID: `TCK-2026MMDD-ENGINE-MADE-EVENTS-SKIP-VALIDATION`. Layer `observability`. Tier `standard`. Type
`refactor`. Priority P3. Tags `[performance, observability]`.

**Request summary.**
- `tick_cost_growth.md` §3 H4 measured `pydantic/main.py:250 __init__` at 2 to 14 % and `observability/event_shapers.py`
  at 1 to 6 %, up to 14 % of `strategic_100`. It classes this as "probably waste": the engine validates events it
  has just produced itself.
- #645's typed event catalog may have changed construction since the profile, so re-measure first.

**Scope:**
- Re-measure on `strategic_100`.
- If it is still material, construct engine-made events without validation (`model_construct`, or validation only
  at the boundary), and keep validation for anything that crosses the API or file boundary.

**Out of scope:** event schema changes.

**Acceptance criteria:**
- [ ] A test proves an engine-made event built without validation serializes byte-identically to the validated one,
  for each event kind in the catalog.
- [ ] Canonical hashes and event-file contents identical on the corpus.
- [ ] Before and after shares recorded.

**Risk:** skipping validation hides a malformed engine event. Keep validation in tests (a flag or a test-only check).

---

## T1: count runs, reruns and STOPs per measured step

Proposed ID: `TCK-2026MMDD-MEASURED-STEP-RUN-AND-RERUN-LEDGER`. Layer `testing`. Tier `standard`. Type `feature`.
Priority P2. Tags `[testing, performance]`.

**Request summary.**
- Nothing records how many paired or gate runs a step took, how many were reruns, or why they were rerun (STOP,
  refusal, ordering change, host kill).
- The only records are narrative: owner memo row 76 and the rpg handovers. For example, a diet step measured 3
  times, a STOP rerun at 10 seeds, and a `NonAuditRunError` rerun on 2026-10-22.
- Without counts, the 09 plan's phase-1 baseline cannot name the dominant term.

**Scope:**
- Append one row per paired or gate invocation to a ledger: step, base and new SHA, worlds, seeds, ticks, runs
  executed, runs reused from cache, wall seconds, outcome (`PASS` / `STOP` / `REFUSED` / killed), rerun-of.
- Report per step totals.

**Depends on:** the per-run `wall_seconds` and RSS retention already routed to rpg and testing.

**Acceptance criteria:**
- [ ] Every `paired.py` and gate invocation writes one row, including refused and killed ones.
- [ ] A summary command prints runs, reruns and wall time per step.

---

## T2: run paired arms off this host

Proposed ID: `TCK-2026MMDD-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST`. Layer `testing`. Tier `standard`. Type `feature`.
Priority P2. Tags `[testing, performance]`.

**Request summary.**
- `paired.py` defaults to `--jobs 2` ("the reaper kills at 3 heavy processes", `tools/rpg_measure/paired.py:194`).
- An engine run needs about 101 to 200 MB (`tick_cost_growth.md` §5; the gate harness measured 126 to 200 MB). The
  cap comes from the shared host: 6 cores and 8.7 GB, 15+ sessions, a global OOM on 2026-10-22.
- The gate already shards per world on CI (`.github/workflows/rpg-gate-report.yml`). Paired arms have no CI path,
  and PR #529 is perf's tripwire, not this.

**Scope:**
- A workflow, or a second-host runner, that runs the arms one process per (world, seed), using the same
  `arm_child.py`, the same cache key (`<sha>-<child hash>-<ticks>`) and `PYTHONHASHSEED=0`, then collects the
  results into the existing `paired.py` comparison.
- The base-vs-base self-check runs the same way.

**Out of scope:**
- Changing what paired runs measure or prove.
- Making the job a required check (test_architecture roadmap principle 8).

**Acceptance criteria:**
- [ ] A paired result from the off-host path equals the local one, byte for byte, on one step.
- [ ] Wall time per step recorded (T1).
- [ ] Runner identity (PERF-D2 tier, interpreter, OS) recorded with the results.

**Note:** PERF-D2 tier. A CI runner is a different host but the same build and interpreter, so it stays DET-PORT-0
only if the runtime identity matches. Otherwise base and new must both run on the same kind of runner.

---

## T3: `no_replay` for paired arms (Mode 2), after a perf ruling

Proposed ID: `TCK-2026MMDD-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST`. Layer `testing`. Tier `standard`. Type
`feature`. Priority P2. Tags `[testing, performance, determinism]`.

**Request summary.**
- Gate and paired arms run with `audit_mode` and no `no_replay` (`tools/test_architecture/rpg_gate_run.py:60-66`),
  so replay is allowed and Phase 7 computes the per-tick SHA-256 digest (`src/engine/kernel.py:1125`;
  `docs/engine/kernel.md`, "State Hashing in Phase 7").
- That digest is 9.2 % (`strategic_100`) to 27.1 % (`frontier_extended`) of a tick (`tick_cost_growth.md` §4,
  PROVISIONAL). This is a lower bound on the saving, because `no_replay` stops every replay emit.
- Paired proofs never read it. `arm_child.py:58,69` hashes the start and final state directly with
  `CanonicalStateHasher.get_hash`. The neutral check (`paired.py:174-180`) and the self-check (`stats.py:125`)
  compare those hashes plus fates and counters.

**Needs first:** a perf-planner ruling that `no_replay` in outcome runs is consistent with PERF-D1 A2. It changes no
budget and reads no clock, but the contract is perf's.

**Scope:**
- Pass `no_replay` in the paired arm kernel.
- Note what `no_replay` turns off: every `ReplayManager.emit` (`src/engine/replay_manager.py:99`), so
  `REFINED_UPDATE` (`kernel.py:657`) and `TICK_END` go too, not just the digest.
- Verify four things:
  - hashes are identical with and without it, i.e. no game logic reads `replay_allowed`;
  - the behaviour counters `arm_child.py:35-36` tallies from `simulation_events.jsonl` are still written;
  - no consumer on the paired or gate path reads the replay stream;
  - the result manifest records the flag.
- Then decide separately whether the gate harness adopts it (testing-planner).

**Acceptance criteria:**
- [ ] On 3 worlds × seed 42 × 1000 ticks: start and final hashes, fates and counters are identical with and without
  `no_replay`.
- [ ] Paired refuses to compare an arm run with replay against one run without it, unless the hashes prove them
  equal.
- [ ] Measured wall time per run before and after, same host.
