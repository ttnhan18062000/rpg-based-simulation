---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-PILOT-EVIDENCE-GITIGNORED-JSON
phase: done
date: 2026-10-02
tags: [data-quality]
---

# TCK-20261002-PILOT-EVIDENCE-GITIGNORED-JSON

## Title
Make the filtered-replay pilot's raw evidence reach the remote (write `.jsonl`, not a gitignored `.json`)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`TCK-20260907-FILTERED-REPLAY-EVAL-PILOT` cites `stored_artifacts/.../pilot_run_raw_output.json`, which
`.gitignore` drops (`stored_artifacts/**/*.json`), so the cited evidence never reached origin/main. The
integrity report's `cited_evidence` check found it. Root cause: `tools/agent_replay/run_pilot.py` writes that
ignored name on every run. Draft and verification came from `agent-working-design`
(`.claude/handover/drafts/pilot-evidence-jsonl/`).

## Scope
- `run_pilot.py` writes `pilot_run_raw_output.jsonl` (compact single-line JSON plus newline); docstring updated.
- Commit the existing data as `.jsonl` (json-equal to the original; whitespace only differs). The pilot was
  deliberately not regenerated, since that would change `generated_at` and the results.
- The closed ticket's one citation (Files Changed) names the `.jsonl`.

## Out of Scope
- Regenerating the pilot. Any other edit to the closed ticket.

## Acceptance Criteria
- The cited `.jsonl` is tracked (not ignored) and parses as the original data.
- `cited_evidence` findings drop from 13 to 12 and the pilot finding is gone.
- `tests/agent_replay` passes; `validate_frontmatter` still passes on the edited done ticket.

## Related Tickets
- TCK-20260907-FILTERED-REPLAY-EVAL-PILOT
- TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT

## Related Docs
none

## Related Stored Artifacts
- stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/pilot_run_raw_output.jsonl

## Related Code Areas
- tools/agent_replay/run_pilot.py

## Assumptions / Open Questions
- `run_pilot.py` has no dedicated unit test and nothing else reads the old filename.

## Implementation Notes
Applied design's `evidence.patch` verbatim (3 files, +6/-4). Same trap as the recorded
`.gitignore drops stored_artifacts .json` lesson: store machine-readable artifacts as `.jsonl`.

## Test Summary
`tests/agent_replay`: 42 passed. The committed `.jsonl` parses to the original structure (21 top-level keys).
`git check-ignore` confirms the `.jsonl` is not ignored.

## Files Changed
- tools/agent_replay/run_pilot.py
- stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/pilot_run_raw_output.jsonl
- tickets/done/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md (one citation line)

## Completion Summary
The pilot's cited evidence is now tracked and will reach the remote.
