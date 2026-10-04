---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT
phase: open
date: 2026-10-04
tags: [ai, hooks, process-improvement]
---

# test_plan — TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT

Manifest round-trip byte identity; .txt suffix and strip; role/drafts/memory selection; rolling replace; empty export error; sha mismatch aborts with no write; differing file backed up; dry-run writes nothing; idempotent re-import; unsafe manifest path refused; memory slug; discard refusal/force/marker; status/pending; hook notice present/absent/fails open for each source; hook silent with no bundle.

## Proof Plan
- level: unit (tmp_path-injected paths) plus one real export for registry/validator isolation
- proof kind: automated tests and a registry regeneration check
- oracle source: sha256 manifest equality, registry row count, hook stdout
- expected effect: byte-identical round trip; tamper aborts with no write; no registry row for the bundle
- selected commands: `pytest tests/tools/test_handover_transit.py tests/tools/test_session_start_handover_hook.py`; `python3 tools/generate_registry.py --check`
