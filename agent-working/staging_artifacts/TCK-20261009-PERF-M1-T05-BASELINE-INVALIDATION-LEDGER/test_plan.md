---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER
date: 2026-10-09
tags: [performance, determinism, testing]
---

# Test plan: TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER

Docs-only ticket; the verification is that every claim in the ledger can be reproduced and the doc gates pass.

## Proof Plan
- Level: docs consistency. Proof kind: reproduction of the inventory commands and counts. Oracle source: `git ls-files` counts, the baseline files themselves, `PERF_PROFILES`. Expected effect: the ledger's per-group counts add up to the 15 + 15 + 21 + others found. Selected commands: the search commands in `investigation.md`; a count check that the ledger rows cover all 30 baseline JSON files.
- `python3 -m pytest tests/docs tests/unit/tools tests/static -q` (frontmatter, registry, link checks).
- `python3 tools/generate_registry.py --check` after `make docs-registry`.
- No src, no test, no rerun: `git diff --stat` must show only docs, agent-working and monitoring files.
