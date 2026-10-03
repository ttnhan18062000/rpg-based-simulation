---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT
phase: open
date: 2026-10-03
tags: [performance, determinism, documentation]
---

# TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT

## Title
Apply the approved PERF-D1/D2/D4/D5/D6 decisions and the C-01..C-16 dispositions to the P1 documents (PERF-M0-T09; documents only)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The repository owner approved PERF-D1, D2, D4, D5, and D6 on 2026-10-03 (`docs/architecture/performance_optimization_decisions.md`). Each record says its P1 document edits "are not yet applied (`PERF-M0-T09`)". The M0 epic defines `PERF-M0-T09` as "P1 roadmap and contract reconciliation — updated/superseded P1 plans through their owners; one discoverable execution order", waiting for every decision that changes a P1 document. All of those are now decided.

Apply the edits. Every edit states current behavior truthfully or records the approved contract, and points to its decision. The code is not changed: where an approved decision describes a mechanism that does not exist yet (Canonical contract, typed digest status, phase catalog), the document says it is the approved contract and that the implementation is pending, with the ticket or program ID, rather than describing it as built.

## Scope
Each item names its source decision or disposition. Line references are from the inventories and may have drifted; locate by content.

1. **`docs/engine/deterministic_execution.md`**
   - PERF-D1: describe the two contracts (Canonical, Live bounded) with their guarantees and the control-input classification table; state that today's runs satisfy neither fully (the three wall-clock inputs), that `audit_mode` is the current way to suppress two of them, and that `verification_level = REDUCED` stays the label for a Live run without a verified trace. Incorporate any additional input found by `TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY` if it has closed; otherwise cite PERF-D1's three
   - PERF-D2: rewrite "Scope of the guarantee" as the DET-PORT-0/1/2 tiers, the reference runtime (CPython 3.13, Linux x86-64), and the rule that every proof records its tier and runtime identity
   - PERF-D5: in "The canonical hash", name the proof digest (`flat-sha256-v1`) and the stability check (MD5 fingerprint, not full state), and state that only the proof digest backs a determinism, replay, certification, or parity claim
   - PERF-D5 and `docs/performance/hash_callsite_inventory.md` §6 rows 1-4: correct when the per-tick hash is computed (conditions and modes), delete the float-rounding claim (D5 point 5: removed, not implemented), and correct the `tick_hash` / `TICK_END` warehouse-field and "replay divergence is detected by comparing `tick_hash` sequences" statements, including the "Replay tick_hash comparison" section, to what exists (payload key `"hash"` in a replay `TraceEvent`; no reader in `src/`)
   - "Known non-determinism sources" and "Regression tests": add the fingerprint-based tests named in PERF-D5 as stability checks, not proofs
2. **`docs/engine/known_limitations.md` §2.4**: hash inventory §6 rows 5 and 6 (fingerprint is MD5 over selected domains; the `DEGRADED` row omits the audit-mode condition)
3. **`docs/engine/runtime_profiles.md` §4**: qualify the "same profile, identical semantics on different hardware classes" statement to the Canonical contract (PERF-D1)
4. **`docs/plans/design_enhancement/determinism_envelope_epic.md`**: answer M1 item 1 ("canonical or live bounded") with "both", citing PERF-D1 (C-04)
5. **`docs/engine/performance_contract.md`, `docs/engine/contracts/certification_contract.md` §3, `docs/performance/perf_baseline_policy.md`** (PERF-D4, C-13), driven row by row by `docs/performance/performance_clause_inventory.md` from `TCK-20261003-PERF-M2-CLAUSE-INVENTORY`:
   - the contract states that it is the single clause-level authority, defines the tripwire and the capacity run with their different claims, the four outcomes (missing or incompatible baseline is `INCONCLUSIVE`), and the result identity fields (PERF-D2 runtime identity, PERF-D1 contract, `RuntimeMode` sequence, processed-work count)
   - the current 10/50-tick average check is described as the tripwire and carries no capacity claim; existing `tests/perf/baselines/` JSON files are tripwire references only
   - the baseline policy's hardware-class table is removed in favor of `certification_contract.md` §3; its §3 thresholds are moved into the contract as capacity-run targets or deleted, per the inventory's PERF-D4 destination column; the policy keeps the calibration procedure only
   - nothing in these documents claims a gate behavior that does not run; where a target has no enforcing check yet, it says so and names `PERF-M2-T03`/`T04`
   - the checks in the inventory's §6.2 that the two-projection shape cannot express get the disposition perf-planner gives when this ticket starts (expected: overhead ratios and within-run trend checks as a third, named "comparative" clause kind in the contract; absolute ceilings and the `PerfBudget` store recorded as tripwire-adjacent debt for `PERF-M2-T03`; OA-11 stays a runtime-control rule outside the contract). Do not choose these yourself; ask for the disposition if it is missing
6. **`docs/engine/authoritative_pipeline.md`** (PERF-D6, C-02): define the counted unit (*refinement phase* = one `run_phase()` call in `refine`; *kernel phase* = a `TickPhase` member); remove the literal "39" from the heading and prose; mark the table as not yet checked against code and point to `docs/performance/phase_inventory.md` for the generated list and its differences (6 executable phases missing, `active_contracts` unmatched); state that the typed catalog in `src/engine/phase_graph.py` becomes the source when `PERF-M3-T01` lands. Do not hand-add or rename table rows
7. **Phase-count mentions elsewhere** (PERF-D6 point 5): the "39-phase" text in `CLAUDE.md` (Engine Contracts table) and in `AGENTS.md`. `AGENTS.md` is generated by `tools/agent_orchestration_codex_adapter/generator.py` from `agent-working/agent-orchestration/`: edit the source and regenerate, never hand-edit `AGENTS.md`. Mark the D19 audit's phase list a historical snapshot where it is presented as current
8. **`docs/plans/design_enhancement/performance_milestones_epic.md`** (C-07, C-09, C-10, C-11, and hash inventory §6 row 7): mark spatial decomposition, narrow SoA, memoization, and hierarchical hashing as Gate A candidates, not committed milestones; exclude M2 item 4 from the preselected set; state hierarchical hashing's PERF-D5 conditions (new versioned scheme, flat audit at certification boundaries, material Gate A cost); state concurrent Resolution and aggregate simulation are Gate B separate-architecture proposals (under evaluation in M6-T05 per the owner's technology direction); correct the "`BudgetedCanonicalHasher` already limits the rate" statement (the wrapper has no production caller and PERF-D5 retires it)
9. **`docs/plans/design_enhancement/design_enhancement_roadmap.md` Section A** (C-01): link the P2 package `docs/plans/design_enhancement/performance_optimization/` beneath this P1 roadmap as its evidence-gated execution plan, with the decisions file as the record of approved decisions; P1 stays the parent authority. Clarify the "C-03/C-04" grouping per finding F-09. Give the one discoverable execution order the epic asks for: a short ordered list of performance milestones with their gate (entry gate, Gate A, Gate B) and pointers, not a copy of the P2 plans
10. **`docs/plans/design_enhancement/subphase_domain_contracts_epic.md`** (C-14): replace the automatic cross-epic M3 path to concurrency with Gate B and separate-architecture wording; the phase domain declarations are justified by identity, drift detection, and instrumentation, and share one format with the data-oriented core proposal (PERF-D6 point 6)
11. **`docs/architecture/performance_optimization.md`** (C-16): make its status and scope unambiguous: keep verified surviving decisions, mark the removed RabbitMQ mechanism historical
12. **`docs/performance/optimization_architecture.md`** (C-15): apply the inventory's classification: verified current behavior stays, target statements are labeled as targets, obsolete statements are removed or marked superseded; phase counts follow item 6
13. **Parity ledger and divergences**: for each edited claim, check `docs/parity_ledger/` (at least `infrastructure.yaml` and `substrate.yaml`) for an entry that cites the old text (float rounding, `tick_hash` comparison, 39 phases, hardware classes, baseline thresholds) and update its `text`/`v2_evidence`/`divergence_note`. No behavior changes, so no `intentional_divergences.md` entry is expected; if one of the edits reveals one, stop and report it
14. **Decisions file**: in `docs/architecture/performance_optimization_decisions.md`, change each "not yet applied (`PERF-M0-T09`)" note to "applied by `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT`", and record F-06 (the two never-created P1 tracking epics) as resolved by item 9's execution order or as still open with a reason
15. After all edits: `make knowledge-index-update`; regenerate `docs/REGISTRY.yaml`

## Out of Scope
- Any edit under `src/`, `tests/`, `tools/` (except running the `AGENTS.md` generator), or `.github/`
- Implementing any decision: no Canonical proxies, control trace, digest record, scheduler change, phase catalog, gate change, or baseline change
- Changing any threshold value, sample size, or `hard` flag in code
- Creating the `TCK-20260825-EPIC-PERFORMANCE-EVOLUTION` / `-SUBPHASE-DOMAIN-CONTRACTS` tickets (F-06): record the decision only
- Editing the P2 plans under `docs/plans/design_enhancement/performance_optimization/` beyond fixing a link that an edit above breaks
- Registering `docs/brainstorm/` (F-05)

## Acceptance Criteria
- [ ] Every item 1-14 is applied, or recorded in Implementation Notes with the reason it was not
- [ ] No edited document describes an approved-but-unbuilt mechanism as existing; each such statement names its pending ticket or program ID
- [ ] Each of the seven statements in `docs/performance/hash_callsite_inventory.md` §6 is corrected, and the hash inventory's "consistent" statements are left consistent
- [ ] The three performance documents agree with each other and with every row of `docs/performance/performance_clause_inventory.md`'s PERF-D4 destination column; a check of the inventory against the edited text is recorded in the test plan
- [ ] No literal refinement-phase count remains in `authoritative_pipeline.md`, `CLAUDE.md`, or `AGENTS.md`; `AGENTS.md` matches its regenerated output
- [ ] Parity ledger entries citing changed text are updated and `docs/parity_ledger/schema.json` validation passes
- [ ] `tests/static`, `tests/docs`, and `tests/architecture` pass (the doc and frontmatter checks, the AGENTS.md generator drift check if one exists)
- [ ] `git diff` touches only `docs/`, `CLAUDE.md`, `AGENTS.md`, `agent-working/agent-orchestration/` (the generator source line only), `agent-working/tickets/`, `agent-working/stored_artifacts/`, `agent-working/agent-monitoring/`, and the knowledge index files
- [ ] The repository owner approves the P1 diff on the PR (these are authority-P1 documents)

## Related Tickets
- TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC (parent; this is `PERF-M0-T09`)
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY (required input for item 5 and 12)
- TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY (optional input for item 1)
- TCK-20261003-PERF-HASH-CALLSITE-INVENTORY, TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT (evidence)
- TCK-20260913-PERF-M0-OWNER-TRIAGE (C-01..C-17 dispositions)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (all PERF-D records, C-01..C-17, F-05..F-11)
- `docs/performance/hash_callsite_inventory.md` §6, `docs/performance/phase_inventory.md`
- `docs/plans/design_enhancement/performance_optimization/performance_m0_architecture_governance_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` ("Plan review, 2026-10-02")
- every document listed in Scope

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260913-PERF-M0-SOURCE-AUDIT/source_inventory.md`
- `agent-working/stored_artifacts/TCK-20261003-PERF-HASH-CALLSITE-INVENTORY/`

## Related Code Areas
- none edited; `src/engine/kernel.py`, `src/engine/checkpoint.py`, `src/engine/pipeline.py`, `src/engine/phase_graph.py`, `src/engine/governor.py` are read only to confirm wording

## Assumptions / Open Questions
- Implement after `TCK-20261003-PERF-M2-CLAUSE-INVENTORY` closes; item 5 and 12 depend on it. Items 1-4 and 6-11 do not, and can be drafted first
- If the wall-clock inventory is still open when this starts, item 1 cites PERF-D1's three inputs and says the inventory is pending; do not wait for it
- The owner approved the decisions, not the wording. The PR is the owner's review of the P1 wording; perf-planner reviews first
- If an edit would change what a test or gate asserts (for example a doc test pinning "39"), stop and report it rather than editing the test
- Large: if the diff becomes hard to review, split at item 5 (performance documents) into a second ticket and tell perf-planner

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
