---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-HANDOVER-TRANSIT-TEST-HOME-ISOLATION
phase: done
date: 2026-10-11
tags: [delivery]
---

# TCK-20261011-HANDOVER-TRANSIT-TEST-HOME-ISOLATION

## Title
handover_transit's default-memory-dir test no longer reads the real ~/.claude

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` calls `default_memory_dir()` against the real `~/.claude/projects`; it fails on this VM because two candidate memory dirs both hold files (the refusal is correct behaviour). Refs #513, part 1 only (the real-dir merge is the owner's).

Unstaffed-seat exception: `tests/tools/**`, `tools/**` and the issue belong to agent-working, whose seat is unstaffed; codebase takes this on lead-planner's request with the owner's confirmation (batch brief `docs/plans/codebase_health/knowledge_lock_transit_test_brief.md`).

## Scope
- Redirect `HOME` and `Path.home()` to `tmp_path`, run from a non-repo checkout dir, keep the slug assertions.
- Add: one filled candidate is chosen; two filled candidates raise `TransitError`.

## Out of Scope
- Any change to `tools/handover_transit.py` (no seam was needed).
- Reading, moving or merging the real memory dirs (owner's, #513 part 2).

## Acceptance Criteria
1. The test passes regardless of what is in the real `~/.claude`.
2. A one-filled and a two-filled (refusal) case are pinned.
3. `pytest tests/tools/test_handover_transit.py` green; the old test is red on this VM at origin/main.

## Related Tickets
- TCK-20261006-HANDOVER-TRANSIT-EXPORT-WIPES-BUNDLE-VIA-SYMLINK-MEMORY-PATH (introduced the candidates)

## Related Docs
- tools/handover_transit.py

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tests/tools/test_handover_transit.py
- docs/plans/codebase_health/knowledge_lock_transit_test_brief.md (batch brief, committed with this ticket)

## Assumptions / Open Questions
None open. The `Path.home` monkeypatch is enough: no code seam needed.

## Implementation Notes
Second candidate is produced via a symlink under the tmp home (the real-world alias case). Never touches real memory dirs.

## Test Summary
Red: the old test on origin/main fails on this VM (`TransitError` at tools/handover_transit.py:135, two filled candidates). Green: `tests/tools/test_handover_transit.py` 43 passed with the isolated test plus one-filled and two-filled cases.

## Files Changed
- tests/tools/test_handover_transit.py
- docs/plans/codebase_health/knowledge_lock_transit_test_brief.md (batch brief, committed with this ticket)

## Completion Summary
The default-memory-dir test now runs against a tmp HOME (Path.home and $HOME redirected, non-repo cwd, symlink alias for the second candidate) and cannot read the real ~/.claude. Pinned: one filled candidate chosen; two filled raise TransitError. No change to tools/handover_transit.py. Unstaffed-seat exception (agent-working). Refs #513 part 1; the real-dir merge (part 2) stays the owner's.
