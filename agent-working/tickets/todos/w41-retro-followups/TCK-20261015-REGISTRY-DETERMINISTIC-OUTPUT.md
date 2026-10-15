---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT
phase: open
date: 2026-10-15
tags: [delivery, determinism, process-improvement]
---

# TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT

## Title
Make docs/REGISTRY.yaml generation deterministic so an unchanged tree regenerates byte-identical and stops conflicting on its timestamp line

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, finding 1. In 2026-10-05..15, 151 of 210 session PRs hit a `docs/REGISTRY.yaml` conflict on GitHub,
and 146 of 288 follow-up pushes were REGISTRY-only re-syncs: a user-approved push plus about 9 min of CI each, roughly 23 h
in all. On top of that, 17 CI failures were stale-REGISTRY drift, and the owner closed 13 PRs and folded them into 4. A
replay of 324 conflicting merge-main commits without the custom driver (as GitHub merges) showed that 222 (69%) conflict
ONLY on line 3, `# Generated: <now>`, written by `tools/generate_registry.py` (around L648-652). Without that line, 102 still
conflict (adjacent same-day ticket insertions). Because the line changes on every run, a no-op regeneration still makes a
diff, so PRs that change no indexed input still touch the file.

## Scope
1. Remove the wall-clock `# Generated:` header line, or replace it with a value derived only from the inputs (e.g. a
   content hash of the entries), so regenerating an unchanged tree gives byte-identical output.
2. Keep `--check` behaviour; make sure no reader parses the removed line (grep tools/, tests/, .github/).
3. Re-run the replay on a sample of this window's conflicting merges (at least #586, #589, #590, #599, #597), driverless
   `git merge-tree`, with the new generator on both sides. Record the before/after conflict count in the ticket.
4. Record in `docs/plans/agent_infrastructure/agent_working_direction.md` an idea row: "stop committing REGISTRY.yaml
   (generate when read / regenerate on main / split per entry)". It reopens TCK-20260912's rejected option B with this
   window's measured cost. This ticket doesn't decide it.

## Out of Scope
- Stopping committing REGISTRY.yaml, splitting it, or a bot regeneration (idea row only).
- Editing CLAUDE.md (owner's file).
- The `.gitattributes` driver itself (TCK-20261015-PROCESS-TEXT-PLANNER-CARD-TLS-MERGE-TREE fixes the wording about it).

## Acceptance Criteria
- Two consecutive `make docs-registry` runs on an unchanged tree produce byte-identical files (test).
- `python3 tools/generate_registry.py --check` passes on main after the change; the real-registry drift test still passes.
- The ticket records the replay counts (before: conflicts on the sample; after: conflicts that remain), with commands.
- The direction-doc idea row exists and cites the numbers above.

## Related Tickets
- TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX (option B rejected then)
- TCK-20260925-CLAUDE-MD-REGISTRY-DRIVER-SERVER-SIDE-CAVEAT
- TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS

## Related Docs
- docs/README.md (The doc registry)
- docs/guides/delivery_process.md

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/generate_registry.py
- tests/ (real-registry drift test, registry generator tests)

## Assumptions / Open Questions
- Assumption: no consumer reads the Generated line. Verify before removing it.
- The remaining 31% (adjacent insertions) is out of reach of this fix; measure it, do not fix it here.

## Implementation Notes
(filled during work)

## Test Summary
(filled during work)

## Files Changed
(filled during work)

## Completion Summary
(filled at close)
