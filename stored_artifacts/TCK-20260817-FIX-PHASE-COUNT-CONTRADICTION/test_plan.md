---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION
artifact_type: test_plan
tags: [documentation, engine]
---

# Test Plan — TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION

## Regression Surface
This is a docs-only fix (no `src/` changes); the surface below exists to prove nothing else was
disturbed and that all kernel-phase-count-related tests keep passing.

**Unit / architecture guard**
- `tests/integration/kernel/test_simulation_kernel_contract.py::test_authoritative_phase_list` —
  asserts `get_authoritative_phases()` still returns the frozen 6-item list; must be untouched.
- `tests/integration/kernel/test_simulation_kernel_contract.py::test_kernel_tick_execution_order` —
  runs a real `tick_once()`; must be untouched.
- `tests/integration/kernel/test_milestone_a_closure.py::test_final_kernel_law_compliance` — asserts
  the 6 mandated `_phase_*` methods (no PERSISTENCE) exist and are orchestrated; explicit Out of
  Scope, must not change or need changing.
- `tests/integration/kernel/test_milestone_a_closure.py::test_closure_no_placeholders`,
  `test_milestone_a_structural_compliance`, `test_milestone_a_baseline_isolation` — unaffected by a
  docs-only change; run to confirm no accidental collateral damage.
- `tests/docs/test_kernel_phase_names_consistent.py::test_kernel_doc_states_all_seven_real_phases` —
  already passing (kernel.md untouched by this ticket); must remain passing.

**Docs / living-test (the ticket's actual target)**
- `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs` —
  currently `xfail(strict=True)`; this ticket's core deliverable is making this pass for real with
  the marker removed.

## New Tests Required
No new test files are required — the living test added by TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT
(`tests/docs/test_kernel_phase_names_consistent.py`) already encodes the exact assertion this ticket
must satisfy. The only test-code change in scope is removing the `@pytest.mark.xfail(...)` decorator
from `test_no_fabricated_phase_names_in_kernel_docs` (lines 27–35) once the underlying docs are fixed.

- Test name: `test_no_fabricated_phase_names_in_kernel_docs` (existing, unmodified assertions)
- Category: architecture guard / living doc-consistency test
- What it verifies: none of `docs/engine/kernel.md`, `docs/engine/architecture.md`,
  `docs/engine/README.md`, `docs/engine/contracts/simulation_kernel_contract.md`,
  `docs/guides/simulation.md`, or `CLAUDE.md` contain `"GOVERNANCE"` (case-sensitive) or
  `"packetization"` (case-insensitive) anywhere in their text.
- Where it lives: `tests/docs/test_kernel_phase_names_consistent.py` (already exists — action here is
  marker removal only, contingent on the scope decision in investigation.md's Risks section: if
  `docs/guides/simulation.md` is fixed alongside `architecture.md`, the marker removal is safe; if
  not, the marker must stay and the AC must be reported as partially blocked rather than the marker
  removed prematurely — removing it while the assertion still fails would just be a normal test
  failure, not a gate to route around, and per CLAUDE.md's Hard Rules must be reported truthfully,
  not "fixed" by re-adding a marker or altering the assertion).

## Scoped Pytest Commands
```
# Core docs-consistency living test (the ticket's real target)
pytest tests/docs/test_kernel_phase_names_consistent.py -v

# Kernel phase-contract regression surface (architecture guards + contract tests)
pytest tests/integration/kernel/test_simulation_kernel_contract.py tests/integration/kernel/test_milestone_a_closure.py -v
```
Do not run `pytest tests/` — scope is docs + the two kernel-phase test files above.

## Anti-Drift Test Guards
- `test_authoritative_phase_list` and `test_final_kernel_law_compliance` together guard against this
  ticket accidentally "fixing" the 6-phase vs 7-phase language by editing the *code* (`TickPhase`,
  `get_authoritative_phases()`, or the mandated `_phase_*` list) instead of the docs — both must
  stay green with zero diff to `src/engine/phases.py` or `src/engine/kernel.py`.
- `test_kernel_doc_states_all_seven_real_phases` guards against an over-correction that removes a
  real phase name from `kernel.md` while fixing unrelated files.
- Re-running the full `PHASE_NARRATING_DOCS` loop in `test_no_fabricated_phase_names_in_kernel_docs`
  (rather than spot-checking only `architecture.md`) guards against declaring victory while
  `docs/guides/simulation.md` (or a reintroduced occurrence in `kernel.md`/README.md/
  simulation_kernel_contract.md/CLAUDE.md) is still fabricated — this is the exact repeat-drift
  pattern flagged in investigation.md's Prior Work section (three independent recurrences of the
  same fabricated phrase since June 2026).
- A manual grep re-check (`grep -rn "GOVERNANCE\|PACKETIZATION" docs/engine/` returning zero matches,
  and a case-insensitive `packetization` grep across the six `PHASE_NARRATING_DOCS` paths) should be
  run as a final human-readable cross-check alongside the pytest run, per the ticket's own AC #3
  ("grep for 'PACKETIZATION'/'GOVERNANCE' as phase names returns zero matches across docs/engine/").
