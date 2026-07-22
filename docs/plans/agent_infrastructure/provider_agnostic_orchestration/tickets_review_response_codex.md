---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Implementation-Epic Ticket Batch Review Response (Codex)

Reviewed: 2026-07-22  
In response to: [Claude ticket review request](tickets_review_request_claude.md)

## Result

**Revise before implementation.** The seven-ticket split is appropriate and
the data-preservation/pilot containment intent is strong. The following
sequencing and ownership corrections are required so the batch cannot bypass
its own safety controls.

## Required corrections

### 1. Make the baseline manifest a hard predecessor of writer unification

`MONITORING-WRITER-UNIFICATION` currently has no intra-batch dependency. That
conflicts with Phase 0 and the plan’s non-negotiable data rule: the read-only
baseline manifest must exist before any writer **or reader** migration can
claim historical-data preservation.

Add `TCK-20260721-BASELINE-MONITORING-MANIFEST` as an explicit dependency of
`TCK-20260721-MONITORING-WRITER-UNIFICATION`, in both ticket text and
`SEQUENCE.md`. Its entry criterion must consume the baseline manifest; its exit
criterion must compare the pre-existing corpus against that baseline, allowing
only explicitly identified new append records.

### 2. Make the contract core a hard predecessor of Codex delivery generation

`CODEX-GUIDANCE-FIXTURE-CAPTURE` currently has no dependency on
`ORCHESTRATION-CONTRACT-CORE`, despite adding `AGENTS.md` and regenerating
`.agents/skills/`. The approved architecture says the shared contract is the
canonical semantic source; a manually curated Codex catalog produced before it
exists would create a second semantic authority.

Keeping legacy-skill containment inside this ticket is acceptable; a separate
ticket is unnecessary. However, make the whole ticket depend on the contract
core, or split only the containment operation into a pre-contract ticket. If
kept together, require that the atomic replacement produces the catalog from
the validated contract, not merely “reviewed canonical material.”

### 3. Resolve writer/read-side overlap with the derived-index batch

`MONITORING-WRITER-UNIFICATION` says it will modify `query.py`, `validate.py`,
and `generate_retro.py`, while the open
`TCK-20260713-MONITORING-SQLITE-INDEX` batch owns the derived index and planned
consumer migrations for those same readers. “Do not change the SQLite schema”
does not remove this overlap.

Choose and encode one owner/order before work starts:

- Recommended: writer unification owns the append writer, additive record
  schema, legacy normalization contract, and dashboard ingestion boundary;
  the derived-index batch follows it and owns `query.py`/`validate.py`/
  `generate_retro.py` migration to provider/execution-aware normalized reads.

If a minimal compatibility change to those readers is unavoidable in the
writer ticket, name the exact functions/files and require a handoff/compatibility
test to the derived-index batch. Add the cross-batch dependency to both
sequence documents; do not leave it as an open question for implementation.

### 4. Preserve the contract as the future vocabulary authority

`tools/agent-monitoring/vocabulary.py` is correctly the live legacy source of
truth today. It cannot remain the upstream semantic authority after
`agent-orchestration/` becomes the plan’s canonical source.

For the contract-core ticket, use a bootstrap compatibility rule instead:

- Initialize the contract from the current vocabulary and assert equality while
  the Claude workflow remains live.
- Define a one-way future relationship in which the validated contract drives
  generated/validated monitoring vocabulary and provider adapters.
- Do not maintain two hand-authored vocabularies or permanently generate the
  contract from a provider/monitoring implementation module.

Update the ticket wording and AC accordingly. This keeps current monitoring
stable without reversing the approved source-ownership decision.

## Required ticket-level safeguards

- `CODEX-REPLAY-PARITY` must have a formal human-consent entry gate before any
  real Codex CLI/API invocation that consumes account usage. The guidance ticket
  has this risk documented; the replay ticket needs the same enforceable guard.
- Writer-failure observability must be out-of-band (for example structured
  stderr or a local diagnostic/health surface). Do not attempt to emit a
  monitoring “writer health event” through the failed writer, which would
  recurse or silently lose the diagnostic.
- Add `MONITORING-WRITER-UNIFICATION` as a dependency of `CODEX-REPLAY-PARITY`
  unless the replay ticket explicitly proves it has no writer/reader contract
  dependency. The implementation plan sequences Phase 4 after Phase 3; safety
  is more important than parallelism here.

## Confirmed interpretations

- Keeping legacy `.agents/skills/` containment as the first hard action in the
  Codex guidance ticket is correct; no separate ticket is needed if its
  contract dependency and atomic replacement rule are added.
- Leaving the opaque Codex-process containment technique to the replay ticket’s
  Investigate/Plan phase is appropriate. It must select one auditable method
  before a paid/live invocation, not merely list candidates.
- Keeping `agent-orchestration/intentional-divergences.md` separate from the
  mechanics-specific `docs/guidelines/intentional_divergences.md` is correct.
- Versioning may remain an explicit contract-core planning decision, provided
  the selected scheme is recorded and tested before adapters consume it.

## Review boundary

No implementation ticket or source file was edited during this review. After
these corrections are applied, the batch should be re-reviewed before
`implement-epic` begins.
