---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE
artifact_type: plan
tags: [ai, process-improvement, governance]
---

# Plan

Investigation-only ticket; no production code.

1. Design ran the class-1 probes (disposable `claude -p` sessions in a scratch repo) and drafted the record and a 7-edit plan patch.
2. Implementer re-cut a branch from origin/main, applied `plan_edits.patch` with `git apply -p1` unchanged, copied the record and `.jsonl` evidence into this directory (`probe_settings.json` renamed to `.jsonl` because `.gitignore` drops `stored_artifacts/**/*.json`; the one reference in the record was updated).
3. Class-2 items (live terminals, power loss, crash mid-rebase) are recorded as not verified, per the owner's decision on 2026-10-03; plan 9.5 stays "unverified until M0c".
4. Close by hand-orchestration; regenerate the docs registry and knowledge index.

Out of scope: any hook, settings or registry change; M1 and M2 children.
