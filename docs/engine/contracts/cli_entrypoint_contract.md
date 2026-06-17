---
status: active
layer: engine
authority: P1
audience: developer
---

# CLI & Entrypoint Compatibility Contract

This document defines the supported system-entry surface for the engine.

## 1. Unified Entrypoint
- **Command**: `python3 -m src`
- **Default Behavior**: Displays a placeholder for the `serve` mode. Full REST/WebSocket parity not yet implemented.

## 2. Subcommands
| Subcommand | Status | Purpose |
| :--- | :--- | :--- |
| `cli` | **SUPPORTED** | Headless simulation mode. |
| `serve` | **PARTIAL** | Placeholder for FastAPI server. |
| `inspect` | **PARTIAL** | Placeholder for entity inspection. |

## 3. Supported Arguments (`cli` mode)
| Argument | Type | Default | Parity Status |
| :--- | :--- | :--- | :--- |
| `--seed` | `int` | `42` | **FULL**. Drives both RNG and World setup. |
| `--entities` | `int` | `10` | **FULL**. Sets initial population size. |
| `--ticks` | `int` | `100` | **FULL**. Sets simulation duration. |
| `--workers` | `int` | `4` | **FULL**. Maps to `max_worker_count` in profile. |
| `--replay` | `str` | `None` | **DIVERGENT**. Uses a directory instead of a single file. |
| `--log-level` | `str` | `INFO` | **FULL**. Supports DEBUG, INFO, WARNING, ERROR. |

## 4. Execution Mode Compatibility
- **Headless**: Default for `cli` subcommand.
- **Concurrent**: Enabled via `--workers > 0`.
- **Deterministic**: Guaranteed for identical `--seed` and `--entities`.

## 5. Startup & Shutdown Semantics
- **Startup**: Registry-less initialization. Scenario generation logic is native to `src.systems.generator`.
- **Shutdown**: Clean finalization of `Kernel` and `ReplayManager`. Produces `manifest.json` in the replay directory.

## 6. Known Divergences
- **Replay Format**: Produces JSON-L chunks and a manifest in a directory, whereas legacy produced a single JSON file.
- **Grid Configuration**: `--grid-width/height` are currently handled via internal defaults (128x128) in the generator, as the engine uses a sparse tile mapping instead of a fixed array.
