---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG
artifact_type: investigation
tags: [architecture, security, testing]
---

# Investigation: store lock, deletion log, kill tests

## Findings (from reading and from the kill tests)
- Writers: all store commands go through `cli.main` (one dispatch), plus the MCP `submit_candidate` (`store_readonly_tools._submit`). No other caller writes the quarantine/catalog.
- `catalogwrite.publish` stages in `.quarantine/.tmp-publish-*`, then `os.link`s. A kill after N links leaves N catalog files + the staging directory.
- **Found by the kill tests (not in the design):** (1) the files published are HARD LINKS to the staging directory, so after a kill their link count is 2 and `records.read_file` refuses them (`hard_link`, reported as `catalog_unreadable`/`SOURCE_RECORD_UNREADABLE`) until the staging directory is removed; `gc --delete` removes it. (2) A kill before the first link leaves an EMPTY `sources/<id>` directory that `audit_chain` did not report and that blocks `adopt` (`source_asset_exists`); `audit_chain` now reports it as `ORPHAN_FILE`.
- The tests' `env` fixture puts the quarantine outside the catalog; the real layout has it inside. The kill tests use the real layout (so the leftover directory note appears).
- `export_runtime` is atomic by one rename; a kill leaves only a `.tmp-*` directory beside the output (outside the catalog, audit cannot see it): recovery is delete it and re-run.
- `verify` flagged the new local files as `UNEXPECTED_FILE`; `verify._local_state` now allows exactly the lock, the log and its archives.

## Design deltas from plan.md (all approved points kept)
- Record is not in `RECORD_TYPES` (local state, no committed fixture); it uses the same strict `StoreRecord` machinery.
- Human-gated commands check the terminal before the lock, so a refusal leaves no lock file; the test snapshot helper ignores `.store.lock` and `.deletions*` (local, gitignored).
- `gc(delete=True)` needs `decided_at` (library never reads the clock); a full log or an unreadable item refuses before anything is removed.
- Archive: the next log's first `prev_hash` = last line hash of the newest archive; a wrong anchor or a missing middle archive is `DELETION_LOG_ANCHOR`.

## Stated limits
Truncating the log tail or deleting the newest archive is not detectable by the chain alone. The lock is advisory (a process that does not call it is not stopped). Linux flock only.
