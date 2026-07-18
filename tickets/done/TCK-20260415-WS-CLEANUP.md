---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260415-WS-CLEANUP
phase: done
date: 2026-04-15
tags: [ws, cleanup]
---

# TCK-20260415-WS-CLEANUP

## Title

Workspace Cleanup of Temporary Files

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Remove all temporary files in the workspace (caches, scratch files, build artifacts) while explicitly preserving any directory named `tmp/`.

## Scope

- Identify and remove Python cache files (`__pycache__`, `*.pyc`).
- Identify and remove Pytest cache files (`.pytest_cache`).
- Identify and remove Next.js build artifacts (`.next/`) in relevant sub-projects.
- Identify and remove scratch files and directories (`scratch/`, `scratch_*.py`).
- Remove hidden system files like `.DS_Store`.
- Explicitly exclude any path containing `tmp/`.

## Out of Scope

- Deleting `node_modules`.
- Touching backup directories unless they contain clear temporary caches.
- Deleting user-created documents or core project files.

## Acceptance Criteria

- All identified cache and scratch files are removed.
- `tmp/` directories in all projects remain intact.
- The workspace is clean of transient build artifacts.

## Related Tickets

- None

## Related Docs

- None

## Related Stored Artifacts

- None

## Related Code Areas

- Root workspace and project directories.

## Assumptions / Open Questions

- Assumes `scratch/` files are no longer needed.
- Assumes `.next/` is safe to delete (it is regeneratable).

## Implementation Notes

- Use `find` with exclusion patterns to safely delete files.

## Test Summary

- Verify remaining files after cleanup.

## Files Changed

- Multiple files and directories deleted.

## Completion Summary

- (Pending)
