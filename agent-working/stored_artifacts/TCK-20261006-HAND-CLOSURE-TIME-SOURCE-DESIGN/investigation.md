# Investigation — TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN

Method: `measure_sources.py` over W40-W41 hand closures at origin/main 7ddcd4526. Findings and numbers are in `design.md` section 1; per-run values in `coverage_by_run.csv`.

Caveats:
- Runs carry no `session_id` today, so A was measured by worktree shard plus a 1800 s contiguous block. Real coverage with a `session_id` key is expected to be equal or better for closures whose shard exists, and cannot exceed the 54.6% ceiling because 102 closures have no tools shard.
- B counts commits on all local refs. Remote-only branches that were deleted after squash merge are not visible, which understates B's start evidence.
- The measurement saw this branch's own commits for none of the 238 closures (they are not hand closures yet).
