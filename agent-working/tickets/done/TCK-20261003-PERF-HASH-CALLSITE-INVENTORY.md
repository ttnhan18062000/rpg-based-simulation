---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY
phase: done
date: 2026-10-03
tags: [performance, determinism, engine]
---

# TCK-20261003-PERF-HASH-CALLSITE-INVENTORY

## Title
Inventory every state-hash and fingerprint call site and every consumer of the result (PA-03A, call-site half; evidence only, no measurement)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PERF-D5 (hash policy) has to be decided on evidence, and the documents disagree with the code about how hashing is scheduled. Verified on 2026-10-02: `Kernel._phase_persistence()` calls `CanonicalStateHasher.get_hash()` directly when replay richness is `FULL` or audit mode is on, and finalization hashes directly too; `BudgetedCanonicalHasher` has no production caller; `CanonicalHashScheduler` is called only from `src/certification/harness.py`. Separately, `AuthoritativeState.fingerprint()` is called from three places in the kernel and was observed at roughly 940 ms per call at 1,000 entities (`TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`, a one-off observation, not a baseline).

Produce the call-site and consumer inventory that PERF-D5 needs. This is the first half of PA-03A. The second half — measuring hash cost on size tiers — is excluded here because the roadmap's RPG-core stability entry gate forbids taking measurements as evidence yet.

## Scope
- Add `tools/perf/hash_callsite_inventory.py`: a read-only `ast`-based scan of `src/` (no engine import, no execution) that lists every call to `CanonicalStateHasher.get_hash`, `BudgetedCanonicalHasher.get_hash`, `CanonicalHashScheduler.compute_hash`, `StateFingerprinter.get_fingerprint`, `AuthoritativeState.fingerprint`, and any other function in `src/engine/checkpoint.py` or `src/replay/fingerprint.py` that returns a digest or fingerprint of authoritative state. For each: file, line, enclosing function, which hash mechanism, and the guard expression that controls whether it runs, as written in source
- Deterministic JSON and markdown output, same conventions as `tools/perf/phase_inventory.py` (stable order, no timestamps); a `--check` mode against a committed JSON that reports added and removed call sites
- Write the analysis the script cannot derive, as a document: `docs/performance/hash_callsite_inventory.md`, generated tables plus a hand-written section, with valid frontmatter. The hand-written section records, per call site, from reading the code:
  - when it runs (every tick, on a cadence, at finalization, on demand) and under which `RuntimeMode`, replay richness, and audit-mode conditions
  - which state tick the digest describes and at which tick it is computed
  - every consumer of the value: where it is stored, compared, emitted, or returned (replay records, checkpoints, certification reports, API responses, tests), with file and line
  - which scheme produces it (flat canonical SHA-256, fingerprint dict, other) and whether two different schemes are ever compared
  - whether a stale or cached value can be returned, and by which path
- State explicitly, with the evidence, which of the three hash-scheduling mechanisms govern which call sites, and which call sites no mechanism governs
- Compare the findings with what `docs/engine/deterministic_execution.md`, `docs/engine/known_limitations.md` §2.4, and `docs/plans/design_enhancement/performance_milestones_epic.md` (M2 item 6) say about hash scheduling, and list each statement the code contradicts, with file and line on both sides. Do not edit those documents
- Tests under `tests/tools/` for the scanner: synthetic source with direct, aliased-import, and guarded calls; deterministic output; `--check` pass and fail; and one run against real `src/` asserting only that it parses and that the three kernel call sites known today are found by mechanism (not by line number)
- Add the tool and test to the test-scope map as for the sibling ticket

## Out of Scope
- Any edit under `src/`
- Measuring hash or fingerprint cost, profiling, or running the kernel — the cost half of PA-03A waits for the entry gate
- Changing hash schedule, scheme, freshness rules, or wiring any scheduler into the kernel — blocked until PERF-D5
- Proposing the hash policy; the planner session drafts PERF-D5 from this ticket's output
- Editing any authority-P1 document
- Closing or re-scoping `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`; reference it only
- Wiring `--check` into CI or any gate

## Acceptance Criteria
- [x] `python3 tools/perf/hash_callsite_inventory.py --format json` runs without importing `src`, and two consecutive runs are byte-identical
- [x] Every call site of the listed hash and fingerprint functions in `src/` appears with file, line, enclosing function, mechanism, and guard expression; a manual `grep` for the function names in `src/` finds no call the script missed, and the comparison is recorded in the test plan
- [x] `docs/performance/hash_callsite_inventory.md` records, for every call site, run condition, state tick versus computation tick, all consumers with file and line, scheme, and staleness path
- [x] The document states which scheduling mechanism governs each call site and names the ungoverned ones
- [x] Every contradiction between the three named documents and the code is listed with file and line on both sides; none of those documents is edited
- [x] Tests pass; the real-source test does not pin line numbers or a total count
- [x] `git diff` touches only `tools/`, `tests/tools/`, `docs/performance/`, `docs/REGISTRY.yaml`, `tickets/`, `stored_artifacts/`, `agent-monitoring/`, and the test-scope map file

## Related Tickets
- TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC (this is its `PERF-M0-T07` evidence half)
- TCK-20260913-PERF-M0-OWNER-TRIAGE (C-06 and C-09 dispositions)
- TCK-20260614-HASH-SCHEDULER (origin of `CanonicalHashScheduler`)
- TCK-20260627-P2F-CANON-HASH-DOC
- TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE
- TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED
- TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT (sibling; shares output conventions)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (C-06, C-09, PERF-D5 stub)
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_prerequisite_execution_plan.md` (PA-03A)
- `docs/engine/deterministic_execution.md`
- `docs/engine/known_limitations.md`
- `docs/plans/design_enhancement/performance_milestones_epic.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260913-PERF-M0-SOURCE-AUDIT/source_inventory.md`
- `stored_artifacts/TCK-20261003-PERF-HASH-CALLSITE-INVENTORY/` (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- `src/engine/checkpoint.py`, `src/engine/kernel.py`, `src/replay/fingerprint.py`, `src/core/state.py`, `src/certification/harness.py`, `src/worldbuilding/compiler.py` (all read only)
- `tools/perf/`, `tests/tools/`

## Assumptions / Open Questions
- Evidence-only release, same basis as the sibling ticket: owner approval of the foundation slice on 2026-10-02
- RPG-core is adding fields to `src/core/state.py`; that changes what the hash covers, not where it is called, so the call-site inventory stays valid across those merges and the script regenerates it when it does not
- If a consumer cannot be traced with confidence (for example a digest passed through a generic dict), record it as "consumer not traced" with the last known hand-off point; do not guess
- Implement after `TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT`, so the output conventions are settled once
- The planner session reviews the inventory document before this ticket closes

## Implementation Notes
Hand-orchestrated by perf-implementer. Stdlib `ast` only, receivers resolved by name (imports, aliases, `x = Class()` assignments); unresolved receivers are listed, not guessed. A text prefilter keeps the real-tree scan to about 1.6 s. `--update-doc` rewrites only the marked generated block of the markdown so the hand-written analysis survives regeneration. Calls inside the mechanisms' own modules are marked as delegations, and the hasher's own `hashlib` use is not reported as a bypass.

## Test Summary
`python3 -m pytest tests/tools/test_hash_callsite_inventory.py tests/tools/test_test_scope_coverage_static.py -q` -> 48 passed (19 new). No test pins a line number or a total count. Manual grep comparison (recorded in the test plan): 13 calls plus the hashlib site, scanner reports 14, none missed. Two JSON runs byte-identical; `--check` exits 0. perf-planner reviewed with no changes.

## Files Changed
- tools/perf/hash_callsite_inventory.py, tests/tools/test_hash_callsite_inventory.py (new)
- tools/gate_checks/test_scope_coverage_static.py (one line in `_TOOLS_PERF_BASENAME_MAP`)
- docs/performance/hash_callsite_inventory.md, docs/performance/hash_callsite_inventory.json
- tickets/todos/perf-evidence-inventories/ -> tickets/done/ (this file); stored_artifacts/; tickets/working_log.csv, docs/REGISTRY.yaml, agent-monitoring/ (closure bookkeeping)

## Completion Summary
Call-site inventory delivered: 14 call sites in `src/`; `CanonicalHashScheduler` governs only the two certification-harness calls, `BudgetedCanonicalHasher` governs nothing, and the kernel's per-tick and shutdown hashes, the compile-time hash and a hand-rolled SHA-256 in the harness are ungoverned; the MD5 fingerprint family is a separate scheme; the per-tick hash describes tick T+1 and the REFINED_UPDATE fingerprint tick T; seven document statements contradict the code. No `src/` or document edit. Not traced: what reads the replay files. Known follow-up from the sibling ticket still open: `.claude/agents/test-scoper.md` carries a copy of the test-scope map and was not updated for the two new `tools/perf` tools; perf-planner raises it with the user.
