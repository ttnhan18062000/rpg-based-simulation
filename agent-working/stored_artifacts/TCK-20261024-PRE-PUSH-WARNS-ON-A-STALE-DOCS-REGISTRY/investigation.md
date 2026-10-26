---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY
artifact_type: investigation
tags: [delivery, process-improvement]
---

# Investigation

- `generate_registry.py` reads `docs/**/*.md` (minus a few skipped subdirs), the ticket folders under `agent-working/tickets/` and `agent-working/stored_artifacts/<ticket>/*.md`; `--check` exits 2 on drift. The only existing registry hook is the post-merge regen, so nothing warns before a push (#718 and #719 failed CI that way).
- Measured: `--check` takes about 5.8 s on this tree, within the hook's budget and run only when a source path changed, so no cheaper probe is needed.
- The skipped `docs/` subdirs (archive, parity_ledger, ...) can trigger the check without being indexed; that only costs the 6 s run and reports a true "current" result, so the path filter stays a simple prefix match rather than a second copy of the skip list.
- `default_run_command` reports a timeout as returncode 1, so "timeout says nothing" falls out of "only rc 2 speaks".
- docs_to_update: docs/guides/delivery_process.md
