---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-INTAKE
artifact_type: test_plan
tags: [architecture, mcp, testing, documentation]
---

# Test plan — TCK-20261002-VISUAL-ASSETS-STORE-INTAKE

## Proof Plan

| Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|
| unit | behaviour of the independent validator, one case per finding code, same findings for MANUAL and CAP_A | the ticket's acceptance list and the Aseprite file-format specification | each defect yields exactly its own code and a clean candidate yields none | `pytest tests/visual_assets/store/unit/test_intake_validator.py` |
| unit | refusal before any byte is copied: symlink (file, directory, entry), extra file, sub-directory, oversize, FIFO, hard link, missing; no quarantine directory left; FIFO never opened | the ticket's acceptance list | `StageError` with its code, producer directory unchanged | `pytest tests/visual_assets/store/unit/test_quarantine.py` |
| unit | idempotent re-submission, no overwrite, conflicting re-submission, partial-stage cleanup, review gates, write confinement | the ticket's acceptance list | tracked catalog and workspace byte-identical; only patched quarantine and review roots written | `pytest tests/visual_assets/store/unit/test_intake_service.py test_cli.py` |
| unit | contract additions (`producer_state`, `candidate_id` UNAVAILABLE both ways, 1-based counts, finding-code set) | agreed contract changes | strict parse rejects every violation | `pytest tests/visual_assets/store/unit/test_records.py` |
| integration (needs Aseprite) | parser vs real Aseprite on drawing-tool revisions, growing-sprite revisions, 14 palette setups; builder files open in real Aseprite; real revision plus real preview pass intake | real Aseprite 1.3.18.6 | parser facts equal Aseprite's own report; unverifiable palettes refused, never guessed | `pytest tests/visual_assets/store/integration` |
| mutation | 21 hand-applied mutants of the new guards | n/a | each fails the intended test (two initial survivors fixed with new tests) | scratch script (not committed) |
| architecture | store layering rows for `intake`, `cli`, `__main__`; planted violations | `STORE_ALLOWED` | boundary test green | `pytest tests/visual_assets/test_boundaries.py` |
| unit/integration (drawing side, after the ops.lua commit) | `build_handoff` idempotence, provenance from what the tools know, tool count 16, no gate tool | the ticket's acceptance list | handoff passes intake end to end | `pytest tests/visual_assets/drawing` |
