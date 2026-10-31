---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261101-PERF-V0002-RECORD-AFTER-FINDING-WHAT-MOVES-HOST-SPEED
phase: open
date: 2026-11-01
tags: [performance]
---

# TCK-20261101-PERF-V0002-RECORD-AFTER-FINDING-WHAT-MOVES-HOST-SPEED

## Title
Find what moves the ubuntu VM's speed, then re-record idle_100_local and movement_100_local as v0002

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Part 2 of TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES, moved here by the owner's option 1 (#715 issuecomment-6546382922). That ticket shipped the fingerprint, schema 1.5, the venv guard and the pinned gates, with no v0002 record.

Until v0002 exists, `idle_100_local` and `movement_100_local` stay on v0001 (no fingerprint), `compare()` reads them as INCONCLUSIVE against a fingerprinted head, and the nightly lane gives no regression reading.

Why the record failed on 2026-10-31 (tables in the parent ticket's Implementation Notes): pinned to CPUs 4-5 at d4bd4c96b, with all gates passing, idle read NOISY at 33.45 % (middle 3 of 5). Movement A was stopped in run 2 by the in-run swap check (pswpin +1). One hour earlier the same movement scenario read 2.25 % in calibration. The host-speed probe on idle CPUs ranged 30-54 ms over 20 readings. The working reading, not yet proven, is that speed varies from outside the guest.

## Scope
**Step 1: find what moves the host speed (first, no record attempt before it).**
- The owner makes the Windows-side checks below; guest tools cannot see them. Results are logged on #715.
  Facts on record (#715 6527003378, lead-planner 2026-11-01): host CPU i5-11400H, 6 cores / 12 threads, no hybrid P/E cores. VirtualBox VM with 6 vCPUs. VT-x confirmed in VBox.log, hypervisorlaunchtype off.
  Still to check:
  1. VBS / Memory Integrity state.
  2. Any execution cap on the VM.
  3. Windows power plan, whether on mains power, and CPU frequency or thermal throttling during a guest probe.
  4. What else uses host CPU, memory and disk in a window: other VMs, antivirus scans, Windows Update, indexing, browsers. Host memory pressure.
  Candidate to test (unmeasured, a guess from lead-planner): 6 vCPUs on 6 cores with hyperthreads means the host may place two vCPUs, or a vCPU and a Windows thread, on sibling threads, and pinning inside the guest cannot control that.
- In the guest: run the host-speed probe on CPUs 4-5 alongside a host-side reading of the same period (one lead slot), and see whether the probe swings match a host-side cause.
- State the finding, including "not found". If nothing is found, bring the owner a choice between a different host or runner and accepting no local tripwire for these scenarios.

**Step 2: decide how to deal with the swap check.** It stopped two series on foreign swap-in alone (3 pages, then 1 page), with the run's own scope unable to swap. Any change to it is a protocol change for the owner to approve, argued from evidence and stated in the PR. Clearing swap alone did not hold: about 705 MB returned within minutes.

**Step 3: the re-record (lead slot, owner go).**
- Re-record the two scenarios as `*.v0002.json` through the T05 baseline lifecycle, same protocol, profile and seed as v0001; retire v0001 as that lifecycle says.
- Rules fixed before the data: state which series is the record before running; run calibration first when the host setup has changed.
- Promotion is the owner's, in the PR.

## Out of Scope
- Loosening the 15 % noise rule (owner, 2026-10-16). It holds whatever this ticket finds.
- Making any perf check blocking (OD-8).
- Other baselines (`_concurrent`, `mixed_200_*`, `strategic_100_*`, simq corpus).

## Acceptance Criteria
- [ ] The Windows-side check results are logged on #715 and summarised in this ticket.
- [ ] A finding on what moves the host speed is stated with its evidence, or "not found" with the owner's choice recorded.
- [ ] `idle_100_local.v0002.json` and `movement_100_local.v0002.json` exist with a non-`UNKNOWN` fingerprint, recorded under the run constraints in force. The owner's promotion approval is recorded in the PR and on #715 before merge. (If the owner's choice is no local tripwire, record that decision instead and close without them.)
- [ ] The nightly lane (`tests/perf/test_perf_regression_baseline.py -m 'perf and slow' -k idle_100_local` and `-k movement_100_local`) runs against v0002 on the same host, and the PR reports the outcome.
- [ ] Virtualisation mode: decide whether it joins record identity, or state why not. It is not in identity today, and the VM moved from NEM to VT-x on 2026-10-30.

## Related Tickets
- TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES (parent)
- TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
- TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (v0001)
- TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS (F1: its hash-scheme change forces a re-record)

## Related Docs
- docs/performance/perf_baseline_policy.md (2.1 spread rule)
- docs/performance/baseline_invalidation_ledger.md
- docs/performance/benchmark_identity_schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/perf/rerun_baselines.py, tools/perf/quiet_gate.py
- tests/perf/baselines/

## Assumptions / Open Questions
- Calibration and chain numbers are at d4bd4c96b; code merged later makes them evidence only.
- Soft-lockup readings were empty before and after the chain, so the 10-30 panic's symptom did not recur in that boot. That is not proof of its cause.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
