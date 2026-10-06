---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-HANDOVER-TRANSIT-EXPORT-WIPES-BUNDLE-VIA-SYMLINK-MEMORY-PATH
phase: done
date: 2026-10-06
tags: [ai, process-improvement]
---

# TCK-20261006-HANDOVER-TRANSIT-EXPORT-WIPES-BUNDLE-VIA-SYMLINK-MEMORY-PATH

## Title
`handover_transit.py export` looks for memory under the symlink-resolved path, finds none, and replaces the whole bundle with a smaller one

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found on PR #374 on 2026-10-06. A routine `tools/handover_transit.py export` in agent-working-implementer's
closure rewrote `agent-working/handover-transit/u24desktop-Virtual-Machine/`:
- `MANIFEST.jsonl` went from 148 entries to 2;
- 132 memory files and 14 handover/draft files were deleted (-5677 lines).

The change was caught in review and reverted before merge. Two defects combine:
1. **Wrong memory path.** `default_memory_dir()` (`tools/handover_transit.py:69-81`) builds the slug from
   `root.resolve()`. On this host `~/Working` is a symlink to `/mnt/data/Working`, so the slug becomes
   `-mnt-data-Working-rpg-based-simulation`, whose `memory/` holds 0 files. Claude Code keys memory by the path the
   session was started from, without resolving symlinks. The real memory is under
   `-home-u24desktop-Working-rpg-based-simulation/memory`, which holds 147 files. Both slug directories exist, so
   which one is right depends on how the session was started.
2. **Silent shrink.** `export_bundle` does `shutil.rmtree(bundle)` (:230) and writes whatever it collected, so an
   export that found almost nothing replaces a full bundle without a word.

## Scope
- **Memory path.**
  - `default_memory_dir()` builds candidate slugs from the git common-dir parent both unresolved (logical path,
    using `$PWD`-style resolution) and resolved, then picks the candidate whose `memory/` holds files.
  - If more than one candidate is non-empty, it raises `TransitError` naming both and asking for the new
    `--memory-dir`. Never guess.
  - If none is non-empty, say so in the export output. Do not drop memory silently.
- **Shrink guard.** Before the `rmtree`, compare the new item set with the existing `MANIFEST.jsonl`. If the new
  bundle would drop any memory entries, or more than 25% of all entries, refuse with a `TransitError` that lists
  the counts. `--allow-shrink` lets the owner do it on purpose.
- **`export --dry-run`.** Prints the counts per kind: notes, drafts and memory, new versus existing.

## Out of Scope
- Changing the bundle layout or the import side.
- Merging bundles across hosts.

## Acceptance Criteria
1. Fixture: a symlinked root where the logical-path slug holds memory and the resolved one is empty. Export picks
   the logical one and bundles its memory.
2. Both candidates non-empty: export refuses with both paths named, and writes nothing. With `--memory-dir`, it
   succeeds.
3. Existing bundle with 148 entries, new collection with 2: export refuses and the bundle is untouched.
   `--allow-shrink` succeeds.
4. An export that only adds or updates entries proceeds as today.
5. `export --dry-run` prints the per-kind new and existing counts and writes nothing.
6. Scoped `tests/tools/test_handover_transit*.py` are green. The "Moving sessions between machines" section of
   `docs/guides/agent_session_reset_boundaries.md` mentions the guard.

## Related Tickets
- PR #332 (introduced handover transit)
- `TCK-20261006-PR-BODY-ATTRIBUTION-TRAILER-NOT-CHECKED` (the PR #374 review where this was found)

## Related Docs
- `docs/guides/agent_session_reset_boundaries.md` ("Moving sessions between machines")

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/handover_transit.py` (`default_memory_dir` :69, `export_bundle` :215, CLI :401)

## Assumptions / Open Questions
- The 25% threshold is a starting value.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06. Root cause reported by agent-working-implementer and verified
here: the resolved slug's `memory/` holds 0 files and the logical slug's holds 147.

## Test Summary
`tests/tools/test_handover_transit.py` (40 pass, 8 new): the candidate holding files is picked; two filled candidates refuse naming both (and `--memory-dir` settles it, through the CLI dry run); none filled returns the first; a home-symlink alias is a candidate; a shrinking export (empty memory over a 7-memory bundle) is refused and leaves the manifest and files untouched; `allow_shrink` replaces it; an add/update-only export proceeds; `export --dry-run` prints `notes/drafts/memory: N new, M existing` and writes nothing. One existing test (re-export drops finished drafts, more than a quarter of the bundle) now passes `allow_shrink=True`.

## Files Changed
- `tools/handover_transit.py` (`memory_dir_candidates`, `_root_aliases`, `default_memory_dir`, `_refuse_shrink`, `export_counts`, `export --memory-dir/--allow-shrink/--dry-run`, `import --memory-dir`)
- `tests/tools/test_handover_transit.py`
- `docs/guides/agent_session_reset_boundaries.md`

## Completion Summary
Closed 2026-10-06. All six acceptance criteria met. Beyond the draft: `import` also takes `--memory-dir`, since it shares `default_memory_dir`. Behaviour to know: a routine export that prunes finished drafts past a quarter of the bundle now needs `--allow-shrink`, and `--no-memory` over a bundle that holds memory is refused for the same reason. The logical-path candidate is derived from `$PWD` and home-directory symlinks, which finds `~/Working` on this host; a symlink elsewhere is not found, and the two-filled-candidates refusal plus `--memory-dir` is the fallback. Not run for real: I did not run `export` against the real bundle (agent-working-design asked that none run until this lands); the real memory directories were only read through `--dry-run` on the fixture and a candidate check.
