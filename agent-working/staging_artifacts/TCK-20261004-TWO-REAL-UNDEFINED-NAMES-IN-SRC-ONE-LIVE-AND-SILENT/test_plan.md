---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT
phase: open
date: 2026-10-04
tags: [engine, social, root-cause, observability]
---

# Test Plan — TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT

## Test Cases
- `tests/unit/engine/test_kernel_provenance_manifest_load.py`: manifest fingerprints come from the provenance file; a corrupt file is logged, not swallowed.
- `tests/unit/social/test_party_issue_command.py`: the command builds a CRITICAL directive.

## Proof Plan
### AC1 / AC2
- **level**: unit (real Kernel construction, real manifest write)
- **proof kind**: regression (fails on old code)
- **oracle source**: `docs/engine/kernel.md`; the run-manifest contract has no parity entry, so `oracle: unresolved` for it
- **expected effect**: `RunManifest.catalog_fingerprint` and `module_fingerprints` equal the provenance file's values; corrupt file produces a warning and `None` fingerprints
- **selected commands**: `pytest tests/unit/engine/test_kernel_provenance_manifest_load.py -q`
### AC4
- **level**: n/a
- **proof kind**: removal
- **oracle source**: `TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD`
- **expected effect**: the method no longer exists; whole-repo grep finds no reference outside historical records
- **selected commands**: `grep -rIn issue_party_command . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=agent-working --exclude-dir=plans`
