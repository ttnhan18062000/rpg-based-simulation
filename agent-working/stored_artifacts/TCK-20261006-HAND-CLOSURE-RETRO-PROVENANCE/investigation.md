# Investigation — TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE

- `compute_retro_metrics` averaged only truthy `duration_s`, so the old 0 hand runs dropped out silently and a null (unknown) would too. Counting unknowns beside each average is new.
- Decisions beyond the ticket text: (a) the by-source table covers hand closures only (the ticket's AC5), pipeline runs are not "unlabelled hand"; (b) derived runs leave Slow Runs and Duration outliers, since those tables would otherwise mix a tool-activity span with elapsed time; (c) `session_window` cost leaves the Spend Proxy tables (it is one ticket-level total on the final event, not a phase figure) and the sidecar-coverage percentage, and has its own line; (d) the "changed meaning from week X" note names the first ISO week in the window that has a `duration_source` row, and renders once at the top.
- The metrics dict is also consumed by the dashboard JSON API; the new `run_summary.provenance` key is additive (None for old windows).
- Epic AC2 and the measured coverage of AC4 need the first full week after merge; they cannot be taken now, so the epic stays open.
