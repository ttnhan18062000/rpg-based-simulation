# V2 CLI & Entrypoint Compatibility Contract

This document defines the supported system-entry surface for the V2 engine.

## 1. Unified Entrypoint
- **Command**: `python3 -m src_v2`
- **Default Behavior**: Displays a placeholder for the `serve` mode. Full REST/WebSocket parity pending Milestone 5.

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
| `--replay` | `str` | `None` | **DIVERGENT**. V2 uses a directory instead of a single file. |
| `--log-level` | `str` | `INFO` | **FULL**. Supports DEBUG, INFO, WARNING, ERROR. |

## 4. Execution Mode Compatibility
- **Headless**: Default for `cli` subcommand.
- **Concurrent**: Enabled via `--workers > 0`.
- **Deterministic**: Guaranteed for identical `--seed` and `--entities`.

## 5. Startup & Shutdown Semantics
- **Startup**: Registry-less initialization in V2. Scenario generation logic is native to `src_v2.systems.generator`.
- **Shutdown**: Clean finalization of `Kernel` and `ReplayManager`. Produces `manifest.json` in the replay directory.

## 6. Known Divergences
- **Replay Format**: V2 produces JSON-L chunks and a manifest in a directory, whereas legacy produced a single JSON file.
- **Grid Configuration**: `--grid-width/height` are currently handled via internal defaults (128x128) in the V2 generator, as the V2 state uses a sparse tile mapping instead of a fixed array.
