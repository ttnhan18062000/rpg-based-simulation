---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT
phase: done
date: 2026-08-17
tags: [documentation, engine, architecture]
---

# TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT

## Title
Audit docs/engine, docs/architecture, docs/performance for stale/duplicate/contradictory content; propose a drift-prevention structure

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
This discussion surfaced three live contradictions between individually-authoritative docs (the Collection-concurrency contradiction, the 6-phase-vs-7-phase contradiction, and an already self-flagged hardware-class conflict between perf_baseline_policy.md and certification_contract.md per TCK-20260702-OBSISO-ISOLATION-PROOF). The author wants a broader audit of docs/engine, docs/architecture, and docs/performance for other stale/duplicate/contradictory docs, plus a proposed structural convention to reduce this class of drift going forward, with findings recorded even where no immediate fix is applied.

## Scope
- Produce an audit doc (following D17's precedent/format) enumerating docs across the three directories (~102 files: docs/engine/ 83, docs/architecture/ 15, docs/performance/ 4), sampled at D17's own depth (3-5 verifiable claims/doc), not claimed exhaustive
- Formally defer (via callout-box, citing the discovering ticket, following perf_baseline_policy.md's "> Known conflict, not resolved here" convention) the hardware-class conflict between perf_baseline_policy.md and certification_contract.md (per TCK-20260702-OBSISO-ISOLATION-PROOF)
- Record the newly-found simulation_kernel_contract.md §9 broader staleness (3 of its 4 bullets look stale: "No scheduler optimization" vs DeterministicScheduler.select_work(), "No adaptive degradation" vs the RuntimeMode ladder, "No external event brokers" vs SimQ's broker mode) with the unconfirmed hypothesis that §9 may describe minimal_kernel.md's narrower scope, needing owner confirmation — do not silently fix
- Cross-link the concurrency and phase-count contradictions in the audit as already-ticketed rather than re-fixing them
- Write down a concrete structural convention with an enforcement mechanism (canonical-doc-per-topic map with cross-link-only rule for satellites, or a periodic/automated doc-parity check), with at least one example wired into a living test, following the test_agents_md_pipeline_note_matches_live_engine_doc pattern
- **(Added 2026-08-17, from independent audits D23/D24 — see Assumptions):** fold in two further pieces of evidence for the same phase-count contradiction that neither of the two seed tickets currently cites: (a) `docs/guides/simulation.md:19-26` describes yet another 6-phase loop and cites `src/engine/authoritative_pipeline.py` as "the 17-phase mutation sequence" — that file does not exist (the real implementation is `src/engine/pipeline.py` + `src/engine/pipeline_phases/`); (b) root `CLAUDE.md` itself states a third number, a "32-phase refinement sequence," for the same subsystem. Both should be corrected as part of this audit's phase-count reconciliation work, alongside architecture.md/README.md.

## Out of Scope
- Fixing the Collection-concurrency contradiction (already ticketed: TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION)
- Fixing the 6-phase vs 7-phase contradiction (already ticketed: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION)
- Actually resolving the hardware-class conflict or the §9 broader-staleness hypothesis — record/defer only, pending owner confirmation
- Full D17-depth audit of all 102 files if Plan-phase confirms breadth exceeds one ticket — may split into directory-scoped follow-ups (engine-contracts / engine-matrices / architecture / performance)

## Acceptance Criteria
- [x] Audit doc enumerates every doc across the three directories (~102 files) with a stale/current/uncertain/duplicate/contradictory classification, sampled at D17's own depth, not claimed exhaustive
- [x] The audit explicitly resolves-by-cross-reference or formally defers (callout-box) each of: the concurrency contradiction, the phase-count contradiction, the hardware-class conflict, AND the newly-found simulation_kernel_contract.md §9 broader staleness — cross-linking D17, P0-DOC-REPAIR, OBSISO
- [x] A concrete structural convention is written down WITH an enforcement mechanism, not just prose — either a canonical-doc-per-topic map with cross-link-only rule, or a periodic/automated doc-parity check, with at least one example wired into a living test
- [x] Any newly-found P1-vs-P1 contradiction NOT fixed in this ticket is recorded via the same callout-box format, citing this ticket's ID

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260618-AUDIT-D17-DOCS
- TCK-20260619-P0-DOC-REPAIR
- TCK-20260702-OBSISO-ISOLATION-PROOF
- TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (source of the two new evidence pieces added 2026-08-17)

## Related Docs
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/certification_contract.md
- docs/engine/contracts/minimal_kernel.md
- docs/engine/authoritative_pipeline.md
- docs/performance/perf_baseline_policy.md
- docs/performance/simq_isolation_overhead.md
- docs/audits/D17_documentation_currency.md
- docs/audits/audit_dimensions.md
- docs/guides/simulation.md (added 2026-08-17 — cites nonexistent src/engine/authoritative_pipeline.py)
- docs/audits/D23_architecture_resilience.md (added 2026-08-17)
- docs/audits/D24_codebase_health_observatory.md (added 2026-08-17)
- CLAUDE.md (added 2026-08-17 — states a third "32-phase" claim)

## Related Stored Artifacts
None.

## Related Code Areas
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/certification_contract.md
- docs/engine/contracts/minimal_kernel.md
- docs/engine/authoritative_pipeline.md
- docs/performance/perf_baseline_policy.md
- docs/performance/simq_isolation_overhead.md
- docs/audits/D17_documentation_currency.md
- docs/audits/audit_dimensions.md
- docs/plans/kernel_concurrency_design_review_proposal.md
- tests/agent_orchestration_codex_adapter/test_agents_md_generation.py

## Assumptions / Open Questions
- Scope is large (102 files); full D17-depth audit likely too big for one standard ticket — explicit sampled scope or directory-scoped follow-ups may be needed if Plan-phase confirms breadth exceeds one ticket
- §9's broader staleness needs owner confirmation of the minimal_kernel.md hypothesis, not an assumed fix
- Strongest evidence for "prose-only fixes re-drift": kernel.md's own dual-table contradiction was already fixed once by TCK-20260619-P0-DOC-REPAIR, yet architecture.md now has a structurally identical contradiction — direct proof a durable check is needed, not just another one-off correction
- Hardware-class conflict was explicitly out of OBSISO's scope; this ticket only re-records it via callout-box, does not fix it
- This audit's scope is explicitly narrowed to avoid duplicating the concurrency and phase-count fix tickets (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION, TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION), focusing on broadening the search beyond the 3 known cases; no hard ordering dependency on those two tickets, though this audit will be more complete if run after they land
- `layer: engine` chosen over `architecture` or `performance` since docs/engine/ is the largest directory in scope (83 of ~102 files) and the two seed contradictions (concurrency, phase-count) both originate there; note this choice here per CLAUDE.md guidance

## Implementation Notes

Executed all 10 steps of the approved plan (`staging_artifacts/TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT/plan.md`):

1-2, 9-10. Wrote `docs/audits/D25_engine_docs_drift.md`: header/methodology, the 16-doc D17-depth
classification table, a "Remaining Files" note for the ~94 lighter-pass files, a "Known
Contradictions" section (4 subsections: concurrency, phase-count, hardware-class, §9 staleness —
each cross-linking D17/P0-DOC-REPAIR/OBSISO/the two OPEN seed tickets as required), a "Parity
Ledger Notes" section (SUB-008, SUB-307/308/309), and "Proposed Structural Convention +
Enforcement Mechanism" + "Recommended Follow-Up" sections (follow-up ticket recommended in prose
only, not filed, per plan).
3. `docs/engine/README.md:13-14` — fixed both stale phase-count claims (6-phase→7-phase names;
   17-phase→37-phase).
4. `CLAUDE.md:258` — fixed the kernel.md summary row's phase names; line 259 left untouched
   (verified already correct).
5. `docs/engine/architecture.md` — added the `> Known conflict, not resolved here` callout box
   after the §5 hardware-class table, citing this ticket and OBSISO.
6. Created `tests/docs/test_kernel_phase_names_consistent.py` exactly per plan (case-sensitive
   GOVERNANCE / case-insensitive packetization), with `test_no_fabricated_phase_names_in_kernel_docs`
   wrapped `xfail(strict=True)`.
7. Created `tests/docs/test_doc_path_existence.py` and fixed `docs/guides/simulation.md:26`'s
   `authoritative_pipeline.py`→`pipeline.py` citation. **Deviation from plan** (see
   `staging_artifacts/.../plan.md`'s new "Deviations" section for full detail): running the new
   test for real surfaced 34 dead path citations across 17 files in the three scoped directories,
   not the single citation the plan anticipated. 22 were confirmed renames and fixed directly
   (listed in Files Changed below); 2 were bugs in the check itself (missing regex word-boundary;
   missing `src/legacy/` exemption for the legacy ledger's intentionally-dead historical entries),
   also fixed. The remaining 12 — mostly citations with zero renamed-file candidates found anywhere
   in the tree, i.e. likely never-implemented rather than moved — are tracked via
   `pytest.mark.xfail(strict=True)` on the test, itemized in the audit doc's "Recommended
   Follow-Up" section as concrete backlog. The test therefore reports `XFAIL`, not `PASS`, at this
   ticket's closure — a deliberate, disclosed deviation, not a silently-forced pass.
8. `docs/plans/kernel_concurrency_design_review_proposal.md` — added the one cross-link line after
   the existing 3-item "Known documentation drift" list; list itself untouched.

**Also discovered, not fixed (flagged, not this ticket's scope):**
`tests/docs/test_prescan_mandate_instruction_draft.py::test_draft_does_not_modify_claude_md_or_agent_md_files`
(from the already-closed `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`) now fails — it
asserts `git diff --stat HEAD -- CLAUDE.md ...` is empty, a leftover regression guard that will
break for any future commit touching `CLAUDE.md`, triggered here by this ticket's required Step 4
edit. Not fixed in this ticket (editing another ticket's test file is outside this ticket's scope);
recommend a follow-up hotfix to scope or remove that guard.

## Test Summary

- `pytest tests/docs/test_kernel_phase_names_consistent.py -v` → 1 passed
  (`test_kernel_doc_states_all_seven_real_phases`), 1 xfailed as designed
  (`test_no_fabricated_phase_names_in_kernel_docs`, pending the two OPEN seed tickets). Matches
  plan's expected outcome exactly.
- `pytest tests/docs/test_doc_path_existence.py -v` → 1 xfailed
  (`test_doc_path_citations_exist`). **Does not match plan's expected `PASS`** — see Implementation
  Notes / staging plan.md Deviations for why (34 real findings vs. the 1 anticipated; 22 fixed, 12
  disclosed and deferred via xfail).
- `pytest tests/docs/test_doc_integrity.py -v` → 6 passed, 1 skipped (pre-existing skip, unrelated
  to this ticket). Matches plan's "existing tests must still pass unchanged."
- Side-effect discovered (not part of the plan's required verification list):
  `pytest tests/docs/test_prescan_mandate_instruction_draft.py -v` → 4 passed, 1 failed
  (`test_draft_does_not_modify_claude_md_or_agent_md_files`), caused by this ticket's approved
  `CLAUDE.md` edit hitting a leftover `git diff HEAD` guard from an already-closed, unrelated
  ticket. See Implementation Notes.

## Files Changed

New:
- `docs/audits/D25_engine_docs_drift.md`
- `tests/docs/test_kernel_phase_names_consistent.py`
- `tests/docs/test_doc_path_existence.py`

Direct plan-scoped edits:
- `docs/engine/README.md` (lines 13-14, phase-count claims)
- `CLAUDE.md` (line 258 only)
- `docs/engine/architecture.md` (§5 callout box)
- `docs/guides/simulation.md` (line 26, path citation)
- `docs/plans/kernel_concurrency_design_review_proposal.md` (cross-link line)

Additional doc-path-existence fixes (found by the new test, Step 7 execution — see Deviations):
- `docs/architecture/doc_updater_agent.md`
- `docs/engine/authoritative_apply_contract.md`
- `docs/engine/contracts/infrastructure_overview.md`
- `docs/engine/contracts/substrate_baseline_contract.md`
- `docs/engine/contracts/task_result_update_substrate_contract.md`
- `docs/engine/matrices/observability_test_matrix.md`
- `docs/engine/matrices/signal_truth_test_matrix.md`
- `docs/engine/matrices/worker_test_matrix.md`
- `docs/performance/perf_baseline_policy.md`
- `docs/engine/phase13_retirement_manifest.md`

Staging artifacts (this run's own rewrite/additions):
- `staging_artifacts/TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT/plan.md` (added "Deviations" section)

## Completion Summary

Implemented all 10 plan steps: the D25 audit doc (16-doc D17-depth classification, 4
known-contradictions cross-references, parity-ledger gap notes, structural convention +
enforcement mechanism, recommended follow-up), 4 direct doc-drift fixes (README.md, CLAUDE.md:258,
architecture.md callout box, kernel_concurrency_design_review_proposal.md cross-link), and two new
living tests. `test_kernel_phase_names_consistent.py` behaves exactly as planned (1 pass, 1
designed xfail). `test_doc_path_existence.py` deviated from plan: it surfaced 34 real dead path
citations (vs. the 1 anticipated), of which 22 were fixed directly during Implement and 12 were
disclosed and deferred via `xfail(strict=True)` with a concrete itemized backlog now recorded in
the audit doc for a recommended follow-up ticket — this is documented as a Deviation, not a
silently-forced pass. A pre-existing, unrelated test regression
(`test_prescan_mandate_instruction_draft.py`) was also discovered as a side effect of the required
CLAUDE.md edit and flagged, not fixed, since it is outside this ticket's scope. Independently
re-verified by Architecture-Verify (7 of the 22 path fixes spot-checked as real, all scope guards
confirmed) and Parity (no ledger entry needed, SUB-008 gap correctly flagged not fixed).
