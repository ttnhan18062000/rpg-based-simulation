---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW
artifact_type: investigation
tags: [agent-monitoring, data-quality]
---

# investigation — TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW

Source: RETRO-2026-W41 final note finding 6 and PR #603's known gap. `week_close.py` folded only `JSONL_KINDS`, so W41's 96 gate_verdicts shards stayed; manual_actions and role_boundary are bare files. `TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS` was dropped but has a DONE row pending in 2026-W42, which a W42 close would write to working_log.csv. `gate_ledger.shard_paths()` returns the bare canonical file first, then the per-identifier files, so folding is invisible to readers.
