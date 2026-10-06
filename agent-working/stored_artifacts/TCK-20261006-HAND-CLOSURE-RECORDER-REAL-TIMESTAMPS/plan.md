# Plan — TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS

1. New `tools/agent-monitoring/hand_closure_time.py`: pure resolve (declared > tool_activity > unknown), the claim window (also the cost join for child 3), thin readers for the session's `tools.jsonl` rows and prior closures.
2. `record_hand_orchestrated_closure.py`: stamp `session_id` (from `CLAUDE_CODE_SESSION_ID`) and `duration_source`/`claim_peers`; `duration_s` null for unknown or an inverted span; events keep the closure `ts`.
3. `record_run.py`/`record_events.py` validate the optional fields; old rows stay valid.
4. `docs/agent-monitoring/schema.md` field rows; module docstring.
