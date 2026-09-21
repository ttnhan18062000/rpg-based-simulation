# Plan — TCK-20260921-REAL-TOKEN-TELEMETRY

1. Promote the peer's scratch logic into `tools/agent-monitoring/real_token_usage.py`: a clean,
   tested, read-only module — `collect()` (streaming filesystem walk) and `build_report()` (pure
   aggregation over already-collected data), separated deliberately so tests never touch the real
   filesystem.
2. Outputs, matching the brief exactly: totals; by day; by model; main vs. subagent; by session
   (role name via `agent-name`/`custom-title`, not `cwd`); by git branch (NEW — per-batch cost);
   context-size buckets; attribution by tool (context shared evenly across tools called in one
   request, text-only requests tracked separately, not dropped); attribution by Bash command
   family; tool-result sizes (char counts only, never content).
3. CLI (`python3 tools/agent-monitoring/real_token_usage.py --since ... [--root ...]`) prints a
   markdown report, matching the peer's own already-reviewed table shapes.
4. Wire an opt-in `--include-real-tokens` flag into `generate_retro.py`'s `main()`; `generate()`
   itself takes an already-built `real_token_report` dict (or `None`, the default) and never
   touches the filesystem — additive, separately-gated `## Token Usage (Real)` section, same shape
   as the existing `## Shadow vs. Baseline Retrieval Comparison` section.
5. Correct `docs/agent-monitoring/schema.md`'s "no workaround" claim and
   `retrieval_baseline_metrics.py::build_context_tokens_section()`'s "platform-blocked" reason —
   both false now that this module exists, both corrected without breaking the one existing pinned
   test (`status`/`citation` unchanged; `reason` reworded, `workaround` key added).
6. Tests: synthetic fixture JSONL built in-test (`tests/tools/test_real_token_usage.py`), never
   reading or copying real transcript content. Real-world validation done separately, read-only,
   via the CLI directly against this machine's own transcripts — confirms the tool works against
   real data shapes without ever writing anything back into the repo.
7. Close via the standard hand-orchestrated path: `stored_artifacts/`,
   `record_hand_orchestrated_closure.py`, `docs/REGISTRY.yaml` regeneration — folded into this
   batch's single close-out with Ticket 2, per the peer's own "one report" instruction for the
   whole batch.
