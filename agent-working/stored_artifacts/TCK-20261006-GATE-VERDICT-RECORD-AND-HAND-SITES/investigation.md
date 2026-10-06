---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation
Verified on origin/main: no gate_verdict, override or adjudication field exists. The gate CLIs print to stdout only. `gate-policy.yaml` is the gate_id source (done_checker_static appears twice, `clean_data_runs_early` at Test and `run_finalize_selfcheck` at Finalize; `run_static_precheck` backs an agent-verdict gate and has no static entry, so a precheck-only run gets `cli:done_checker_static`).

Hazards found: the doc-staleness CLI takes positional args, so new options are stripped before parsing; `attest_gate` wraps gate CLIs, so an unguarded inner write would double-count; a nested checker run by `post_native_run_check` would be mislabelled `hand` without the mode env.
