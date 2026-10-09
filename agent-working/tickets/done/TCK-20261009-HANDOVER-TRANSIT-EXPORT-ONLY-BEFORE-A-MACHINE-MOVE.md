---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-HANDOVER-TRANSIT-EXPORT-ONLY-BEFORE-A-MACHINE-MOVE
phase: done
date: 2026-10-09
tags: [delivery]
---

# TCK-20261009-HANDOVER-TRANSIT-EXPORT-ONLY-BEFORE-A-MACHINE-MOVE

## Title
The delivery guide asks for a handover-transit export only before a machine move, not before every PR

## Status
DONE

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
Docs only. `tests/docs/`, `tests/tools/test_handover_transit.py` and `tests/tools/test_session_start_handover_hook.py`: 120 passed, 1 skipped, 1 xfailed; no test cites step 2a or the old "a PR's own export step" wording (grep over tests/ found none). `git diff --stat origin/main...HEAD -- agent-working/handover-transit/` is empty after the restore commit.

## Files Changed
- docs/guides/delivery_process.md (step 2a is now one paragraph: not part of a PR, own commit or PR, repo is public)
- docs/guides/agent_session_reset_boundaries.md (the machine-move section states it is the only place the export is prescribed, warns the repo is public, and drops "a PR's own export step does this already")
- tools/handover_transit.py (docstring only)
- agent-working/handover-transit/ (restored to origin/main in its own commit; the PR no longer carries the 78-file export)

## Completion Summary
No agent-facing guide tells a PR to refresh the handover-transit bundle any more. The machine-move procedure is unchanged apart from the public-repo warning and "in its own commit or PR". Searched `docs/`, `.claude/agents/`, `docs/guidelines/session_roles/`, `registries/`, `tools/` for the per-PR instruction: the only hits were delivery_process.md step 2a, agent_session_reset_boundaries.md step 1 and the exporter docstring, all fixed. No hit in CLAUDE.md (the owner's) or elsewhere outside agent-working's paths. For later: do not run the export before a batch PR.
