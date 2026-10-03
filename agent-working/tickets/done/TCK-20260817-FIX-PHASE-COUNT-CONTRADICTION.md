---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION
phase: done
date: 2026-08-17
tags: [documentation, engine]
---

# TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION

## Title
Fix 6-phase vs 7-phase contradiction across architecture.md, README.md, kernel.md

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
docs/engine/architecture.md §2 describes a 6-phase loop (INIT, GOVERNANCE, SCHEDULING, PACKETIZATION, RESOLUTION, PERSISTENCE); docs/engine/kernel.md and simulation_kernel_contract.md §4 both describe a 7-phase loop (INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE) with no GOVERNANCE/PACKETIZATION. Three P1 docs disagree, and the code (src/engine/kernel.py::tick_once) proves kernel.md/simulation_kernel_contract.md correct — architecture.md and README.md carry the fabricated GOVERNANCE/PACKETIZATION phase names and need reconciliation against the real 7 _phase_* methods.

## Scope
- Correct docs/engine/architecture.md §2's phase list to match the 7 real _phase_* methods in src/engine/kernel.py::tick_once (INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE), removing the fabricated GOVERNANCE/PACKETIZATION phase names
- Correct docs/engine/README.md's 'Core Loop' bullet, which carries the identical fabricated 'Init, Governance, Scheduling, Packetization, Resolution, Persistence' text, to match the 7-phase list
- Add an explicit clarifying note reconciling docs/engine/contracts/substrate_baseline_contract.md §4's '6 authoritative phases + PERSISTENCE as non-authoritative Observational Boundary hook' framing as equivalent to (not contradicting) the 7-phase numbering elsewhere
- Do a repo-wide grep for GOVERNANCE/PACKETIZATION as phase names across docs/engine/ before closing, to confirm no third occurrence remains

## Out of Scope
- The Collection-phase concurrency contradiction (separate ticket: TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION), which touches the same two files (kernel.md, simulation_kernel_contract.md) — coordinate but no hard ordering required
- docs/systems/ai_system.md's already-archived occurrence of the same fabricated term (handled by TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT)
- Rewriting tests/integration/kernel/test_milestone_a_closure.py's '6-phase' docstring/assertions — only decide whether a clarifying note is needed, don't alter test assertions

## Acceptance Criteria
- [x] architecture.md §2 no longer contains GOVERNANCE or PACKETIZATION as phase names; its phase list matches the 7 real _phase_* methods in kernel.py::tick_once, same order
- [x] README.md's Core Loop bullet no longer says 'Init, Governance, Scheduling, Packetization, Resolution, Persistence'; matches the 7-phase list
- [x] kernel.md + simulation_kernel_contract.md + corrected architecture.md/README.md all state the same 7 phases; grep for 'PACKETIZATION'/'GOVERNANCE' as phase names returns zero matches across docs/engine/
- [x] substrate_baseline_contract.md §4 explicitly notes its 6-phase+hook framing is equivalent to (not contradicting) the 7-phase numbering elsewhere, so it is not re-flagged as a 4th conflicting count

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260619-P0-DOC-REPAIR
- TCK-20260623-FIX-KERNEL-PHASES
- TCK-20260618-AUDIT-D17-DOCS
- TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT

## Related Docs
- docs/engine/architecture.md
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/substrate_baseline_contract.md
- docs/engine/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/engine/architecture.md
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/substrate_baseline_contract.md
- docs/engine/README.md
- src/engine/kernel.py
- tests/integration/kernel/test_milestone_a_closure.py

## Assumptions / Open Questions
- README.md wasn't named in the original proposal excerpts but has the identical defect; included in scope so the contradiction doesn't just recreate itself from a different doc
- substrate_baseline_contract.md's '6 authoritative + 1 non-authoritative hook' framing is internally consistent with test_milestone_a_closure.py's own '6-phase' docstring — leaning toward documenting the convention as canonical rather than editing the test, to avoid unscoped test changes
- This is a repeat of the same contradiction class TCK-20260619-P0-DOC-REPAIR already fixed once in kernel.md; the structural fix (living test / canonical-doc convention) is scoped to TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT, not duplicated here
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC depends on this ticket landing first (see SEQUENCE.md in this folder)

## Implementation Notes
Executed the approved plan's 6 steps in the stated dependency order:
1. `docs/engine/architecture.md` §2 heading (line 45) and prose (line 47) changed from "6-Phase"/"six
   phases" to "7-Phase"/"seven phases".
2. `docs/engine/architecture.md` §2's fabricated phase table (GOVERNANCE row 2, PACKETIZATION row 4)
   replaced with the plan's exact 7-row table (INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP,
   ADVANCEMENT, PERSISTENCE), using kernel.md's Read/Write/Emit domain vocabulary verbatim for the new
   COLLECTION/CLEANUP/ADVANCEMENT Permissions cells, per the plan's translation rule.
3. Removed the `@pytest.mark.xfail(strict=True, reason=(...))` decorator block from
   `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs`,
   run only after Steps 1-2 landed.
4. Appended the reconciling cross-reference sentence to `docs/engine/contracts/substrate_baseline_contract.md`
   §4, after the existing "Observational Boundary" paragraph. The "MUST execute the following 6 phases"
   sentence and numbered list were left byte-identical.
5. Added parity ledger entry `INFRA-367` to `docs/parity_ledger/infrastructure.yaml`. Re-grepped
   `^- id: INFRA-` before adding — INFRA-366 was still the highest existing ID, so INFRA-367 was still
   the next available sequential ID (no concurrent-session collision). Verified the entry individually
   validates against `docs/parity_ledger/schema.json`'s item schema via `jsonschema.validate`.
6. Final grep verification (`grep -rn "GOVERNANCE" docs/engine/`, `grep -rni "packetization" docs/engine/`)
   confirmed zero case-sensitive `GOVERNANCE` hits and only legitimate `Governance`-adjacent references
   remaining (architecture.md's "### Phase Governance" heading, `governance_logic.md`, `GovernorPolicy`-
   adjacent contract prose). One pre-existing, non-fabricated `packetization` hit was found in
   `docs/engine/contracts/substrate_baseline_contract.md` line 31 ("Work packetization and execution") —
   an ordinary-English-noun usage describing what COLLECTION does, predating this ticket, not in
   `PHASE_NARRATING_DOCS`, and not touched by this ticket's Step 4 edit (which only appended a sentence
   well below that line). Recorded as a Deviation in `staging_artifacts/.../plan.md` rather than silently
   treated as satisfying the plan's literal "zero hits anywhere" wording.

**Scope addition per the plan's Design Decision**: `docs/guides/simulation.md` (lines 19-20 and 25) was
also fixed, even though it is not named in this ticket's Scope/Related Docs/Acceptance Criteria. This
was required because `tests/docs/test_kernel_phase_names_consistent.py`'s `PHASE_NARRATING_DOCS` list
checks that file too, and leaving it unfixed would have turned Step 3's marker removal into a real,
unintended `AssertionError` instead of a clean pass. Line 26 (the separate 17-vs-37 pipeline-count
mismatch) was explicitly left untouched, as scoped.

No production code (`src/`) was changed — this is a documentation-only reconciliation, consistent with
the ticket's Type (bug) being a docs-drift bug, not a behavior bug.

## Test Summary
Ran, all passing, no `xfail`/`XPASS` markers in output (`.venv/bin/python3 -m pytest`):
- `tests/docs/test_kernel_phase_names_consistent.py -v` — 2 passed (`test_no_fabricated_phase_names_in_kernel_docs`
  and `test_kernel_doc_states_all_seven_real_phases` both real, unguarded passes).
- `tests/integration/kernel/test_simulation_kernel_contract.py -v` — 2 passed, unaffected.
- `tests/integration/kernel/test_milestone_a_closure.py -v` — 4 passed, unaffected (its own 6-mandated-
  phase docstring/assertions were correctly left untouched, per Scope Guards).
- `tests/docs/test_doc_integrity.py -v` — 6 passed, 1 skipped (pre-existing skip, unrelated), unaffected.
Additionally validated: new `docs/parity_ledger/infrastructure.yaml` entry `INFRA-367` individually
validates against `docs/parity_ledger/schema.json`'s item schema (`jsonschema.validate`); whole-file
YAML parses cleanly with `INFRA-367` present exactly once.

## Files Changed
- `docs/engine/architecture.md` — §2 heading/prose (6→7 phase) and phase table (GOVERNANCE/PACKETIZATION
  rows replaced with COLLECTION/CLEANUP/ADVANCEMENT rows)
- `docs/guides/simulation.md` — lines 19-20 (phase-loop sentence) and line 25 (kernel.py phase-count
  label) corrected to 7-phase; line 26 (17-vs-37 mismatch) left untouched, as scoped
- `tests/docs/test_kernel_phase_names_consistent.py` — removed the `@pytest.mark.xfail` decorator from
  `test_no_fabricated_phase_names_in_kernel_docs`
- `docs/engine/contracts/substrate_baseline_contract.md` — appended one reconciling cross-reference
  sentence after §4's "Observational Boundary" paragraph
- `docs/parity_ledger/infrastructure.yaml` — added new entry `INFRA-367`
- `docs/plans/kernel_concurrency_design_review_proposal.md` — added completion cross-link after C3
- `staging_artifacts/TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION/{plan,investigation,test_plan}.md` —
  added a `## Deviations` section (plan.md) documenting the pre-existing `packetization` hit found
  during Step 6 verification, and fixed unregistered frontmatter tags (`[fix, phase, count,
  contradiction]` → `[documentation, engine]`, matching the same gap found and fixed on a prior
  ticket in this batch)
- `tickets/inprogress/TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION.md` — this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary
Reconciled the fabricated 6-phase GOVERNANCE/PACKETIZATION kernel loop still narrated in
`docs/engine/architecture.md` §2 (and, per a documented scope addition, `docs/guides/simulation.md`)
against the real 7-phase loop (INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT,
PERSISTENCE) already correct in `kernel.md`/`simulation_kernel_contract.md`/`README.md`. Added a
reconciling cross-reference note to `substrate_baseline_contract.md` §4 so its "6 authoritative phases"
framing is explicitly documented as equivalent to, not contradicting, the 7-phase count used elsewhere.
Removed the `xfail(strict=True)` guard from `test_no_fabricated_phase_names_in_kernel_docs`, which now
passes for real, along with `test_kernel_doc_states_all_seven_real_phases`. Added parity ledger entry
`INFRA-367` recording the correction. Documentation-only change; no production code or test assertions
(other than the marker removal itself) were touched.
