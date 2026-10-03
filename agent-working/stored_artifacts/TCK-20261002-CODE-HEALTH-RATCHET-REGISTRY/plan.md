---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY

1. Add `F` and `E9` to ruff's `select`, rule X1 to the standard, before anything is seeded.
2. `tools/code_health/`: `findings.py` (the `Finding` record and its key), `adapters.py` (four pure adapters), `registry.py` (rows, validator, seed, delete, tighten), `ratchet.py` (compare and report), `scan.py` (run the tools, read their JSON), `__main__.py` (CLI). Package imports only.
3. Capture real tool output over a small sample package into `tests/fixtures/code_health/` and write adapter, ratchet, registry-validator and CLI tests that use a scratch repository.
4. Seed `registries/code_health_exceptions.jsonl` from a full scan (`reviewed: false`); add `make code-health` and `.PHONY`.
5. Parity ledger entry through `tools/parity_ledger_writer.py`; ownership row; update the standard's command table and registry paragraph.
6. Verify, close.

## Scope guards
No `src/`, `.claude/`, `CLAUDE.md`, `.github/workflows/`, existing test file, CI wiring, or snapshot work. Nothing is fixed, reformatted or annotated in `src/`.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| One adapter per tool, fixture-fed tests | 2, 3 |
| Ratchet exit codes; line-move case | 2, 3 |
| Improved/gone reported; delete tested | 2, 3 |
| Registry seeded `reviewed: false`; three rejections each tested | 3, 4 |
| Match keys documented; moved-line test | 2, 3 |
| `make code-health` exits 0, `.PHONY` | 4 |
| No pair findings beyond a link | 2, 3 |
| Ledger entry and ownership row | 5 |
| Package imports, orphan check | 2 |
| Diff scope, noqa count, tests only new | 6 |
| test.yml unchanged | 6 |
