---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION
phase: done
date: 2026-08-17
tags: [documentation, engine]
---

# TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION

## Title
Fix Collection-phase concurrency contradiction in simulation_kernel_contract.md §9

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
docs/engine/kernel.md states Collection is concurrent, while docs/engine/contracts/simulation_kernel_contract.md §9 states "No concurrency or parallel execution." Both are status: active, authority: P1. The actual code (src/engine/worker_manager.py, ThreadPoolExecutor/ProcessPoolExecutor) matches kernel.md's description, not the contract's, and a third P1 doc (bounded_concurrency_contract.md) further confirms concurrency is real and intentional. simulation_kernel_contract.md §9 is the stale outlier and needs correcting to match the other two docs and the code.

## Scope
- Correct simulation_kernel_contract.md §9's "No concurrency or parallel execution" line to a narrower, accurate statement consistent with kernel.md and bounded_concurrency_contract.md (Collection/Deliberation phase concurrency via bounded worker pool is real and intentional)
- Ensure the resulting text still permits src/engine/worker_manager.py's existing ThreadPoolExecutor/ProcessPoolExecutor behavior without calling it a violation
- Update or add the relevant parity ledger entry (docs/parity_ledger/substrate.yaml or infrastructure.yaml) if applicable

## Out of Scope
- The 6-phase vs 7-phase contradiction (separate ticket: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION)
- Landing the kernel concurrency design doc or the broader docs/engine audit (separate tickets)
- Rewriting simulation_kernel_contract.md §9's other bullets ("No scheduler optimization", "No adaptive degradation", "No external event brokers") flagged as possibly-also-stale — deferred to the broader audit ticket (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT)

## Acceptance Criteria
- [x] simulation_kernel_contract.md §9 no longer contains "No concurrency or parallel execution" or an equivalent blanket denial
- [x] kernel.md + simulation_kernel_contract.md + bounded_concurrency_contract.md state a mutually consistent claim: Collection/Deliberation is the sole concurrent phase via bounded worker pool
- [x] Corrected text still permits existing src/engine/worker_manager.py behavior without calling it a violation
- [x] Parity ledger entry (docs/parity_ledger/substrate.yaml or infrastructure.yaml) updated or added if relevant

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC

## Related Docs
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/project_lawbook_m10.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/project_lawbook_m10.md
- src/engine/worker_manager.py
- tests/integration/kernel/test_simulation_kernel_contract.py

## Assumptions / Open Questions
- Don't just delete the §9 line — replace with a narrower accurate statement so a real constraint isn't silently lost
- Overlaps TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION on the same two files (kernel.md, simulation_kernel_contract.md) — coordinate to avoid merge conflicts if worked concurrently; no hard ordering required between the two
- No existing test asserts on §9's literal text — this is a docs-only fix
- docs/engine/manifest.json references this file; not fully verified whether any tooling depends on exact current wording
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC depends on this ticket landing first (see SEQUENCE.md in this folder)

## Implementation Notes
Re-read `docs/engine/contracts/simulation_kernel_contract.md` fresh rather than trusting the
ticket's quoted text (per the ticket's own instruction, given nearby-section churn from sibling
tickets in this batch). The live §9 "Kernel Boundaries" at the time of this fix read exactly:

```
- No scheduler optimization.
- No concurrency or parallel execution.
- No adaptive degradation.
- No external event brokers.
```

Confirmed `kernel.md`'s "⚡ Concurrency & The Resolution Bottleneck" section (`docs/engine/kernel.md:53-56`)
asserts "Concurrent Collection: the Deliberation phase is the only window for parallel execution"
and frames RESOLUTION as "The Singular Bottleneck" — directly contradicting the contract's blanket
denial. Confirmed `docs/engine/contracts/bounded_concurrency_contract.md` (already updated by
sibling ticket TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE with its new §5.1) documents a real,
intentional, profile-controlled bounded worker pool (`WorkerManager`, `src/engine/worker_manager.py`,
`ThreadPoolExecutor`/`ProcessPoolExecutor`) and a Deterministic Commit Law (§3) that RESOLUTION
uses to collapse proposals into one serial, order-independent apply pass. Found `class ConcurrencyLaw`
at `src/core/concurrency_law.py` — it is the frozen `CLASS_PRIORITY` mapping (`CRITICAL`=0,
`PERIODIC`=10, `OPPORTUNISTIC`=20, `DEFERRED`=30) backing that Deterministic Commit Law, confirming
the real constraint §9 was gesturing at was never "concurrency doesn't exist" but "concurrency must
never affect deterministic tick outcome."

Replaced the single bullet `- No concurrency or parallel execution.` in §9 with a narrower, accurate
statement: concurrency is bounded to the COLLECTION phase only (naming `WorkerManager` and its
`ThreadPoolExecutor`/`ProcessPoolExecutor`), every other phase (INIT/SCHEDULING/RESOLUTION/CLEANUP/
ADVANCEMENT/PERSISTENCE) runs synchronously, and RESOLUTION always collapses COLLECTION's proposals
through the single deterministic serial apply order backed by `ConcurrencyLaw`/§3 Deterministic
Commit Law — so concurrent Collection execution never affects tick outcome. Left §9's other three
bullets (scheduler optimization, adaptive degradation, external event brokers) and the 6-phase vs
7-phase contradiction (§4) untouched, per this ticket's explicit Out of Scope.

Added `docs/parity_ledger/infrastructure.yaml` entry `INFRA-366` (status `verified`, priority `P2`,
`proof_type: contract`) recording the contradiction and its fix, citing `WorkerManager`,
`Kernel._phase_collection`/`_phase_resolution`, `ConcurrencyLaw`, and
`bounded_concurrency_contract.md` §3 as `v2_evidence`, and citing
`test_worker_determinism.py::test_concurrency_determinism_equivalence`,
`test_worker_determinism.py::test_race_resistance_via_sorting`, and
`test_simulation_kernel_contract.py::test_authoritative_phase_list` as `test_path`. Verified via
`tools/parity_index.py build` (status `ok`, 2048 entries, 0 `missing_v2_evidence`) and
`tools/parity_index.py entry INFRA-366` (`health_findings: []`).

Deviation from a literal reading of the ticket: because `INFRA-366` was added with a real `test_path`
from the start (not `null`), it moved the live `missing_test_path_count` scanned by
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
from 1336 to 1335. This is the documented, sanctioned baseline-drift pattern that test file's own
comment block already explains (two prior tickets already recorded there caused the same kind of
drift) — updated the hardcoded assertion from `1336` to `1335` and appended a matching comment
entry attributing the drift to this ticket, rather than leaving CI red or silently editing the
assertion without explanation. This was not in the ticket's original Scope/Acceptance Criteria but
is a direct, legitimate, in-scope consequence of Acceptance Criterion 4 (parity ledger entry with
real evidence) and is called out explicitly here rather than silently worked around.

## Test Summary
- `.venv/bin/python3 -m pytest tests/integration/kernel/test_simulation_kernel_contract.py -v` — 2 passed. Confirms the ticket's Assumption held: no test asserts on §9's literal text, so the wording change alone did not need any test change.
- `.venv/bin/python3 -m pytest tests/integration/kernel/test_worker_determinism.py -v` — 2 passed (`test_concurrency_determinism_equivalence`, `test_race_resistance_via_sorting`) — the two tests newly cited as `INFRA-366`'s `test_path`.
- `.venv/bin/python3 -m pytest tests/docs/test_doc_integrity.py tests/integrity/test_doc_guards.py -v` — 9 passed, 1 skipped. Confirms `docs/engine/manifest.json`'s required-header check (`Purpose`, `Kernel Boundaries`) still passes against the edited contract file.
- `.venv/bin/python3 -m pytest tests/tools/test_parity_ledger_schema.py tests/integrity/test_parity_guards.py -v` — 5 passed. Confirms the new `INFRA-366` entry is schema-valid.
- `.venv/bin/python3 tools/parity_index.py build` — `status: ok`, 2048 entries, `missing_v2_evidence: 0`.
- `.venv/bin/python3 tools/parity_index.py entry INFRA-366` — `found: true`, `health_findings: []`.
- `.venv/bin/python3 -m pytest tests/tools/test_parity_index_baseline.py -v` — initially 14 passed / 1 failed (`test_baseline_manifest_does_not_coerce_missing_test_path`, expected `1336` vs live `1335`, the drift explained above); 15 passed after updating the baseline assertion and its comment.
- `.venv/bin/python3 -m pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_writer.py -v` — 53 passed. Confirms the broader parity-index tooling still builds/queries correctly with the new entry present.

## Files Changed
- `docs/engine/contracts/simulation_kernel_contract.md` — §9 "Kernel Boundaries": replaced the blanket "No concurrency or parallel execution." bullet with a narrower, accurate statement naming `WorkerManager`, the COLLECTION-phase bounded pool, and RESOLUTION's deterministic serial commit (`ConcurrencyLaw`).
- `docs/parity_ledger/infrastructure.yaml` — added new entry `INFRA-366` documenting the contradiction and its fix.
- `tests/tools/test_parity_index_baseline.py` — updated `test_baseline_manifest_does_not_coerce_missing_test_path`'s hardcoded live-scan assertion from `1336` to `1335` and its explanatory comment, to reflect `INFRA-366` legitimately shipping with a real `test_path` (documented baseline-drift pattern, not a gate workaround).
- `docs/plans/kernel_concurrency_design_review_proposal.md` — added completion cross-link after C2.
- `tickets/inprogress/TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION.md` — this ticket: Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary.

## Completion Summary
Corrected the stale blanket denial in `simulation_kernel_contract.md` §9 ("No concurrency or
parallel execution") to a narrower, accurate statement that concurrency is bounded to the
COLLECTION phase's profile-controlled worker pool (`WorkerManager`), with every other phase
synchronous and RESOLUTION always collapsing proposals through a single deterministic serial
commit order (`ConcurrencyLaw`) — bringing `kernel.md`, `simulation_kernel_contract.md`, and
`bounded_concurrency_contract.md` into mutual agreement and matching the real
`ThreadPoolExecutor`/`ProcessPoolExecutor` behavior in `src/engine/worker_manager.py`. Added parity
ledger entry `INFRA-366` recording the fix with concrete code/test evidence, and updated one
downstream hardcoded parity-index baseline test whose live-scanned count legitimately shifted as a
direct result. No production code changed; no test asserted on §9's literal wording, so no other
test needed updating.
