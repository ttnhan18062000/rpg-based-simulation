# Agent Bookkeeping Determinism — Implementation Sequence

Epic: `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`. Source: `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` (raised 2026-07-10). Three child tickets, each fixing one instance of the same anti-pattern (agent-prompt "Step 0/0b" text carrying a purely mechanical instruction whose correctness depends on the agent reproducing it verbatim).

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260710-CURRENT-RUN-SIDECAR-BASH | P1, highest-confidence live-reproduced bug (`tool_call_count`/`cost_proxy_score` silently zeroed with no error). The ticket's own Assumptions section recommends sequencing it first, higher priority than C2, and shares the same Step 0/0b blocks in the same 3 workflow files. |
| 2 | TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH | P2, same class of bug as ticket 1 but lower stakes (`ts` is display/ordering only, not read by `generate_retro.py`'s duration logic). Shares the same Step 0/0b blocks in the same 3 files as ticket 1 — its own Assumptions section recommends sequencing after ticket 1 to avoid diff conflicts rather than editing concurrently. |
| 3 | TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT | P1, but architecturally heavier: no shared files with tickets 1-2 (touches `mechanics-auditor.md`/`mechanics_auditor_static.py`, not the JS workflow files), but requires reversing `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s prior explicit "out of scope" ruling on adding a pipeline call site, which needs Architecture-Review sign-off. Sequenced last so the two lower-risk, higher-confidence fixes land first. |

## Dependency Notes
- No hard code dependency between the 3 tickets — tickets 1 and 2 share files (coordination risk, not a blocking dependency) and are sequenced to avoid concurrent edits to the same Step 0/0b blocks; ticket 3 is fully independent of both.
- Ticket 3 may require an Architecture-Review decision (new call site vs. post-hoc audit mechanism) before its own Plan phase can proceed — this is a within-ticket gate, not a cross-ticket dependency.
