---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261005-FRONTMATTER-SWEEP-SCRIPT-PARTIAL-WRITE-BLAST-RADIUS
phase: done
date: 2026-10-05
tags: [ai, frontmatter, process-improvement]
---

# TCK-20261005-FRONTMATTER-SWEEP-SCRIPT-PARTIAL-WRITE-BLAST-RADIUS

## Title
Corpus-wide frontmatter script writes file by file with no dry run, so a mid-run crash leaves other sessions' artifacts modified

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
A frontmatter script run by rpg-implementer-2 modified 12 other sessions' `agent-working/stored_artifacts/` files before it crashed. The files were restored from HEAD and no damage remained, but the script's shape made the damage possible. The script path, traceback and the 12 paths were requested from rpg-feature-planning and are NOT yet in hand.

Leading candidate (read, not confirmed as the one that ran): `tools/add_frontmatter_tickets.py`.
- `main()` walks every `agent-working/stored_artifacts/<ticket>/**/*.md` and every `done/` ticket.
- `process_ticket_file` and `process_artifact_file` each call `path.write_text(...)` immediately, per file (lines ~203 and ~230). A crash on file N leaves files 1..N-1 rewritten.
- There is no dry-run mode, no ticket-scope argument and no argparse at all.
- It strips and rewrites existing frontmatter wholesale, so a file with richer hand-written frontmatter loses it.

`tools/tag_corpus_sweep.py` was also read: it writes only a report JSON and is not a candidate for this blast radius.

## Scope
1. Confirm the script from the traceback and paths (first step; if it is another script, apply the same fix there and update this ticket).
2. In the confirmed script: compute every edit in memory first; on any error raise before writing anything; write only after a full pass succeeds.
3. Default to dry-run (print the would-modify list and count); a writing run needs an explicit flag (e.g. `--apply`).
4. Add a per-ticket scope option (e.g. `--ticket-id`, repeatable) so a session cannot touch artifacts that are not its own.
5. Tests for each of the above.

## Out of Scope
- Changing which frontmatter schema the script produces.
- Other corpus-wide scripts, except to list them in Implementation Notes if they share the write-as-you-go shape (report only).

## Acceptance Criteria
1. A run in which any file raises leaves every file byte-identical to before (tested with an injected failure on file N > 1).
2. Running with no flags writes nothing and prints the list and count of files it would change.
3. `--apply` writes only after every edit was computed.
4. `--ticket-id X` restricts both ticket and artifact walks to X.
5. Existing `tests/tools/test_add_frontmatter_tickets.py` still passes or is updated with reasons.
6. The traceback and 12 paths are recorded in the ticket's investigation, or the ticket states they were never supplied.

## Related Tickets
- TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX (unrelated; neighbouring tooling only)

## Related Docs
- docs/guidelines/frontmatter_schema.md
- docs/guides/ticket_tagging.md

## Related Stored Artifacts
- none yet

## Related Code Areas
- tools/add_frontmatter_tickets.py
- tests/tools/test_add_frontmatter_tickets.py

## Assumptions / Open Questions
- Assumption: the candidate above is the script that ran. Unverified until rpg-feature-planning supplies the path and traceback.
- Open: whether a per-ticket flag is enough, or the script should refuse to run at all outside a dedicated ticket's own artifacts.

## Implementation Notes
- The traceback and the 12 paths were never supplied (requested from rpg-feature-planning, not in hand), so `tools/add_frontmatter_tickets.py` stays an unconfirmed candidate. It was fixed on its own merits; if a different script turns out to have crashed, it needs the same fix (file a follow-up then).
- `add_frontmatter_tickets.py`: `compute_ticket_file` / `compute_artifact_file` return the new content without writing; `plan_edits()` computes every edit first (any exception propagates before a single write); `main(argv)` is a dry run by default (prints `would modify:` per file and a count) and writes only with `--apply`; `--ticket-id` (repeatable) restricts both the done-ticket walk and the artifact-folder walk. `process_*_file` keep their signatures and now call the compute functions.
- Other corpus-wide scripts sharing the write-as-you-go shape: not surveyed (out of scope, report-only); `tools/tag_corpus_sweep.py` writes only a report JSON.

## Test Summary
`tests/tools/test_add_frontmatter_tickets.py`: 33 pass. New `TestSweepSafety`: no-flag dry run writes nothing and prints the count (AC2); an injected failure on a later ticket's artifact leaves every file byte-identical (AC1, AC3); `--ticket-id` leaves the other ticket's files untouched (AC4). The one existing `main()` test now passes `--apply` (the default changed on purpose).

## Files Changed
- tools/add_frontmatter_tickets.py
- tests/tools/test_add_frontmatter_tickets.py

## Completion Summary
`add_frontmatter_tickets.py` is now dry-run by default, computes all edits before writing, and takes `--ticket-id`. The traceback and paths were never supplied, so the culprit script is still unconfirmed (AC6).
