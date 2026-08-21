---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION
artifact_type: investigation
tags: [documentation, engine]
---

# Investigation — TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION

## Current Behavior

### `src/engine/kernel.py::Kernel.tick_once` (real ground truth)
`tick_once()` (line 343) delegates to `_tick_once_inner()` (line 360), which calls exactly 7 `_phase_*`
methods in this order:

1. `_phase_init()` (line 364, method body line 499)
2. `_phase_scheduling()` (line 379, method body line 559)
3. `_phase_collection()` (line 388, method body line 563)
4. `_phase_resolution()` (line 397, method body line 575)
5. `_phase_cleanup()` (line 403, method body line 681)
6. `_phase_advancement()` (line 407, method body line 713) — internally also invokes
   `_phase_observability()` (line 736) as a sub-step, not a separate top-level `tick_once` phase
7. `_phase_persistence()` (line 426, method body line 1059)

This exactly matches the ticket's claimed real phase list (INIT, SCHEDULING, COLLECTION, RESOLUTION,
CLEANUP, ADVANCEMENT, PERSISTENCE) — confirmed, not merely trusted.

There is also a formal `TickPhase` enum in `src/engine/phases.py` (all 7 values, `IntEnum`, "FROZEN /
Phase 4 Milestone 1"), and `get_authoritative_phases()` (same file) returns exactly 6 of them —
INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT — explicitly excluding PERSISTENCE,
which the enum comments as a "Non-authoritative hook (must not influence authoritative state)". This
is the code-level source of truth behind the "6 authoritative + 1 non-authoritative hook" framing
found in `substrate_baseline_contract.md` §4 (see below) — it is not stale doc language, it is a
real, tested, currently-enforced distinction (`tests/integration/kernel/test_simulation_kernel_contract.py::test_authoritative_phase_list`
asserts `get_authoritative_phases() == [INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT]`).

### `docs/engine/architecture.md` §2 (lines 45–61) — STILL FABRICATED, confirmed
Heading: "## 2. The 6-Phase Deterministic Kernel Loop" (line 45), body: "Every tick executes exactly
six phases in a strict, contract-enforced sequence." (line 47). The phase table (lines 51–58):

| # | Name (as written) |
|---|---|
| 1 | INIT |
| 2 | **GOVERNANCE** — fabricated, not a real `_phase_*` method |
| 3 | SCHEDULING |
| 4 | **PACKETIZATION** — fabricated, not a real `_phase_*` method |
| 5 | RESOLUTION |
| 6 | PERSISTENCE |

Missing entirely: COLLECTION, CLEANUP, ADVANCEMENT. This is the only remaining occurrence of
GOVERNANCE/PACKETIZATION as fabricated phase-table entries inside `docs/engine/architecture.md`
(grep confirms lines 54 and 56 only). "Phase Governance" (line 61, section heading, describes the
PhaseContract runtime-integrity mechanism) is a legitimate, unrelated use of the word "Governance"
and must not be touched.

### `docs/engine/README.md` — confirmed clean (already fixed by TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT)
Direct re-grep (`grep -n "GOVERNANCE\|PACKETIZATION\|Governance\|Packetization" docs/engine/README.md`)
returns zero matches, any casing. Its "Core Loop" bullet (line 13) already reads: "The 7-phase
orchestrator (Init, Scheduling, Collection, Resolution, Cleanup, Advancement, Persistence)." No
action needed on this file — the ticket's own AC #2 is already satisfied.

### `docs/engine/kernel.md` and `docs/engine/contracts/simulation_kernel_contract.md` — already clean
Both already state the correct 7-phase list with no GOVERNANCE/PACKETIZATION occurrences (zero grep
hits in either file). `kernel.md` additionally carries a "Phase Domain Permissions" table (lines
144–158) listing all 7 phases including PERSISTENCE tagged `_(non-authoritative)_`, and a note (line
160) cross-referencing `simulation_kernel_contract.md` §7.1 for RNG-consumer tracing — both already
internally consistent with the 7-phase framing.

### **GAP NOT IN TICKET SCOPE — `docs/guides/simulation.md` still carries the identical fabricated text**
Lines 19–20:
> "Every simulation run is a deterministic 6-phase loop (Init → Governance → Scheduling →
> Packetization → Resolution → Persistence) repeated per tick."

And line 25: "`src/engine/kernel.py` — the 6-phase loop" (also wrong: should be 7-phase). Line 26
additionally claims "`src/engine/pipeline.py` — the 17-phase mutation sequence", which conflicts with
`docs/engine/README.md`'s own "37-phase refinement sequence" claim for `authoritative_pipeline.md` —
this second number mismatch (17 vs 37) is a **separate, pre-existing contradiction**, out of this
ticket's scope (not a phase-name issue), noted here only as an anti-drift hazard, not something to
fix under this ticket.

This file is **not listed anywhere** in the ticket's Scope, Related Docs, Related Code Areas, or
Acceptance Criteria — see Risks and Open Questions below; this blocks a clean AC #3/xfail-removal
close as scoped.

### `docs/engine/contracts/substrate_baseline_contract.md` §4 "Kernel Orchestration Law" (lines 26–37)
States: "The `Kernel` MUST execute the following 6 phases in strict sequential order" and lists INIT,
SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT (6 items, matches `get_authoritative_phases()`
exactly), then a separate "### Observational Boundary" subsection (lines 36–37) describing PERSISTENCE
and "all other hooks" as non-authoritative, executing "after the tick is logically sealed at the
ADVANCEMENT phase." This is internally consistent and, per the code-level `TickPhase`/`get_authoritative_phases()`
split above, factually accurate — not itself wrong, just not explicitly cross-referenced against the
"7 phases" language used elsewhere (kernel.md, README.md, this ticket). AC #4 asks only for an
explicit clarifying note here, not a rewrite of the 6-phase framing itself.

### `tests/integration/kernel/test_milestone_a_closure.py`
`test_final_kernel_law_compliance` (line 60) asserts exactly the 6 `mandated_phases` (`_phase_init`
through `_phase_advancement`, no `_phase_persistence`) are present on `Kernel` and appear in
`_tick_once_inner`'s source — this is the **same** 6-authoritative-phase convention as
`get_authoritative_phases()`/`substrate_baseline_contract.md` §4, already internally consistent, and
correctly out of this ticket's scope per the ticket's own "Out of Scope" section — no changes needed
here, confirmed.

### `tests/docs/test_kernel_phase_names_consistent.py` (added by TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT)
Two tests:
- `test_no_fabricated_phase_names_in_kernel_docs` — currently `@pytest.mark.xfail(strict=True, ...)`,
  citing this ticket by name. Iterates `PHASE_NARRATING_DOCS = ["docs/engine/kernel.md",
  "docs/engine/architecture.md", "docs/engine/README.md",
  "docs/engine/contracts/simulation_kernel_contract.md", "docs/guides/simulation.md", "CLAUDE.md"]`
  and asserts none contain `"GOVERNANCE"` (case-sensitive) or `"packetization"` (case-insensitive,
  i.e. also catches Title-Case "Packetization").
- `test_kernel_doc_states_all_seven_real_phases` — asserts `kernel.md` names all 7 real phases; not
  xfail-marked, already passes today (kernel.md is already correct).

**Critical consequence for AC/closure**: `test_no_fabricated_phase_names_in_kernel_docs` checks
`docs/guides/simulation.md`, which still fails the check today (confirmed: "Packetization" present,
case-insensitive match). If this ticket fixes only `architecture.md` (its stated scope) and removes
the `xfail` marker per the dispatch instructions, the test will **fail for real** (not the strict-xfail
XPASS the marker is designed to catch — just a normal `AssertionError` on the `docs/guides/simulation.md`
iteration), because that file was never in scope. Fixing `docs/guides/simulation.md`'s 6-phase
sentence (lines 19–20, 25) is required for the xfail-removal step to actually produce a passing test,
even though the ticket body never names this file. See Risks and Open Questions.

## Mechanics / Engine Constraints
This is a documentation-only fix; no simulation law, formula, or mutation-pipeline behavior changes.
The relevant constraint is `docs/engine/kernel.md`'s own "Law of Ticks" framing and the
`substrate_baseline_contract.md` §4 "Kernel Orchestration Law" — both of which this ticket must keep
internally consistent, not alter the substance of. `src/engine/phases.py`'s `TickPhase` enum is
documented "FROZEN (Resource Phase 4 Milestone 1)" — this ticket must not touch the enum or
`get_authoritative_phases()`, only reconcile the docs against it.

## Docs Requiring Update
- `docs/engine/architecture.md`: §2's phase table (lines 51–58) still lists fabricated GOVERNANCE
  (row 2) and PACKETIZATION (row 4) instead of the real COLLECTION/CLEANUP/ADVANCEMENT phases;
  heading/prose ("6-Phase", "exactly six phases") must also become 7-phase language.
- `docs/guides/simulation.md`: lines 19–20 carry the identical fabricated "Init → Governance →
  Scheduling → Packetization → Resolution → Persistence" 6-phase sentence, and line 25 says "the
  6-phase loop" — not listed in the ticket's own Scope/Related Docs but required for
  `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs`
  (which explicitly checks this file) to pass once its `xfail` marker is removed, per the dispatch
  instructions. Flagged as a scope gap — see Risks and Open Questions; do not silently expand scope
  without a decision on how to record it.
- `docs/engine/contracts/substrate_baseline_contract.md`: §4 needs one added clarifying note (not a
  rewrite) stating the "6 authoritative phases" framing is the code-verified authoritative-only
  subset (`src/engine/phases.py::get_authoritative_phases()`), with PERSISTENCE as the 7th,
  non-authoritative phase — equivalent to, not contradicting, the 7-phase numbering used in
  kernel.md/README.md/architecture.md.
- `docs/parity_ledger/infrastructure.yaml`: no existing entry documents the architecture.md/README.md
  phase-count correction itself (INFRA-366 is the sibling concurrency-contradiction ticket's entry
  and only mentions this ticket in its `support_boundary` as deferred work). Per the Authoritative
  Mechanics Rule ("If logic changes, update... the parity ledger entry in the same session") and the
  precedent INFRA-366 set (a doc-only correction ticket added its own ledger entry), this ticket
  should add a new entry recording the architecture.md/kernel.md phase-count reconciliation, evidenced
  by `src/engine/kernel.py::tick_once`/`_tick_once_inner` and `src/engine/phases.py`, with
  `test_path` pointing at `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs`
  and `tests/integration/kernel/test_simulation_kernel_contract.py::test_authoritative_phase_list`.

## Parity Ledger Overlap
- `docs/parity_ledger/infrastructure.yaml` INFRA-366 (status: `verified`, priority: P2) — the sibling
  concurrency-contradiction ticket's entry (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION, already
  closed). Its `support_boundary` explicitly excludes "the 6-phase vs 7-phase contradiction
  (TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION)" — i.e. it deliberately did not cover this ticket's
  scope. Its `test_path` includes `tests/integration/kernel/test_simulation_kernel_contract.py::test_authoritative_phase_list`,
  which already passes and is unaffected by this ticket. No P0 entries found touching this ticket's
  scope; nothing here blocks closure, but a new entry should be added per "Docs Requiring Update"
  above.

## Prior Work
- `stored_artifacts/TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT/` — the ticket that discovered this
  contradiction, fixed `docs/engine/README.md`, and added the xfail-guarded living test this ticket
  must flip to a real pass. Its plan explicitly deferred the architecture.md fix to this ticket
  (Design Decision referenced in the dispatch prompt).
- `tickets/done/TCK-20260623-FIX-KERNEL-PHASES.md` — an earlier (2026-06-23) instance of the exact
  same fabricated "Init → Governance → Scheduling → Packetization → Resolution → Persistence" text,
  that time quoted from `docs/engine/kernel.md` itself (since fixed) as the root cause of a
  `test_final_kernel_law_compliance`/Milestone B/C/D closure-test failure caused by a missing
  `_phase_init` call. Confirms this exact fabricated phrase has independently drifted back into the
  docs at least three times (kernel.md in June, then architecture.md/README.md/CLAUDE.md/
  docs/guides/simulation.md discovered by AUDIT-ENGINE-DOCS-DRIFT in August) — the living-test
  approach this ticket closes out is the first attempt at a structural (not one-off) fix for that
  drift pattern.
- `tickets/done/TCK-20260619-P0-DOC-REPAIR.md` — the first fix of `kernel.md`'s conflicting phase
  tables (per `docs/audits/D17_documentation_currency.md` Finding 2), the direct predecessor of the
  repeat-drift pattern above.

## Risks and Open Questions
- **BLOCKING for a clean xfail-marker removal**: `docs/guides/simulation.md` (lines 19–20, 25) still
  contains the exact fabricated phase text and is explicitly checked by
  `test_no_fabricated_phase_names_in_kernel_docs`, but is absent from this ticket's Scope/Related
  Docs/Acceptance Criteria. Two options, not resolved here — Plan must pick one and record it: (a)
  treat this as within-ticket scope creep that is nonetheless required to satisfy the ticket's own AC
  (the xfail-removal instruction), and fix `docs/guides/simulation.md` alongside architecture.md,
  documenting the scope addition in Implementation Notes; or (b) leave `docs/guides/simulation.md`
  unfixed and leave the `xfail` marker in place, reporting the AC as not fully achievable within
  stated scope and flagging a new hotfix/follow-up ticket. Given the ticket's own dispatch context
  says the test "should flip from XFAIL to a real PASS" upon this ticket's closure, and the marker
  citation only names this ticket (and the already-closed concurrency ticket) as blockers, option (a)
  is the only path that satisfies the actual intent — recommend Plan adopt it and note the ticket
  body under-scoped this file.
- The 17-phase vs 37-phase mutation-pipeline-count mismatch (`docs/guides/simulation.md` line 26 vs
  `docs/engine/README.md` line 14) is a distinct, pre-existing contradiction not in this ticket's
  scope (it's a pipeline-phase count, not a kernel-tick-phase count) — do not fix it under this
  ticket; flag separately if not already tracked.
- `docs/systems/ai_system.md` no longer exists at that path — it was archived to
  `docs/archive/systems/ai_system.md` (confirmed via `find`), consistent with the ticket's Out of
  Scope note that TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT already handled it. The archived
  copy still contains GOVERNANCE/PACKETIZATION text (grep hit), but archived docs are not
  phase-narrating living docs and are correctly excluded from `PHASE_NARRATING_DOCS` — no action
  needed.

## Anti-Drift Hazards
- Do not touch `docs/engine/architecture.md`'s "### Phase Governance" section heading (line 61) or
  "Governor"/"GovernorPolicy" references elsewhere in the file — only the two table rows (GOVERNANCE,
  PACKETIZATION) and the "6-Phase"/"six phases" framing language are in scope.
- Do not touch `tests/integration/kernel/test_milestone_a_closure.py`'s 6-phase docstring/assertions
  (explicit Out of Scope) — its 6-mandated-phase list is a different, legitimate convention
  (authoritative-only, matching `get_authoritative_phases()`), not a bug.
- Do not rewrite `substrate_baseline_contract.md` §4's "MUST execute the following 6 phases" language
  itself — it is correct and code-verified; only add a clarifying cross-reference note, per AC #4's
  literal wording ("explicitly notes... is equivalent to (not contradicting)").
- `CLAUDE.md` line 261 ("`governance_logic.md` | Governance and eligibility rules") is a legitimate,
  unrelated table entry describing a real contract file — do not flag or "fix" it; the living test's
  case-sensitive `"GOVERNANCE"` check and case-insensitive `"packetization"` check correctly do not
  match it today (confirmed via grep), and it must stay that way.
- Any fix to `docs/guides/simulation.md` (if adopted per the Risks section) must be minimal — only
  the phase-name/phase-count sentence, not the surrounding CLI/world-authoring guide content, and
  must not attempt to also fix the unrelated 17-vs-37 pipeline-count mismatch on the adjacent line.
