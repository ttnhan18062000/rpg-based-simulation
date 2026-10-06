# Plan — TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION

1. `hand_closure_time.Resolution.claimed` is the cost join: the closing session's unattributed `tools.jsonl` rows after its previous hand closure (declared start: rows inside the declared window).
2. `record_hand_orchestrated_closure.attach_session_window_cost`: the claimed rows' count and the unchanged `cost_proxy.compute_cost_proxy_score` go on the final event not already attributed by a sidecar, `cost_source: "session_window"`; sidecar-attributed events get `cost_source: "sidecar"`.
3. `record_events.validate_record` checks `cost_source`; schema.md documents it.
