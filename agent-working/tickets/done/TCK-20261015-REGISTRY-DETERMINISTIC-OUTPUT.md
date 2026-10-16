---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT
phase: done
date: 2026-10-15
tags: [delivery, determinism, process-improvement]
---

# TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT

## Title
Make docs/REGISTRY.yaml generation deterministic so an unchanged tree regenerates byte-identical and stops conflicting on its timestamp line

## Status
DONE

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
Dropped the wall-clock `# Generated: <now>` line from `tools/generate_registry.py` (header is now two fixed lines) and the unused datetime import. Nothing parses that line: `--check` compares parsed entries, and the one test that rewrote it (`test_check_ignores_header_timestamp_drift`) now edits the second header comment instead. Added a determinism test (two runs with a moved clock are byte-identical, no `Generated` in the file). Direction-doc idea row added (stop committing REGISTRY.yaml), citing the measured cost; it decides nothing. Replay (driverless 3-way `git merge-file` of docs/REGISTRY.yaml for every `Merge remote-tracking branch 'origin/main'` commit in a PR branch, once as committed and once with line 3 removed from base, ours and theirs, which is what the new generator produces on both sides): last 60 merged PRs, 67 origin/main merges, 59 conflicted as committed, 21 still conflict without the Generated line (64% of the conflicts gone; the remaining ones are adjacent same-day ticket insertions, out of scope). The five named sample PRs (#586, #589, #590, #599, #597) have 4 such merges: 2 conflicted before and 2 after, and in both the header hunk is gone (hunk counts 3 to 2 and 2 to 1), the other hunks are adjacent insertions. The script is stored in the ticket's stored artifacts (`replay_registry_merges.sh`).

## Test Summary
`tests/tools/test_generate_registry.py` 69 passed (new determinism test; the header test rewritten), `tests/tools/test_done_checker_static.py` passed. The real-registry drift test passes after regeneration.

## Files Changed
tools/generate_registry.py, tests/tools/test_generate_registry.py, docs/plans/agent_infrastructure/agent_working_direction.md, docs/REGISTRY.yaml (regenerated, no clock line), agent-working/stored_artifacts/TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT/

## Completion Summary
The generator no longer writes a wall-clock line, so an unchanged tree regenerates byte-identical. Replay on 60 PRs: 59 REGISTRY conflicts before, 21 after. The remaining 31 to 36% are adjacent insertions, unchanged by design.
