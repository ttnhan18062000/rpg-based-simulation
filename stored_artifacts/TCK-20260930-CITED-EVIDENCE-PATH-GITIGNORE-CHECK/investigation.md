---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK
artifact_type: investigation
tags: [ai]
---

# Investigation

- `.gitignore:239` `stored_artifacts/**/*.json`, `:240` `!stored_artifacts/**/manifest.json`. Verified with `git check-ignore -v`: `.json` ignored, `.jsonl` and `manifest.json` not.
- Existing advisory style: `tools/gate_checks/proof_plan_advisory.py`, plumbed through `run_advisory_checks()` in `done_checker_static.py`; the CLI prints `[advisory]` lines outside `any_fail`.
- Pre-close, a ticket cites its own `tickets/inprogress/` path and `staging_artifacts/` paths that migrate at close; both would false-WARN, hence the skip and the staging-to-stored resolution.
- A tracked file matching an ignore pattern (force-added) is not a clean-checkout problem; `git check-ignore` without `--no-index` already omits it, and the check also requires the path to be absent from `git ls-files`.
- Backticked-path extraction is deliberately narrow (open question in the ticket): prose paths without backticks are not checked.
