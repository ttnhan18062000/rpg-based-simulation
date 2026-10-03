---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION
artifact_type: test_plan
tags: [architecture, mcp, testing, documentation]
---

# Test plan — TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION

## Proof Plan

| Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|
| unit | adopt happy path: exactly the four files, strict records, hashes agree; second adoption gives r0002 with parent r0001 and r0001 untouched | ticket acceptance list | records parse; bytes hash to the recorded value | `pytest tests/visual_assets/store/unit/test_adoption.py` |
| unit | every refusal has its own code and leaves the catalog tree byte-identical | ticket scope item 1 | `GateError` code, no write | same |
| unit | failure injected at every position of the publish leaves the tree byte-identical (files and new directories) | ticket acceptance list | rollback complete | `pytest tests/visual_assets/store/unit/test_catalogwrite.py` |
| unit | revoke, `is_build_eligible`, later adopt refused, revoked files still present | ticket acceptance list | eligibility false, nothing deleted | `pytest tests/visual_assets/store/unit/test_revoke.py` |
| unit | `audit_chain` passes a fresh tree and names the specific break per planted tamper | ticket acceptance list | one break code per tamper | `pytest tests/visual_assets/store/unit/test_audit.py` |
| unit | CLI gate: non-zero without a terminal or `--approver`; typed id confirms | ticket acceptance list | exit codes | `pytest tests/visual_assets/store/unit/test_cli_gates.py` |
| architecture | drawing never imports adoption/revoke; new layer rows | `STORE_ALLOWED`, planted violations | boundary test green | `pytest tests/visual_assets/test_boundaries.py` |
| mutation | hand-applied mutants of the new guards | n/a | each fails the intended test | scratch script (not committed) |
