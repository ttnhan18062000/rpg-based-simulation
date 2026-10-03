---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality]
---

# Investigation — TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION

## Full re-enumeration (not trusting the ticket's ~8-site count, per explicit instruction)

Grepped the whole repo for the double-glob idiom's actual shape
(`grep -rn 'glob(f"\*/' --include=*.py .`), broader than a literal-regex match on a specific
variable name, then read every hit's surrounding function to confirm it's a real instance and not
a coincidental `*/`-shaped glob for something unrelated (two false positives excluded:
`epic_blocked_status_static.py:60` and `done_checker_static.py:1019`, both `.md`-file globs,
unrelated to monitoring shards).

**9 real production read-widening call sites, not ~8, and not the same 8 the ticket or the design
peer's own grep named:**

1. `tools/gate_checks/done_checker_static.py:114` — `_jsonl_rows_for_run_id_across_weeks()`
2. `tools/agent_replay_codex/monitoring_shards.py:45` — `source_paths()`
3. `tools/agent-monitoring/bash_command_mix.py:76` — `week_shards()`
4. `tools/agent-monitoring/generate_retro.py:87` — inside `_source_mtime()`
5. `tools/agent-monitoring/validate.py:320` — `load_data_glob_with_line_count()`
6. `tools/agent-monitoring/manifest.py:77` — `_source_paths()`
7. `src/api/agent_ops_dashboard/ingest.py:138` — `_week_shard_paths()`
8. `tools/agent-monitoring/record_events.py:100-101` — inline in `compute_tool_stats()`
9. **`tools/agent-monitoring/verify_referential_integrity.py:71`** — genuinely new: named by
   neither the ticket nor the design peer's own grep. Its own comment cites
   `TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP` as the ticket that widened it, but that
   ticket's own Files Changed list never names this file — it has its own independent inline copy
   of the widened glob, not a call into the shared `validate.py::load_data_glob_with_line_count()`
   its docstring says its own consumers include. Confirmed by reading the code directly: this file
   duplicates the pattern rather than reusing the function that already exists for exactly this
   purpose.

**Correction to the design peer's own grep, worth recording precisely since it changes what
"enumerate the rest" turned up**: they reported `validate.py::load_data_glob_with_line_count()` and
`generate_retro.py::_source_mtime()` as *not* matching their regex, evidence the idiom "has
variants." Read both directly: both contain the literal double-glob shape
(`glob(f"*/{X}.jsonl") + glob(f"*/*.{X}.jsonl")`), just as a local variable inside a longer
function rather than a bare return statement — a plain `grep -rn 'glob(f"\*/'` finds both. Their
regex likely anchored on the exact `return` shape the simpler one-liners use. Not a defect in their
work — it's exactly the "the idiom has variants" caution they raised, just resolved: the variant is
in how the two globs are combined and assigned, not in the glob expressions themselves.

## Sites checked and confirmed OUT of scope (T1/T2's own new code)

- `tools/working_log_parser.py::parse_pending_working_log_shards()` — globs
  `data_root.glob("*/*.working_log.jsonl")`. This is a **single** glob, not a narrow/wide pair,
  because working_log shards never had a legacy bare-canonical-name shape to also match (T2
  introduced them from scratch, already wide-shaped on day one). Not an instance of the defect
  class this ticket consolidates — confirmed by reading, not assumed clear because it's new code.
- `tools/agent-monitoring/monitoring_consolidation.py:64` — `sorted(week_dir.glob(f"*.{kind}.jsonl"))`.
  The design peer flagged this as a "confirmed new site." Read its actual purpose: this glob is
  deliberately **per-identifier-only** — it exists to find files *to fold into* the canonical
  file, so it must never also match the canonical file itself. It is not the narrow/wide defect
  (missing the wide shape); it is correctly narrow by design. It is, however, still an
  independently-hand-rolled path-construction expression of the same general family, which is
  exactly the proliferation this ticket exists to stop recurring — see Scope decision below for
  how it's folded into the shared module anyway, on those grounds, not because it was broken.

## `record_events.py:100-101`'s `Path(".")` hazard — confirmed, not assumed

```python
tools_paths = sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl")) + sorted(
    Path(".").glob("agent-monitoring/data/*/*.tools.jsonl")
)
```
`Path(".")` resolves against whatever the process's current working directory happens to be at
call time — never a repo-root-anchored path. Every other call site in the re-enumerated list takes
its root as an explicit parameter (`data_dir`/`data_root`/`week_dir`), so this is the one genuine
outlier. Migrating this site onto a shared resolver that takes a real root parameter fixes this as
a side effect (Scope decision below), rather than porting a relative-CWD assumption into the new
consolidated function.

## Resolver location (Open Question 1) — decided

New sibling module, `tools/agent-monitoring/monitoring_shard_paths.py`, not an addition to
`monitoring_batch_identifier.py`. That module's own scope is narrowly "what identifier does this
one write/read belong to" (a single-purpose git-branch/PR-resolution concern with its own detached-
HEAD/sidecar fallback chain, unrelated to glob mechanics). The read-path problem's callers span a
much wider footprint — `tools/gate_checks/`, `tools/agent_replay_codex/`, `tools/agent-monitoring/`
itself, and `src/api/agent_ops_dashboard/` (a `src/` module already reaching across into `tools/`
for this exact reason, per its own existing import). A new, narrowly-scoped sibling module matches
the existing precedent of `src/` importing a dedicated `tools/agent-monitoring/` module rather than
deepening `monitoring_batch_identifier.py`'s own more specific responsibility.

## Per-site fallback audit (Open Question 2 — no blanket answer, decided per site)

| Site | Existing fallback/nuance beyond the bare double-glob | Disposition |
|---|---|---|
| `done_checker_static.py::_jsonl_rows_for_run_id_across_weeks` | Filters by `run_id` after reading | Preserved — post-processing stays local, only path discovery moves to the shared call |
| `monitoring_shards.py::source_paths` | Second arg is a `source_stem` derived from `source` (strips an extension) for the per-identifier half | Preserved — the stem derivation is a caller-side concern, passed into the shared call unchanged |
| `bash_command_mix.py::week_shards` | None beyond the bare double-glob | Migrated as-is |
| `generate_retro.py::_source_mtime` | Takes the max `st_mtime` across all matched shards for staleness detection | Preserved — mtime computation stays local, only path discovery moves |
| `validate.py::load_data_glob_with_line_count` | Also returns a line count alongside records | Preserved — line counting stays local |
| `manifest.py::_source_paths` | None beyond the bare double-glob | Migrated as-is |
| `ingest.py::_week_shard_paths` | None beyond the bare double-glob (the dashboard backend) | Migrated as-is |
| `record_events.py` inline (`compute_tool_stats`) | `Path(".")`-relative root (the hazard above) | Fixed as a side effect — takes a real root now |
| `verify_referential_integrity.py` inline | Reads `(dict, source_path_str)` tuples, not bare dicts, for its own per-line provenance tracking | Preserved — the per-line read loop stays local, only path discovery moves |
| `monitoring_consolidation.py::consolidate_jsonl_kind` | Per-identifier-only (no bare-canonical match) | Given its own narrower shared primitive (`per_identifier_shard_paths`), not the wide one |

No site's fallback is dropped; every one keeps its own post-glob-read behavior exactly as before,
confirmed per site by reading, matching AC3's explicit instruction not to apply a blanket
keep-or-drop.
