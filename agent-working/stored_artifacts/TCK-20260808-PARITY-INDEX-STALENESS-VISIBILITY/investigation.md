---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY
artifact_type: investigation
tags: [ai, observability, process-improvement]
---

# Investigation — TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY

## Docs Requiring Update

None. Searched `docs/` for any dedicated `parity_index.py` CLI-usage guide (`grep -rl
"parity_index.py" docs/`) — 9 hits, all decision docs / plans / archived ideas / other tools' own
references, none a living "how to use this CLI" reference doc. No doc update required beyond the
module's own docstring (updated in Implement to list the new subcommand) — a real finding, not a
skip.

## AC1: is the hash-recomputation mechanism actually separable from a full rebuild?

**Confirmed yes, cheaply.** Traced `_build_into()` (`tools/parity_index.py:380-419`):

```python
shard_manifest = [
    {"filename": s["filename"], "sha256": s["sha256"], "entry_count": len(s["entries"])}
    for s in shards
]
shard_manifest_json = serialize_manifest(shard_manifest)
source_manifest_hash = hashlib.sha256(shard_manifest_json.encode("utf-8")).hexdigest()
```

`shards` comes from `_load_shards(ledger_dir)` (`tools/parity_index.py:208-217`) — a lean
function that globs `*.yaml`, parses each shard for `len(entries)`, and computes a per-file
`sha256`. It does **not** call `_populate_entries`/`_populate_ref_tables`/`_populate_entry_health`/
`_populate_entry_fts` — those are the expensive, DB-writing steps `_build_into()` runs
afterward. A staleness check needs only `_load_shards()` + the same 3-line manifest/hash
construction — reused directly, not re-derived, avoiding any drift risk between the check and the
real build. `source_manifest_hash` is stored in the `ledger_generation` table (one row per built
DB, since `_atomic_replace_db` always builds into a fresh temp file with fresh schema) and
readable via a plain `SELECT`, no rebuild needed.

## AC2 (Assumptions section): does `parity-index/` write-safety (INFRA-315) actually apply to a `make` target?

**Re-verified directly, not just reasoned about — the concern doesn't apply to a `make` target at
all.** `_is_unsafe_parity_build_call()` (`tools/agent-monitoring/generate_retro.py:254-260`)
checks `"parity_index.py" in summary and "build" in summary` against a Bash tool call's raw
`input_summary` string. A `make parity-index` invocation's own `input_summary` is literally
`"make parity-index"` — the substring `"parity_index.py"` never appears in it, so this specific
audit **cannot see through the Makefile abstraction at all**. It only catches direct
`python3 tools/parity_index.py build` invocations without `--db-path parity-index/parity.db`.
This means a `make` target is not merely "arguably different in intent" from the audited
ad-hoc-CLI case — it's structurally invisible to the exact mechanism the concern was about.

Combined with `parity-index/` being gitignored (confirmed via `grep -n "parity-index" .gitignore`
→ line 271) and the direct precedent `agent-monitoring-index` already sets (its own `make`
target, `Makefile:284-286`, runs `tools/agent-monitoring/build_index.py` with **no** `--db-path`
override at all, building straight into that tool's own real default path
`agent-monitoring-index/monitoring.db`, also gitignored) — the correct design is: `make
parity-index` builds into the REAL `parity-index/parity.db` default path, matching every other
derived-SQLite-index `make` target in this repo, not a scratch path.

## Makefile precedent — style to mirror

`docs-registry`/`simq-corpus-registry` (`Makefile:255-259`) use the plain
`python3 tools/<script>.py` invocation form (no venv-detection wrapper), unlike
`agent-monitoring-index`'s fancier `$(shell for py in ...)` interpreter probe. Confirmed directly
(not assumed) that bare `python3` can import `yaml` on this machine
(`python3 -c "import yaml"` succeeds) and that `python3 tools/parity_index.py build --db-path
<scratch>` runs successfully under bare `python3` — the simpler `docs-registry` style is
sufficient and is what this ticket mirrors, not the heavier wrapper.

## Design

1. New `check_staleness(db_path=None, ledger_dir="docs/parity_ledger") -> dict` function in
   `tools/parity_index.py`, reusing `_load_shards()` + the exact 3-line manifest/hash
   construction from `_build_into()` (factored into a small shared helper to guarantee the check
   can never silently drift from what a real build actually hashes).
   - DB file doesn't exist → `{"status": "NOT_BUILT", ...}`
   - DB exists, hash matches → `{"status": "FRESH", "db_hash": ..., "live_hash": ..., "built_at": ...}`
   - DB exists, hash differs → `{"status": "STALE", "db_hash": ..., "live_hash": ..., "built_at": ...}`
2. New `check-staleness` CLI subcommand, matching the `entry`/`impact`/`health` argparse pattern
   exactly (`--db-path` default `DEFAULT_DB_PATH`). Exit code: `0` for `FRESH`, `1` for
   `STALE`/`NOT_BUILT` — matching the existing `build` command's own `0 if status == "ok" else 1`
   convention, so it composes cleanly in a shell pipeline/Makefile check.
3. Two new Makefile targets:
   - `parity-index`: `python3 tools/parity_index.py build` (real path, no override, matching
     `agent-monitoring-index`'s own precedent)
   - `parity-index-check`: `python3 tools/parity_index.py check-staleness` (real path)
   Both added to the `.PHONY` line alongside the existing target names.
4. Update `tools/parity_index.py`'s own module docstring to mention `check-staleness` in its list
   of supported operations (it currently documents build/entry/impact/health).
