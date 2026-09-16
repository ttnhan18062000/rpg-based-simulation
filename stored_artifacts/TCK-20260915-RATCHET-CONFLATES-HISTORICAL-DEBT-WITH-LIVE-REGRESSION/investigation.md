# Investigation — TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION

## The original finding

`monitoring_integrity_backlog_check.py`'s item 2 (`working_log DONE rows with no run record`)
combined frozen historical debt (~216 unreconstructable rows) and live process misses (3, from
this epic's own tickets closing without `record_hand_orchestrated_closure.py`) into one integer.
A failure like `219 exceeds 218 by 1` gives no way to tell which population moved without a
multi-step investigation — and the cheapest wrong response (raise the ceiling) would have silenced
the mechanism on the first real thing it ever caught.

## The widened scope, confirmed directly rather than assumed

One day of real operation showed five checks move on legitimate activity, not regression:

| Check | What moved it |
|---|---|
| `no-run-record` (item 2) | historical debt + live misses in one integer |
| `working_log_duplicate` (84→85) | a legitimate `BLOCKED`→`DONE` reopen |
| `event_seq_integrity` (71→72) | the same reopen |
| `ATTRIBUTION_RATE_FLOOR` | hand-orchestrated work (sanctioned) — gate already deleted |
| `CITATION_RESOLUTION_FLOOR` | closing one ordinary ticket — gate already deleted (this batch) |

For `working_log_duplicate_check.py` and `event_seq_integrity_check.py` specifically: both
modules' own pre-existing docstrings already established, before this ticket touched them, that
most of their measured population traces to the same legitimate multi-invocation/reopen mechanism
(51/71 duplicate-seq runs, 19/46 gapped runs). A single legitimate reopen moves both
`event_seq_integrity_check.py` conditions at once, and moves `working_log_duplicate_check.py`'s
count too if it writes two working_log rows for the same ticket_id.

## Disposition, per the explicit guard

`tool_call_count_mismatch_check.py` and `vocabulary_drift` (in `monitoring_anomaly_validator.py`)
were checked and confirmed NOT to share this shape — both count corpus debt that only grows
through a real mistake, and neither moved on any legitimate activity during this period. Left
untouched, per the ticket's own explicit instruction that this must not become a general
deratcheting exercise.
