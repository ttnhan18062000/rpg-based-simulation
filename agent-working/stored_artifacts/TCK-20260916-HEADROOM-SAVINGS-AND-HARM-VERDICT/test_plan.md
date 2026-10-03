# Test Plan — TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT

No pytest suite applies — this ticket is prose synthesis over two sibling tickets' own already-
verified evidence, not code.

| Case | Verification |
|---|---|
| Savings figure sourced correctly | Re-read `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`'s own table directly, not paraphrased from memory |
| Harm comparison uses matched window boundaries | Same `--harm-check-window-start 2026-09-16` command run twice, at two real different times, population counts recorded both times |
| Ceiling-effect limitation stated | `done_rate=1.0` and zero failures in *both* windows — explicitly noted as leaving no degradation headroom to detect |
| Cache-hit degradation gap stated honestly | Cross-checked against `docs/agent-monitoring/schema.md`'s "What is not recorded" directly |
| Abandon-vs-revert split correctly reasoned | Confirmed `.mcp.json`'s `headroom` entry is unconditional on `main` (not something this ticket should undo); Phase 2's own proxy was never enabled (nothing to revert there) |
| Fork clause (Caveman) preserved, not started | `registry.npmjs.org`/`@caveman-ai/cli` reachability cited from prior confirmation this window, not re-verified from scratch (nothing about network reachability changes between checks) |
| Epic ticket updated to reflect the verdict | `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` Acceptance Criteria and Status edited in the same batch |
| Folder-move rule checked, not assumed | `ls tickets/todos/headroom-context-compression-trial/` confirms child 5 (`PROXY-SESSION-CLASS-ROLLOUT`) remains — the whole-folder move does not apply yet |

Executed: two real invocations of `retrieval_baseline_metrics.py --harm-check-window-start
2026-09-16` (baseline capture, then this ticket's own re-run), direct reads of the trial ticket
and `docs/agent-monitoring/schema.md`, and a directory listing of the epic's own todos folder.
