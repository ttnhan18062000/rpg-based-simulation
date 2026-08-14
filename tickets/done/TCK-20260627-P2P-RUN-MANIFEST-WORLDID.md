---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2P-RUN-MANIFEST-WORLDID
phase: done
date: 2026-06-27
tags: [run-manifest, traceability, observability, world-id]
---

# TCK-20260627-P2P-RUN-MANIFEST-WORLDID

## Title
Add world_id field to run_manifest.json for run traceability

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
D08 F5 found that all run manifests record `scenario_name: cli_default` regardless of which world was used. The world ID (dungeon_crawl, urban_political, etc.) is not recorded in `run_manifest.json`. Post-hoc analysis of stored run artifacts cannot identify the world from the artifact alone without external bookkeeping. Source: D08 F5 (Score 4/15).

## Scope
Add a `world_id: str` field to the `RunManifest` dataclass, populated at kernel initialization from the world spec's ID. Set to `"unknown"` if no world spec is provided (cli_default mode).

## Out of Scope
- Changing any other field in the manifest
- Changing how scenario_name is populated

## Acceptance Criteria
- [x] `run_manifest.json` contains a `world_id` field after every run
- [x] `world_id` matches the world composition ID used (e.g. `"dungeon_crawl"`, `"urban_political"`)
- [x] `world_id: "unknown"` in cli_default runs where no world spec is passed
- [x] Existing manifest-parsing tests pass without change

## Related Tickets
- N/A

## Related Docs
- `docs/audits/D08_multi_scenario.md` F5

## Related Stored Artifacts
- `stored_artifacts/TCK-20260627-P2P-RUN-MANIFEST-WORLDID/`

## Related Code Areas
- `src/observability/reporting/artifact_repository.py` (RunManifest definition)
- `src/engine/kernel.py:52–73,151–172` (Kernel.__init__ signature + manifest construction)
- `src/cli/entry.py:245` (Kernel call site in CLI)
- `src/lab/orchestrator.py:209,222` (Kernel call sites in lab orchestrator)

## Assumptions / Open Questions
- Resolved: `world_id` is passed as a new optional `str` parameter to `Kernel.__init__()`. CLI and lab
  orchestrator supply it; all other callers default to `"unknown"`.

## Implementation Notes
- Added `world_id: str = "unknown"` to `RunManifest` (Pydantic BaseModel) in
  `src/observability/reporting/artifact_repository.py`. Default ensures backward compat — old manifests
  without the field parse cleanly via model_validate.
- Added `world_id: Optional[str] = None` parameter to `Kernel.__init__()`.
- In manifest construction block (kernel.py), set `world_id=world_id or "unknown"`.
- Updated `src/cli/entry.py` to pass `world_id=world_id` (local var already present at line 206).
- Updated `src/lab/orchestrator.py` both Kernel call sites to pass `world_id=scenario_spec.world_id`.
- No custom serializer changes needed — Pydantic handles field inclusion automatically.

## Test Summary
- 3 new unit tests added to `tests/unit/observability/test_run_artifact_repository.py`:
  - `test_run_manifest_world_id_default` — default serializes to "unknown"
  - `test_run_manifest_world_id_explicit` — explicit value round-trips
  - `test_manifest_world_id_persists_via_repo` — write/read via repository
- Full manifest test suite: 75 passed, 1 skipped, 0 failures
- Parity ledger: INFRA-230 added to `docs/parity_ledger/infrastructure.yaml`

## Files Changed
- `src/observability/reporting/artifact_repository.py` — added `world_id: str = "unknown"` to RunManifest
- `src/engine/kernel.py` — added `world_id` param; used in manifest construction
- `src/cli/entry.py` — pass `world_id` to Kernel
- `src/lab/orchestrator.py` — pass `world_id=scenario_spec.world_id` at both Kernel call sites
- `tests/unit/observability/test_run_artifact_repository.py` — 3 new tests
- `docs/parity_ledger/infrastructure.yaml` — INFRA-230 added

## Completion Summary
D08 F5 resolved. `RunManifest` now carries a `world_id: str` field (default `"unknown"`).
The CLI and lab orchestrator supply the actual world ID at Kernel construction time. All other
Kernel call sites produce `"unknown"` safely. 75 manifest tests pass, 3 new tests green.
Parity ledger updated (INFRA-230, verified, P2).
