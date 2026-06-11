---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [ph10, m2, cli, compat]
---

# Walkthrough: Phase 10 Milestone 2 CLI Compatibility

Recovered the user- and operator-facing entry surface for the V2 engine.

## CLI & Entrypoint Recovery

### 1. Unified Entrypoint
- Implemented `src/__main__.py` and `src/cli/entry.py`.
- Supports the standard `python3 -m src` entry gate.

### 2. Subcommand & Argument Parity
- Recovered the `cli` subcommand for headless simulation.
- Supports core legacy arguments: `--seed`, `--entities`, `--ticks`, `--workers`, `--replay`, and `--log-level`.
- Implemented a minimal `EntityGenerator` in V2 to satisfy initial population requirements in a deterministic manner.

### 3. Execution-Mode Compatibility
- Integrated the CLI with the V2 `Kernel` and `RuntimeProfile`.
- Enabled concurrent execution via the `--workers` flag.
- Ensured bit-identical determinism for identical CLI inputs.

## Verification

### Black-Box Testing
- Created [test_entry_parity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/cli/test_entry_parity.py).
- Verified basic execution, invalid argument handling, default mode, and seed-based determinism.

```bash
pytest tests/cli/test_entry_parity.py
# Result: 4 passed
```

### Compatibility Contract
- Published the official [cli_entrypoint_contract.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/cli_entrypoint_contract.md) defining the supported surface and known divergences (e.g., replay directory structure).
