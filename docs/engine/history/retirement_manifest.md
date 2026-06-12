---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 13 Retirement Manifest

## Purpose
This document identifies all legacy assets slated for permanent deletion in Phase 13.

## 1. Core Logic & Engine
These directories contain the original procedural simulation logic that has been fully replaced by the functional, domain-isolated `src` architecture.

| Path | Description | Replacement |
| :--- | :--- | :--- |
| `src/core/` | Legacy RPG entities and logic. | `src/core/` |
| `src/engine/` | Legacy world loop and resolver. | `src/engine/` |
| `src/workers/` | Legacy worker implementations. | `src/workers/` |
| `src/logging/` | Legacy formatting logic. | `src/logging/` |

## 2. API & Infrastructure
Legacy endpoints and platform wrappers that have been superseded by the V2 API and CLI layers.

| Path | Description | Replacement |
| :--- | :--- | :--- |
| `src/api/` | Legacy REST/WS endpoints. | `src/api/` |
| `src/platform/` | Legacy config and platform shims. | `src/platform/` |
| `src/broker/` | Legacy message broker logic. | `src/engine/worker_manager.py` |

## 3. Legacy Verification Suite
The entire legacy test suite is slated for removal. `tests/` is now the sole authority for project verification.

| Path | Description | Status |
| :--- | :--- | :--- |
| `tests/` | All legacy unit, integration, and scenario tests. | DEPRECATED |

## 4. Operational Assets
Legacy scripts and configuration files that are no longer compatible with the V2 runtime.

| Path | Description | Replacement |
| :--- | :--- | :--- |
| `scripts/profile_simulation.py` | Legacy profiling script. | `src/cli/entry.py` |
| `config/legacy_defaults.yaml` | Legacy configuration defaults. | `src/config/` |

## Retirement Protocol
1. **Phase 12 (Current)**: Mark all assets as DEPRECATED.
2. **Phase 13 (Next)**: Execute `rm -rf` on the identified paths.
3. **Phase 13**: Refactor `src/` to `src/` to restore canonical directory naming.
