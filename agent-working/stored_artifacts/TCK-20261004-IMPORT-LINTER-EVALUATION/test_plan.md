---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-EVALUATION
artifact_type: test_plan
tags: [architecture, planning]
---

# Test plan — TCK-20261004-IMPORT-LINTER-EVALUATION

No repo tests change. Evidence is the measurement record itself: per rule an injected-violation pair (existing test result, contract result), per contract version, wall time, peak memory, violation count, and the 2 x 2 flag matrix; namespace-package coverage counts. Checks at close: `git diff --stat origin/main...HEAD` shows no change to `src/`, `tests/`, `pyproject.toml`, `uv.lock`, `.github/`; frontmatter validators on the record.

## Proof Plan
level: measurement; proof kind: injected violations in a scratch copy; oracle source: the existing boundary tests; expected effect: a per-rule parity table that supports exactly one of replace, add, drop; selected commands: `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 uvx --from import-linter lint-imports --config <scratch>`.
