# Test Plan — TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS

`tests/tools/test_hand_closure_time.py` (25): resolve precedence and every source; the design's two ACs (no evidence -> unknown, null, start==end; five rows -> tool_activity with the first row's ts and the span, other session/sidecar rows ignored); the claim partition (no row claimed twice); readers; validators accept old rows and reject bad new values; the real CLI in a scratch repo for unknown, tool_activity, other-session rows, declared, inverted span, no session id; `generate_retro` and the duplicate-run check load old and new rows.
Plus the 1,303-test sweep over tests mentioning monitoring/record_run/record_events/generate_retro.
