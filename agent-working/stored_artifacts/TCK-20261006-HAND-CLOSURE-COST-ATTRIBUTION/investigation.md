# Investigation — TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION

- The old path omitted cost keys for hand closures because no sidecar existed (`compute_tool_stats(..., omit_when_unattributed=True)`); the keys are only ever added when evidence exists.
- Decision beyond the design: events of a hand closure share the closure time, so phases cannot be told apart. The claim is therefore ONE ticket-level total on the final non-sidecar event, and `cost_source` tells consumers it is not phase-resolved. Splitting rows across events by an invented rule would fabricate a per-phase spend. The retro child must not read a `session_window` figure as a phase figure.
- Rows with a non-null `run_id` (sidecar-attributed) are excluded when reading, so they keep their attribution. No row is claimed twice: the window's lower bound is the previous hand closure's end for the same `session_id`.
- With a declared start, the window is the declared span (rows in [start, end] after the previous closure); a declared closure with no rows keeps the keys absent.
- Coverage ceiling stays what TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES found: sessions with no hooks write no rows.
