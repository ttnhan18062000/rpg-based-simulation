---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2P-RUN-MANIFEST-WORLDID
artifact_type: investigation
tags: [run-manifest, observability, world-id, traceability]
---

# Investigation — Add world_id to RunManifest

## Finding

D08 F5 (Score 4/15): All run manifests record `scenario_name: cli_default` regardless of which world
was used. The world ID (`dungeon_crawl`, `urban_political`, etc.) is not recorded in `run_manifest.json`.
Post-hoc analysis cannot identify the world from the artifact alone.

## RunManifest Definition

**File:** `src/observability/reporting/artifact_repository.py:8–34`

`RunManifest` is a Pydantic BaseModel. Current fields include `run_id`, `scenario_name`, `scenario_type`,
`seed`, `engine_version`, `observability_mode`, `started_at`, `ended_at`, `ticks_requested`,
`ticks_completed`, `status`, `artifact_schema_version`, `failure_reason`, and several world assembly
path/fingerprint fields (`resolved_world_path`, `compile_context_path`, etc.).

No `world_id` field exists.

## Kernel Construction Site

**File:** `src/engine/kernel.py:52–73` (`__init__` signature), `127–172` (manifest creation).

`Kernel.__init__()` already accepts `resolved_world_path`, `compile_context_path`,
`provenance_manifest_path`, `assembly_report_path`, `validation_report_path`, `compile_report_path`,
`runtime_content_source`, `catalog_fingerprint`, `module_fingerprints` — but no `world_id`.

The manifest is constructed at line 152 inside a block guarded by `obs_mode != ObservabilityMode.OFF`.

## world_id Availability at Kernel Call Sites

| Caller | world_id available? | Notes |
|---|---|---|
| `src/cli/entry.py:245` | Yes — `world_id` local variable at line 206 | Not passed to Kernel |
| `src/lab/orchestrator.py:209,222` | Yes — `scenario_spec.world_id` / `world_spec.world_id` at line 115 | Not passed to Kernel |
| `src/perf/bench_harness.py:65` | No obvious world context | Should default to "unknown" |
| `src/perf/long_run_harness.py:158,321,328` | No world context in visible code | Should default to "unknown" |
| `src/certification/harness.py:89,174,300` | No world context | Should default to "unknown" |
| `src/engine/scenario_runtime.py:341` | No world context | Should default to "unknown" |
| `src/observability/sweeper.py:198` | No world context visible | Should default to "unknown" |
| `src/observability/mining/controller.py:225` | No world context visible | Should default to "unknown" |
| `src/api/engine_manager.py:131` | No world context | Should default to "unknown" |
| `src/domains/campaigns/runner.py:93` | No world context visible | Should default to "unknown" |
| `src/engine/scenario_checkpoint.py:103` | No world context visible | Should default to "unknown" |
| `src/observability/readiness/harness.py:105` | No world context | Should default to "unknown" |

## Decision

- Add `world_id: str = "unknown"` to `RunManifest` (default ensures backward compatibility).
- Add `world_id: Optional[str] = None` to `Kernel.__init__()`.
- In manifest construction, set `world_id=world_id or "unknown"`.
- Update CLI entry.py to pass `world_id` string.
- Update lab orchestrator to pass `world_id=scenario_spec.world_id` at both Kernel call sites.
- No other callers need changes — they will produce `world_id: "unknown"` by default.

## Serialization Impact

Pydantic's `model_dump()` and `model_dump_json()` automatically include new fields. No custom
serializer or deserializer changes are required. The `update_manifest()` path in `RunArtifactRepository`
uses `model_validate()` with full round-trip — adding a field with a default handles backward compat
automatically (old manifests without the field parse fine with `world_id="unknown"` default).
