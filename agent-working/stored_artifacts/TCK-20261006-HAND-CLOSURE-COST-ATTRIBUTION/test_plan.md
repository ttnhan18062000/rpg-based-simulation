# Test Plan — TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION

`tests/tools/test_hand_closure_time.py` (cost section): hand-computed count and `compute_cost_proxy_score` on the final event with `cost_source: "session_window"`; nothing claimed -> keys absent; a sidecar-attributed final event is not overwritten; declared window; two closures in one session through the real CLI attribute 6 + 4 rows with no repeat; a row with a sidecar `run_id` is not claimed; no joinable rows -> keys absent. Monitoring sweep: 1,517 passed.
