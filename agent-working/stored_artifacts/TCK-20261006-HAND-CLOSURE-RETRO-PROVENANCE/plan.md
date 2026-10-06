# Plan — TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE

1. New `tools/agent-monitoring/retro_provenance.py` (summary + renderers), wired into `generate_retro.compute_retro_metrics` (`run_summary.provenance`) and `generate`.
2. Owner decision (2026-10-06): headline average = measured/declared only; derived averaged beside it with n; unknown counted, never averaged.
3. Inert when no run carries `duration_source`, so earlier weeks render unchanged (the frozen-output tests still pass).
4. Docs: `docs/guides/agent_monitoring.md` section; the direction-doc row moves to "shipped (code)" with the baseline, post-landing measurement pending.
