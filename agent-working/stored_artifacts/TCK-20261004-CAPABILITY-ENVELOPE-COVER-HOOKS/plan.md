---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Plan: TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS

1. Add `hooks` to `FIELDS`, `extract_hook_entries`, `load_hook_settings` (degrades on a missing, unreadable or non-object file).
2. `seed_registry` and `build_report`/`compute_diff` take the hooks settings; CLI gets `--hooks-path`.
3. Hooks-only `not_in_live` in the diff.
4. Document in `docs/ai/capability_envelope_baseline.md`; seed the 14 real hooks; tests.
Scope guard: no `settings*.json` edit, no hook behaviour change.
