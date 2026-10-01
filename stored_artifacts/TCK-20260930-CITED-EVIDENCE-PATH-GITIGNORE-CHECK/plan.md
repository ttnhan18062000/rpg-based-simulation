---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK
artifact_type: plan
tags: [ai]
---

# Plan

1. New `tools/gate_checks/cited_evidence_advisory.py`: `check_cited_evidence_paths(ticket_id, tier, root)` -> `(OK|WARN|NA, evidence)`. Citations are backticked tokens under `stored_artifacts/`, `staging_artifacts/`, `tickets/` with a file extension; wildcards, `{}` placeholders and the ticket's own file are skipped; a path absent on disk is skipped; a `staging_artifacts/X` citation is checked at `stored_artifacts/X`. `git check-ignore -v` names the matching rule; `git ls-files` finds untracked paths. Never raises.
2. Wire into `run_advisory_checks()` (not `run_static_precheck()`), so it never changes a verdict or the exit code.
3. `.gitignore` decision: keep the `stored_artifacts/**/*.json` rule (it keeps large generated JSON out; `.jsonl` is the existing convention and `manifest.json` is excepted). The WARN tells the author to store as `.jsonl`.
4. Docs: `docs/guides/delivery_process.md` advisory paragraph and `.claude/agents/done-checker.md` Step 0c (now all tiers, two advisories).
