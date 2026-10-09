---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-HANDOVER-TRANSIT-EXPORT-ONLY-BEFORE-A-MACHINE-MOVE
phase: open
date: 2026-10-09
tags: [delivery]
---

# TCK-20261009-HANDOVER-TRANSIT-EXPORT-ONLY-BEFORE-A-MACHINE-MOVE

## Title
The delivery guide asks for a handover-transit export only before a machine move, not before every PR

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/guides/delivery_process.md` PR Lifecycle step 2a tells every PR to run `python3 tools/handover_transit.py export`
and stage `agent-working/handover-transit/`. Only #332, which created the bundle, ever did. PR #459 then followed the
step and carried 78 files (+5,099/-1,438 lines) unrelated to its six tickets: every session's handover note, all open
drafts across domains, and the project memory files, all published on a public repo. The owner decided (2026-10-09):
drop the bundle from #459, and change the guide so the export happens only before a machine move, as
`docs/guides/agent_session_reset_boundaries.md` ("Moving sessions between machines") already describes.

## Scope
- `docs/guides/delivery_process.md`: remove step 2a from the per-PR lifecycle. Replace it with one line: the
  handover-transit bundle is exported only when moving sessions to another machine, in its own commit or PR, never
  inside a ticket batch. Point to `agent_session_reset_boundaries.md`.
- `docs/guides/agent_session_reset_boundaries.md`: make sure the machine-move section is the only place the export is
  prescribed, and that it warns the repo is public, so the export publishes notes and memory.
- `tools/handover_transit.py` docstring: same correction if it says "before every PR".
- Search other agent-facing text (.claude/agents/**, docs/guides/**, the session role cards and templates) for the
  per-PR instruction, and fix each hit inside agent-working's paths. Report any hit outside them (CLAUDE.md is the
  owner's) instead of editing it.

## Out of Scope
- Changing what the exporter includes, or deleting the existing bundle on main.
- CLAUDE.md (owner's); propose the wording only if it names the step.

## Acceptance Criteria
1. No agent-facing guide tells a PR to refresh the handover-transit bundle.
2. The machine-move procedure is unchanged and states the public-repo exposure.
3. Docs tests (tests/docs/, tests/tools/ guide tests, if any cite step 2a) pass.

## Related Tickets
- TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT (created the bundle)

## Related Docs
- docs/guides/delivery_process.md
- docs/guides/agent_session_reset_boundaries.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tools/handover_transit.py (docstring only)

## Assumptions / Open Questions
- `search_docs` index not built, graphify graph missing in this worktree: the duplicate scan used the ticket folders
  and grep. No open ticket covers this.

## Implementation Notes
Lands on PR #459 (agent-working-small-fixes-batch), together with removing the bundle refresh from that PR.

## Test Summary
## Files Changed
## Completion Summary
