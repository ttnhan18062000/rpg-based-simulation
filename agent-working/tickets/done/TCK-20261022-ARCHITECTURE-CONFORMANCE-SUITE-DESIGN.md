---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261022-ARCHITECTURE-CONFORMANCE-SUITE-DESIGN
phase: done
date: 2026-10-22
tags: [architecture, determinism]
---

# TCK-20261022-ARCHITECTURE-CONFORMANCE-SUITE-DESIGN

## Title
Conformance-suite design for the engine execution modes: the worlds, seeds and assertions each mode must pass, and what each assertion cannot see

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`docs/plans/architecture/engine_execution_modes_proposal.md` §5 names a conformance suite as the precondition for Modes 2, 3
and 5. Modes 2 and 3 must reproduce Mode 1's final canonical hash, Mode 4 asserts invariants only, and Mode 5 asserts
invariants and outcome distributions only. The port-leak audit (`docs/plans/architecture/port_leak_audit.md`,
TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT) showed that a hash-equality assertion alone is not enough today. The user
approved this design and asked for it to start now, before proposal step 1 lands (#715 issuecomment-6345579717 and
issuecomment-6346236596). The work is design only: no tests, no code, no runs.

## Scope
- Write a new doc, `docs/plans/architecture/conformance_suite_design.md` (frontmatter `layer: architecture`), covering:
  1. **Mode preconditions.** Mode 1 runs on fixed budgets (`audit_mode`, or pinned NORMAL), per PERF-D1 A2 (see
     `docs/architecture/performance_optimization_decisions.md`). `CANONICAL` is only for cost or governance runs. The suite
     never compares runs across signal contracts, so every case records its contract and refuses a mixed pair. For Mode 2,
     carry perf's conditions from #593 issuecomment-6343379030: the flag is recorded and mixed arms are refused, `no_replay` is
     passed from the arm path only (`rpg_gate_run.build_kernel` is shared with the gate), and replay stays on where a per-tick
     digest trail is needed.
  2. **Worlds and seeds.** A small fixed matrix. Name candidate worlds from what exists (the scenario and world registries,
     the `tests/certification/` and SimQ corpus worlds) and say why each one is in it: which subsystems it exercises, its tick
     count and its rough cost. Include at least one world that fires faction attacks (audit F4), and one checkpoint-restore case
     (audit F3), marked as expected-red until its fix lands.
  3. **Assertions per mode.** For each of Modes 1 to 5, list what is asserted (final canonical hash, invariants such as
     HardLawMonitor and conservation, outcome distributions) and, explicitly, **what the assertion is blind to**. Hash
     equality cannot see `item_instances`, `recent_world_events`, `quest_registry`, `factions`, `clans` or
     `information_providers` until perf's PERF-D5 scheme bump. Propose a stopgap per-field digest for those six, as a design
     option only; whether to use it is perf's call.
  4. **Cross-process cases.** Same seed in two processes with different `PYTHONHASHSEED` (it catches audit F4), and two runs in
     one process (it catches the process-global singletons, the Mode 3 pool case). Mark which ones are expected-red today.
  5. **Lane placement (draft).** Propose which lane each case runs in (fast, slow, nightly, CI job), using the T2 facts:
     GitHub-hosted runners, 4 vCPU / 16 GB, 6 h job limit, free minutes, no self-hosted runner, both arms of a pair in one job
     on one VM, and runner timing unfit for timing comparisons. Mark the placement **pending testing-planner**.
  6. **Dependencies.** A table of each case and what it waits on (step-1 tickets H2 to H4 and T1 to T3, the PERF-D5 bump, the
     rpg fixes F1, F3 and F4, the A2 default flip, the v1 baseline). Anything that needs step-1 code is marked `pending step 1`.
  7. **Open questions**, with owners.
- Add the doc to `docs/plans/architecture/README.md` Contents.

## Out of Scope
- Writing or changing tests, or anything under `src/**`, `tests/**`, `docs/architecture/**` or `docs/performance/**`.
- Runs, timings or hash experiments.
- Editing `engine_execution_modes_proposal.md` (item B, held for architecture-planner-u24).
- Deciding lane placement (testing-planner), the hash scheme (perf-planner) or rpg semantics such as whether
  `recent_world_events` is canonical (rpg-planner). Record each as an open question.

## Acceptance Criteria
- AC1: every mode (1 to 5) has its preconditions, assertions and a "blind to" list.
- AC2: every world in the matrix has a reason, a rough tick count and cost, and a pointer to where it is defined (`path`).
- AC3: audit findings F1 to F5 each map to a case or to an explicit "not covered, because".
- AC4: lane placement is marked as a draft pending testing-planner, and every case lists its dependency.
- AC5: frontmatter validates, README Contents updated, `docs/REGISTRY.yaml` regenerated and committed.
- AC6: no file outside `docs/plans/architecture/**`, `docs/REGISTRY.yaml`, this ticket and `agent-working/agent-monitoring/`
  is changed.

## Related Tickets
- TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT (input)

## Related Docs
- docs/plans/architecture/engine_execution_modes_proposal.md (§4, §5, §6)
- docs/plans/architecture/port_leak_audit.md
- docs/plans/architecture/faster_feature_testing_draft_tickets.md (step 1: H2 to H4, T1 to T3)
- docs/architecture/performance_optimization_decisions.md (PERF-D1 A2, PERF-D2, PERF-D5)
- docs/testing/test_taxonomy.md
- docs/engine/performance_contract.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/certification/ (test_cert_long_run_stability.py, test_phase10_enhanced_determinism_parity.py), src/engine/checkpoint.py,
  src/engine/signal_source.py, the rpg gate runner (rpg_gate_run)

## Assumptions / Open Questions
- Assumes testing-planner places lanes later; the doc proposes only.
- Item B may change proposal wording. Where the design depends on proposal text, cite it by section, not by quote.

## Implementation Notes
Context scan first (search_docs, then graphify query). Branch: architecture-implementer-engine-modes, on top of 7971418a1.
Close by hand with `--path-reason investigation_only`. Send the SHA to architecture-planner before any push.

## Test Summary
Design only; no tests apply. `tools/validate_frontmatter.py` on the new doc: no violations.

## Files Changed
- docs/plans/architecture/conformance_suite_design.md (new)
- docs/plans/architecture/README.md (Contents row)
- docs/REGISTRY.yaml (regenerated)
- ticket move and monitoring shards

## Completion Summary
Conformance-suite design written. Covers mode preconditions (fixed budgets for Mode 1, never compare across contracts,
perf's Mode 2 conditions), a six-world matrix with reasons and costs (gate worlds cost UNVERIFIED), per-mode assertions with
blind-to lists, an inverted canary for the six unhashed fields, cross-process cases X1-X4, contract and guard cases, a
draft lane placement pending testing-planner, a dependency table and seven open questions with owners. F1-F5 each map to a
case or a stated reason. Whether any shipped world fires a faction attack is UNVERIFIED and is the first probe (A0).
