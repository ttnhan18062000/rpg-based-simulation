---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG
artifact_type: plan
tags: [architecture, security, testing]
---

# Plan (DESIGN ONLY, no code yet): store lock, deletion log, kill tests (ADR D24)

Status: awaiting asset-planner approval of the design, then owner approval of the D24 text.

## Facts read (2026-10-10)
- Writers: `intake`, `review`, `build`, `release`, `export-runtime` (writes outside the catalog but reads committed state), `gc --delete`, `adopt`, `adopt-set`, `revoke`, `draft keep|drop|export` (export writes a NEW dir outside the store), plus the MCP `submit_candidate` (it calls the intake service) and `export_handoff` (drawing workspace, its own per-sprite lock: out of scope).
- Dispatch is one `if args.command == ...` chain in `store/cli.py::main`; the store root is `config.CATALOG_ROOT`, resolved once (module dir, or `VISUAL_ASSETS_CHECKOUT`).
- `catalogwrite.publish` stages under `.quarantine/.tmp-*`, publishes with exclusive `os.link`, rolls back on failure; a SIGKILL can leave orphan files (docstring, line 1-6). `gc` lists leftover `.tmp-*`.
- `gc` deletes only untracked local items under quarantine, review and `generated/`.

## Design

### 1. Lock
- File: `<visual_assets>/catalog/.quarantine/.store.lock`? No: `.quarantine` may be deleted by gc. Use `<visual_assets>/catalog/.store.lock` (gitignored via a new `.gitignore` line; one lock per store data root, so a worktree and the main checkout have separate locks, matching their separate stores). The file is never deleted (no unlink race).
- Module `visual_assets/store/lock.py`: context manager `store_write_lock(command: str)`. `os.open(O_CREAT|O_RDWR|O_NOFOLLOW, 0o600)`, refuse a symlink or non-regular file, `fcntl.flock(fd, LOCK_EX|LOCK_NB)`. On `BlockingIOError`: raise `GateError("store_locked", ...)` naming the holder read from the file (`pid`, `command`, `started_at`), then exit 1 at once. No waiting.
- Holder record: after acquiring, truncate and write one canonical JSON line `{"command","pid","started_at"}`. It is advisory text only; truth is the kernel lock. A stale file after a kill is harmless: flock is released by the kernel, the next writer overwrites it. The refusal message says the holder info is the last writer's claim.
- `started_at` is injected like other timestamps (`_now()` passed in), not read inside the module, to keep determinism of tests.
- Taken at ONE place: `cli.main` wraps the dispatch for the writing command set (a frozen set `WRITING_COMMANDS`; `draft` splits on `keep|drop`), and the MCP `submit_candidate` entry takes it around the intake call. A test asserts every `add_parser` command is in exactly one of `WRITING_COMMANDS` / `READ_ONLY_COMMANDS` so a new command cannot forget the decision.
- Reentrancy: nothing calls `main` recursively; the lock is not reentrant, a nested acquire in the same process refuses (a test), which catches an accidental double wrap.
- Windows/NFS: not supported (Linux `flock`); the module refuses to import-run elsewhere with a clear error. Stated in the ADR.

### 2. Deletion log
- File: tracked `visual_assets/catalog/provenance/deletions.jsonl`? `gc` deletes untracked local files, so a tracked log of local deletions would churn git for nothing and conflict across machines. Proposed: **local, gitignored, append-only** `visual_assets/catalog/.deletions.jsonl`, plus the rule that `audit_chain` verifies it when present. Alternative for the owner: tracked. Decision requested (see Open questions).
- Record (typed contract `DeletionRecord`, canonical JSON, one per line, under `store/contracts`): `kind` (quarantine|review|generated), `path` (relative to catalog root), `content_hash` (sha256 of file bytes, or of a canonical tree listing for a directory), `reason`, `decided_at` (UtcTimestamp, injected), `prev_hash` (sha256 of the previous line, chain start = 64 zeros).
- `gc --delete` hashes each item BEFORE removing it, appends the record with `O_APPEND` + fsync, THEN removes. A kill between the two leaves a record for a still-existing path, which `audit_chain` reports as a note ("recorded, not yet removed"), never a break. Log-first is chosen so no deletion is ever unrecorded.
- `audit_chain` checks: each line parses, canonical bytes round-trip, `prev_hash` chain intact, path stays inside the three deletable roots (no `sources/`, `provenance/`, `manifests/`), no duplicate line. A tampered/reordered/truncated-middle line is a BREAK. A truncated tail is undetectable by chain alone (stated limit); the log grows only by append.
- Listing: `python -m visual_assets.store deletions` (read-only, no lock), prints one line per record.
- Bound: new budget `MAX_DELETION_LOG_BYTES` (1 MiB) in config and `budgets.md`; `gc --delete` refuses to append past it (owner reviews).

### 3. Kill-mid-publish tests
Subprocess helper runs `catalogwrite.publish` (and `runtime_export`) with an env-injected kill point that does `os.kill(os.getpid(), SIGKILL)` through the existing `_link` module-attribute seam (publish) and a new equivalent seam in `runtime_export`. Injection points (>=3 each): (a) before the first `os.link`, (b) after file 1 of N linked, (c) after the last link before temp cleanup; runtime_export: (d) after the first PNG written, (e) before the manifest is written. Asserts after each: the store parent process can still `verify`/read; `audit_chain` reports the orphans (codes already exist or one new `orphan_publish_file`); a re-run either completes (idempotent exclusive link tolerated for identical bytes? NO: it refuses cleanly with the existing `exists` error and the documented recovery is `gc` for `.tmp-*` and a manual `git clean` listing printed by audit) and never half-overwrites. Lock proof: child holds the lock, is SIGKILLed, parent acquires immediately.
Recovery is documented in `store_contract.md` (orphan catalog files: audit lists them; remove with `git clean -n` review; this ticket adds no automatic orphan deletion, because that would be a tracked-state deletion kind).

### 4. Files touched
`visual_assets/store/{lock.py,cli.py,gc.py,audit.py,config.py,catalogwrite.py?,runtime_export.py}` (only the injectable seam), `store/contracts/deletion.py`, MCP `submit_candidate` entry in `visual_assets/drawing/server/`, `.gitignore` (lock + log lines), tests under `tests/visual_assets/`, `docs/assets/{store_contract,budgets,retention_and_rollback}.md`, ADR D24 + D18 marked superseded-in-part, `docs/assets/README` index if needed. No `src/`, no `.github/`.

### 5. Security review points (for the review step)
symlink/`O_NOFOLLOW` on the lock file; holder JSON is untrusted text when printed (strip control chars, cap length); log path containment and no `..`; log append is atomic per line (`O_APPEND`, line < PIPE_BUF not guaranteed, but the lock serialises writers); `gc` already verifies each target sits under an allowed root, the log repeats that check.

## Proposed ADR D24 text (for the owner)
| D24 | Store writes (`AM1-W10.4` reversal of D18): every command that writes the store takes one advisory lock per store data root (`flock` on `catalog/.store.lock`) and a second writer refuses at once, naming the holder's pid and command (no waiting); read-only commands take no lock. `gc --delete` appends one chained, typed record per removal to an append-only deletion log before it removes the item. `audit_chain` verifies the log. Kill-mid-publish is tested at fixed points; a hard kill can still leave orphan files, which `audit_chain` reports and the operator removes by hand | **owner to decide** | D18 assumed one operator; the owner chose on 2026-10-10 to allow automation and several agent sessions, so the rule must be enforced by code, and a deletion needs a record | `flock` is unavailable (non-Linux host), or `gc` gains a deletion kind for tracked objects (a typed roots record first) |
D18 stays, marked "superseded in part by D24 (no lock, no deletion record)".

## Open questions for the planner / owner
1. Deletion log local+gitignored (proposed: no git churn, per machine) or tracked (shared history, merge conflicts)?
2. Lock file in `catalog/` (proposed) vs `visual_assets/`?
3. Orphan removal stays manual (proposed) — ok?

## Proof Plan
- Concurrency: two subprocesses, second refuses with holder info, exit 1, no wait (time-bounded test); read-only commands pass while the lock is held.
- Command coverage test: every parser command is classified; a mutant that removes the lock from one writing command fails it.
- Deletion log: record per removal; tampered/reordered/forged-path/over-budget log -> audit BREAK; log-first kill leaves a "recorded, not removed" note.
- Kill tests: SIGKILL at 3 publish + 2 export points; store readable, audit reports orphans, kernel releases the lock, re-run refuses or completes cleanly.
- Mutation proofs: remove `LOCK_NB`, remove `O_NOFOLLOW`, drop the log-before-remove ordering; each must fail a named test (assert single-match mutants).
