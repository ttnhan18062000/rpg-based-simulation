---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN
date: 2026-10-05
tags: [ai, process-improvement]
---

# Plan: TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN

1. `_dump` single serialiser; `_splice_entry` entry-local upsert with parse-back verification and fallback.
2. `write_entry` reads the shard text once, calls `_splice_entry`, writes once; validation first and index rebuild last are unchanged.
3. Tests for the real shard, add, invalid entry, hand formatting, fallback. Spec sentence in `parity-updater.md`.
Scope guard: no shard reformat, no schema change, existing invalid entries untouched.
