---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Investigation: TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS

- M0b (`TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md`, row b): `--agent` with a `tools` allowlist applies to the MAIN session (no Bash; a plain run had it). So the read-only mechanism works; `roster.Role.tools` and `generate_agents.py` already render it.
- Every seat has a `may_write` grant, so no pure-review seat exists; no allowlist set. Owner decision needed if one should.
- Implementers have `may_write: ["**"]`, so `may_write` cannot be the exemption for them: only narrow grants and `owns` exempt, and the domain route decides.
- `route(path, from_domain)` on typical paths: src from agent-working is owned by rpg (event); tickets, drafts and REGISTRY are unowned (no event); `tests/tools/**` is a split including agent-working (no event).
- PreToolUse `additionalContext` is already used by an advisory hook in settings (secret scan), so it is a supported advisory channel.
- Message class has no machine marker; the plan's convention is a first-line class word, so the check is a first-line match and is advisory only.
