# Investigation — TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT

## Correcting the ticket's own "on abandon: execute the revert runbook" instruction, before acting

Flagged by peer review before this ticket ran: that instruction was written when the MCP
registration was a temporary trial artifact. It is now permanent on `main` (PR #228), at the
user's own explicit request that Headroom be usable in this repository. Verified this directly
rather than taking it on trust: `.mcp.json` on `main` (confirmed via the earlier isolation
ticket's own work, re-checked here) has the `headroom` entry unconditionally, not gated behind
anything reversible by a routine ticket closure. Executing a revert here would silently undo that
permanent state — split the decision in the ticket itself (see Scope) rather than following the
original wording literally.

## Harm comparison: a real re-run, not a fabricated "after" number

Re-ran the exact same command the baseline ticket used
(`retrieval_baseline_metrics.py --harm-check-window-start 2026-09-16`) at this ticket's own later
moment. Same window start, both computed by the identical code path — the only thing that changed
is "now." Population grew from 42/252/4956 to 44/264/5033 (runs/events/tools), matching exactly
this batch's own additional ticket closures in between. All rates (`done_rate`,
`per_event_failed_rate`, `per_event_blocked_rate`) are unchanged.

## Why this harm comparison structurally cannot detect compression-induced harm

The trial (`TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`) was explicit-trigger-only by design
— every `headroom_compress` call was on a payload copied to `/tmp`, never on live session traffic.
No real agent work was ever routed through compression during either the baseline or the
"post-trial" window. This means the harm comparison, however clean its numbers look, is comparing
two windows of the *same uncompressed system* — it cannot speak to what would happen if real
session traffic were actually compressed, because that was never tested. Stated as an explicit
confounder in the verdict rather than let the clean numbers imply more than they can support.

## Cache-hit degradation: confirmed genuinely unmeasurable, not just difficult

The ticket's own Scope names this as a harm signal in its own right (per the plan doc's cache-
stability section). Checked `docs/agent-monitoring/schema.md`'s "What is not recorded" directly:
token and cache-hit data are not recorded, with "no workaround within the current platform." This
is the same platform limitation `TCK-20260708-AGENT-COST-OBSERVABILITY` already established. Not
attempted to work around here; recorded as an honest, stated gap in the harm check's own coverage.

## The payload-weighting reading, not just the raw range

Re-read the trial's own 4-payload table directly rather than re-summarizing from a prior turn's
own paraphrase. The single payload that compressed, `docs/REGISTRY.yaml`, is functionally an index
this repo's own `CLAUDE.md` already directs agents to query/filter rather than read whole
(`docs/REGISTRY.yaml` is the authoritative flat index...query it with grep or python3 -c
'import yaml...' before scanning raw directories`). Cross-referenced against
`TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS` (already shipped in the same
batch), which explicitly pushes agents toward ranged reads over whole-file reads — the opposite
direction from the condition that would make Headroom's own compression apply. This is why the
verdict states the payload-weighting point as the central finding rather than the raw 0%-99.5%
range.
