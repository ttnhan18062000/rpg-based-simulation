---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION
artifact_type: plan
tags: [agent-monitoring, observability, data-quality]
---

# Plan — TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION

## 1. New module: `tools/agent-monitoring/monitoring_shard_paths.py`

```python
def shard_paths(data_root: Path, kind: str) -> list[Path]:
    """Every path that could hold real <kind> data: the bare per-week canonical file
    (data_root/<week>/<kind>.jsonl) and every per-identifier file
    (data_root/<week>/<id>.<kind>.jsonl). data_root must be a real, resolvable path -- never
    relative to an assumed CWD (record_events.py's own historical Path(".") hazard)."""

def per_identifier_shard_paths(week_dir: Path, kind: str) -> list[Path]:
    """Every per-identifier <kind> file in one week directory, excluding the bare canonical file
    -- the narrower question a consolidator needs (which files to fold IN), not the full read
    picture `shard_paths()` answers."""
```

`shard_paths()` is built on top of `per_identifier_shard_paths()` internally (one glob call reused,
not two independent expressions) via explicit per-week-directory iteration -- it never issues a
second repo-wide `data_root.glob("*/*.<kind>.jsonl")` call itself. This eliminates the fragile
double-glob idiom structurally rather than centralizing it in one place: after migration, the
idiom's literal textual shape appears **zero** times anywhere in the repo, not once (see the AC5
static guard below, which asserts exactly that).

## 2. Per-site migration (preserves every fallback per investigation.md's table)

Each site keeps its own post-glob logic; only the path-discovery expression is replaced with a call
to `shard_paths(data_root, kind)` (nine read-widening sites) or `per_identifier_shard_paths(week_dir,
kind)` (`monitoring_consolidation.py`'s own narrower need — folded in on proliferation grounds, not
because it was broken, per investigation.md).

`record_events.py` additionally switches its root from `Path(".")` to `Path("agent-monitoring/data")`
(module-relative-to-cwd is still how every other real call site in this repo resolves it — matches
the existing convention rather than introducing a new absolute-path assumption).

## 3. AC5 — "demonstrated not asserted": adopting the static-guard idea

Accepting the design peer's suggestion, for the same reason `test_working_log_csv_has_exactly_one_
writer` already exists and just caught nothing new on this exact review pass: a 10th copy should
fail at test time, not be found by inspection two weeks later. Unlike that guard, this one doesn't
need full AST resolution — the double-glob idiom's two-line shape is itself the literal signature
being searched for, so a plain source-text regex scan suffices (the AST guard's own reason for
rejecting grep — "the literal path string never appears on the same line as the open() call" —
doesn't apply here, since the glob expression *is* the thing being matched, not an indirect
reference to it).

New test: scans every `.py` file under `tools/`, `src/` (excluding `tests/`) for the paired
narrow+wide glob shape (matched independently per half, within a small line window, not one
combined regex -- the idiom's exact textual combination varies per site: f-string vs. plain
literal, bare filename variable vs. one with `.jsonl` already appended). Asserts **zero** hits
after migration, since `monitoring_shard_paths.py` itself never reproduces the paired shape (see
above) -- run once before migration to confirm it correctly finds the real pre-migration sites,
not assumed to work from the regex alone.

## 4. Tests

- `tests/tools/test_monitoring_shard_paths.py` (new): `shard_paths()`/`per_identifier_shard_paths()`
  correctness (bare-only, per-identifier-only, both, neither); the static guard above.
- Each of the 10 migrated files' own existing test suite re-run unmodified (AC4) — a passing
  detection-proving test for each stays passing without edits, or any edit is justified here.

## 5. Verification

Per-file test run after each migration (catch a regression at the site that caused it, not at the
end), then the full `tests/tools/` regression.
