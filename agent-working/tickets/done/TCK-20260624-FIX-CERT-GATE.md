---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-CERT-GATE
phase: done
date: 2026-06-24
tags: [certification, release-gate, domain-registry, logic-checklist]
---

# TCK-20260624-FIX-CERT-GATE

## Title
Fix release gate failure — register CERT domain or rename RPG-CERT-001/002 in logic checklist

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/certification/test_final_gate.py::test_real_release_proof_is_valid` fails with `M10 Gate Failure`. Investigation shows `reports/release_proof/` exists and contains the proof artifact. The failure is in `scripts/release_gate.py` which validates `docs/logic_checklist_exhaustive.md` and finds two IDs with an unregistered domain prefix:

- `RPG-CERT-001` (line ~3189)
- `RPG-CERT-002` (line ~3190)

The domain `CERT` is not registered in `release_gate.py`'s valid-domain list. The script exits 1, and the test treats exit 1 as a gate failure.

This is independent of the long-run certification tests — they write to `reports/certification/`, not `reports/release_proof/`.

## Scope
Either:
- **(A)** Register `CERT` as a valid domain in `scripts/release_gate.py` — preferred if `RPG-CERT-*` IDs are intentional and represent a real certification subsystem
- **(B)** Rename `RPG-CERT-001` and `RPG-CERT-002` in `docs/logic_checklist_exhaustive.md` to use an already-registered domain (e.g., `RPG-INFRA-xxx` numbering)

Also fix the 3 warnings for missing test paths (`RPG-INFRA-155`, `RPG-INFRA-156`, `RPG-INFRA-157`) — either add test paths or mark them as `N/A`.

## Out of Scope
- Changing what the release gate validates beyond the domain and missing-path issues
- Running the long-run certification tests

## Acceptance Criteria
- `test_real_release_proof_is_valid` passes
- `scripts/release_gate.py` exits 0 on the current `docs/logic_checklist_exhaustive.md`
- No CRITICAL ERRORs in gate output

## Related Tickets
None

## Related Docs
- `docs/logic_checklist_exhaustive.md` — lines ~3189–3190
- `scripts/release_gate.py` — valid domain list

## Related Code Areas
- `scripts/release_gate.py` — domain validation logic and valid-domain list
- `docs/logic_checklist_exhaustive.md:3189–3190` — `RPG-CERT-001`, `RPG-CERT-002`
- `tests/certification/test_final_gate.py` — invokes `release_gate.py` and checks exit code

## Assumptions / Open Questions
- Determine if `CERT` was intended as a permanent domain for certification-specific checklist items, or if it was a typo/naming inconsistency
- If option A: add `CERT` to the valid-domain list alongside existing domains
- For the 3 missing test path warnings: check whether the corresponding features have tests — if yes, add the path; if no, mark as `N/A` or `"pending"`

## Implementation Notes
Option A (preferred):
```python
# In scripts/release_gate.py, valid_domains set:
VALID_DOMAINS = {"CORE", "COMBAT", "ECON", "STRAT", "WORLD", "INFRA", "CERT"}  # add CERT
```

Option B (rename):
```
# In docs/logic_checklist_exhaustive.md lines 3189-3190:
- RPG-CERT-001 → RPG-INFRA-158
- RPG-CERT-002 → RPG-INFRA-159
```

For missing test paths (RPG-INFRA-155/156/157):
```
test_path: "N/A"  # or add the actual test file path
```

## Test Summary
Run: `python3 scripts/release_gate.py && pytest tests/certification/test_final_gate.py::test_real_release_proof_is_valid -v`

## Files Changed
- `scripts/ledger_validator.py` — Added `"CERT"` to DOMAINS set; fixed path existence check to strip `::function` pytest node ID suffixes before calling `os.path.exists()`
- `reports/release_proof/` — Generated proof artifacts (release_report.md, manifest_snapshot.json, proofs_bundle.json) via `scripts/generate_release_proof.py`

## Completion Summary
Added `CERT` to the approved domain set in `scripts/ledger_validator.py` (Option A). Root cause of INFRA-155/156/157 warnings was that the validator called `os.path.exists()` on full pytest node IDs (e.g. `tests/arch/file.py::test_func`) which always fail — fixed by stripping `::` suffix before the existence check. Generated the missing release proof bundle. Gate exits 0 and `test_real_release_proof_is_valid` passes.
