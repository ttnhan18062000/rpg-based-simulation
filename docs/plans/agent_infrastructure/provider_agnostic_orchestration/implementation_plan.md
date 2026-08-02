---
status: historical
layer: ai
authority: P1
audience: developer
maturity: implemented-nonlive-activation-deferred
date: 2026-08-02
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Implementation Plan: Provider-Agnostic Agent Orchestration

> **Status: IMPLEMENTED FOR NON-LIVE PROVIDER PARITY; LIVE ACTIVATION DEFERRED (2026-08-02).**
> The provider-neutral contract, generated Codex guidance, non-live runtime proof, and controlled
> pilot capability chain have been completed and independently reviewed. This plan remains a
> historical implementation record; it does not authorize a live Codex workflow, a hook-bearing
> config, a monitoring append, or a pilot. Those actions remain blocked pending a future explicit
> owner decision and the governed human prerequisites.

## Objective

Enable Claude Code and Codex to follow one semantic agent-working process while
using their own supported configuration surfaces. Both providers must use the
same lifecycle, role obligations, gate decisions, artifacts, execution identity,
and monitoring semantics without requiring identical hooks, file layouts, or
tool APIs.

The migration must preserve the stable Claude workflow during rollout and keep
historical monitoring data readable. Missing optional historical fields are
acceptable; rewriting, deleting, or corrupting existing records is not.

## Preconditions — Must Be Recorded Before Implementation Tickets

1. **Discovery gate is corrected and closed.**
   - The `.agents` disposition must no longer claim `.claude/` is a Codex skill
     location.
   - The approved future arrangement must name the Codex-native surfaces:
     repository `AGENTS.md` for durable instructions and `.agents/skills/` for
     repository skills, with current legacy `.agents` content still treated as
     retired until regenerated/reviewed.
   - The closure summary must distinguish the provider-neutral replay proof
     from a real Codex adapter invocation.
2. **Scope is Linux-only for shared monitoring writes.** Windows and macOS
   remain explicitly unsupported until the writer protocol has evidence on each
   newly supported platform.
3. **A human owner approves the implementation epic boundary.** It starts with
   `implement-ticket` replay/shadow behavior only. It does not authorize
   cutover of all development or simulation workflows.
4. **Existing Claude behavior is a protected baseline.** No phase may replace
   or redirect the live `.claude/workflows/*.js` pipeline until the relevant
   Claude and Codex conformance/shadow tests pass.

## Architecture Boundary

```text
                         Canonical semantic source
                         agent-orchestration/
       roles · workflows · gates · artifacts · schemas · divergences
                                       |
               ------------------------+------------------------
               |                                                 |
      Claude adapter                                      Codex adapter
 CLAUDE.md + .claude/*                         AGENTS.md + .agents/skills
 native workflow/hooks                         + trusted .codex/* settings
               |                                                 |
               ---------------- normalized runtime ---------------
                                       |
                 shared gate checks, artifacts, monitoring contract
                                       |
                       append-only historical + new records
```

`agent-orchestration/` is the only semantic authority. Provider adapters may
translate invocation syntax, configuration, permissions, hook registration, and
payload parsing. They must not independently redefine workflow phases, terminal
statuses, gate policy, artifact requirements, or monitoring-field meanings.

## Non-Negotiable Data-Safety Rules

| Rule | Required implementation behavior |
|---|---|
| Existing JSONL is immutable historical input | Never rewrite, backfill, reorder, delete, or compact `agent-monitoring/*.jsonl` during this epic. |
| New schema is additive | New records carry `schema_generation`, `provider`, `execution_id`, `ticket_id`, and contract version; legacy fields remain readable through normalization. |
| Legacy gaps are explicit | Readers return `unknown`/`legacy` provenance for absent fields; they must not infer provider or execution identity from unreliable strings except in documented best-effort views. |
| Writes are atomic and append-only | The approved Linux lock-file protocol guards every new shared writer; no provider writes until it uses the common writer boundary. |
| Migration is reversible | New adapters/configuration are additive and feature-flagged. Disabling Codex must leave the live Claude path and historical data unchanged. |
| Verification does not mutate source data | Fixtures, replays, stress tests, and migration tests use snapshots/read-only inputs or temporary copies only. |

Before any writer change, capture a **read-only baseline manifest**: record
counts, byte sizes, SHA-256 hashes, parser/validator result, and known legacy
warning count for each JSONL file. After every writer/reader migration, rerun
the same manifest and require equality for pre-existing files except for
intentional new append records made by an explicitly identified test or live
execution. No ticket may claim data preservation from a clean-tree assumption
alone.

## Common Contract and Adapter Model

### Canonical contract contents

Create `agent-orchestration/` incrementally with a small versioned core:

```text
agent-orchestration/
  README.md                         # ownership, compatibility, generation policy
  contract.yaml                     # contract version, global invariants, providers
  workflows/implement-ticket.yaml   # first vertical slice only
  roles/<role>.yaml                 # first-slice role obligations
  skills.yaml                       # semantic skill catalog and provider mappings
  monitoring-schema.yaml            # current/new generation and legacy policy
  hook-events.yaml                  # normalized lifecycle-event vocabulary
  intentional-divergences.md        # reviewed semantic differences
```

YAML remains human-reviewable. Python validation models are generated or
derived from the YAML contract and must fail clearly on malformed or incomplete
definitions. Contract generation/validation must be deterministic, run without
network access, and never modify provider files unless invoked through an
explicit generation command.

### Provider-native delivery

| Semantic concern | Claude Code | Codex | Constraint |
|---|---|---|---|
| Durable guidance | `CLAUDE.md` | root `AGENTS.md` | Both derive/reference the same contract intent; neither embeds divergent policy. |
| Reusable skills | `.claude/skills/` | `.agents/skills/` | Provider-native copies are generated/reviewed outputs, never two hand-maintained semantic sources. |
| Roles/workflow entry | `.claude/agents/`, `.claude/workflows/` | Codex-supported configuration/commands from `.codex/` plus contract adapter | Exact Codex role shape is verified by fixture before enabling. |
| Hooks/settings | `.claude/settings.json` | trusted `.codex/` configuration | Normalize events at the boundary; do not assume payload equivalence. |

The initial Codex `AGENTS.md` must be concise and progressive: repository
orientation, mandatory verification, pointer to the shared contract, and
provider-specific setup only. It must not copy the entire Claude instruction
file or load all workflow detail into every request.

## Delivery Sequence

### Phase 0 — Baseline, safety harness, and contract skeleton

**Goal:** establish invariant checks before any provider runtime behavior.

- Create the read-only monitoring baseline manifest and legacy-reader fixture
  corpus covering each known historical schema generation.
- Add a contract validator and schema-version compatibility tests.
- Define a provider-neutral execution envelope:
  `provider`, `execution_id`, `ticket_id`, `run_id`, `workflow`, `phase`,
  `contract_version`, and `schema_generation`.
- Add tests asserting current Claude records remain readable before and after
  the new reader is introduced.
- Create no `.codex/` hook registration and modify no production writer in
  this phase.

**Exit criteria:** baseline manifest is reproducible; contract validation is
deterministic; legacy parser fixtures pass; existing Claude workflow tests are
unchanged.

### Phase 1 — Shared semantics for `implement-ticket`

**Goal:** express the first vertical slice in the contract without rerouting
live Claude execution.

- Model standard and hotfix `implement-ticket` phases, terminal statuses, role
  responsibilities, required artifacts, and gate outcomes.
- Define contract conformance as explicit assertions: every provider adapter
  must expose the same phase order, terminal-status vocabulary, gate intent,
  and artifact obligations.
- Generate/read-only render a Claude adapter representation and compare it to
  the existing workflow. Differences require an entry in
  `intentional-divergences.md` and human approval.
- Keep current `.claude/workflows/implement-ticket.js` authoritative for live
  execution until shadow parity succeeds.

**Exit criteria:** contract and Claude conformance fixtures pass for the first
slice; every divergence is intentional and reviewed; no live workflow behavior
changes.

### Phase 2 — Codex guidance, skill, and capability fixtures

**Goal:** create the smallest supported Codex adapter surface safely.

- Add root `AGENTS.md` and regenerated `.agents/skills/` only from reviewed
  canonical material; do not reactivate stale legacy `.agents` files.
- Add minimal trusted `.codex/` configuration only after a fixture confirms
  project trust, matcher behavior, and an actual hook payload for each event
  used by the first slice.
- Run isolated Codex fixture experiments in a scratch directory outside the
  production project configuration. Record payload schema, timing, and trust
  prerequisites as durable fixtures, not prose-only claims.
- Verify subagent/role behavior only to the degree needed for the first slice;
  represent unsupported differences in `intentional-divergences.md`.

**Exit criteria:** Codex discovers the intended `AGENTS.md` and skills;
required hook payload fixtures are captured; no project production hook is yet
enabled; Codex adapter conformance fixtures pass.

### Phase 3 — Monitoring writer and reader migration

**Goal:** make new provider-attributed records safe without damaging history.

- Extract a common Linux-only append writer using the approved lock-file
  protocol, bounded retry, stale-lock recovery, and malformed-line handling.
- Route new Claude and Codex writes through that common boundary only after
  stress, crash/recovery, and concurrent two-writer tests pass.
- Add additive schema fields to new records. Retain reader support for every
  recorded legacy shape; never run a historical rewrite.
- Update validation, query, retro generation, derived monitoring index, and
  dashboard ingestion to group/filter by provider and execution identity while
  visibly labeling legacy unknowns.
- Use explicit writer health/error events; monitoring failure remains
  non-blocking for workflow completion but observable.

**Exit criteria:** Linux concurrent-write tests pass; baseline historical
records still validate/read with the same or a documented-improved warning
profile; dashboard/retro queries preserve legacy visibility; no non-Linux
writer is enabled.

### Phase 4 — Real Codex replay and shadow parity

**Goal:** prove a Codex adapter can execute the first slice before live work.

- Execute the replay fixture through the real Codex adapter, not merely the
  provider-neutral Python replay runner.
- Assert zero ticket edits, zero production-hook invocation, and zero
  monitoring-corpus writes during replay.
- Compare Claude and Codex replay outputs: phase completion, gate result,
  required artifact references, normalized event intent, and declared
  divergences.
- Run shadow mode against selected `implement-ticket` inputs. Claude remains
  the only live writer/editor; Codex output is isolated and compared.

**Exit criteria:** replay and shadow parity are evidence-backed; differences
are either fixed or registered as intentional; no unexplained gate/status or
artifact mismatch remains.

### Phase 5 — Isolated live Codex pilot

**Goal:** permit one recoverable, low-risk live ticket path.

- Select an explicitly designated standard/hotfix ticket with a human owner,
  rollback plan, and no concurrent provider execution of the same work.
- Enable only the hooks/events proven in Phase 2 and the common writer proven
  in Phase 3.
- Require pre/post snapshots of the ticket and monitoring corpus plus normal
  test/gate checks.
- Keep the Claude workflow intact as the fallback. Disabling the Codex adapter
  must require configuration rollback only, not data repair.

**Exit criteria:** pilot completes with attributable, valid monitoring records;
contract conformance and mechanical gates pass; no data-integrity regression;
human review explicitly approves widening scope.

### Phase 6 — Controlled expansion and cutover review

**Goal:** migrate only proven workflows, one at a time.

1. Expand `implement-ticket` coverage only after multiple successful pilots.
2. Add `create-tickets`, then `implement-epic`, each with its own contract,
   fixture, conformance, shadow, and pilot evidence.
3. Defer simulation/lab workflows until development-workflow parity is stable.
4. Before retiring any legacy provider path, run a cutover review covering
   replay parity, monitoring integrity, historical readability, operational
   documentation, and rollback feasibility.

## Test and Evidence Matrix

| Concern | Required evidence | Failure response |
|---|---|---|
| Contract validity | YAML/model validation and deterministic-generation test | Block adapter generation. |
| Claude preservation | Existing workflow/gate regression suite and behavior diff | Revert/add feature flag; do not redirect Claude. |
| Codex configuration | `AGENTS.md`/skill discovery and real hook-payload fixtures | Keep Codex adapter disabled. |
| Monitoring integrity | Baseline manifest, append stress/recovery tests, legacy parser fixtures | Disable new writer; preserve raw corpus for diagnosis. |
| Replay containment | Static forbidden-call test and real-path no-mutation snapshot | Block replay/pilot. |
| Provider parity | Phase/status/artifact/event fixture comparison | Record divergence or block promotion. |
| Live pilot | Human-owned ticket, pre/post snapshots, gates/tests, rollback drill | Revert adapter configuration; do not repair historical files in place. |

## Rollback and Incident Policy

- **Configuration rollback:** disable the Codex adapter/hook registration and
  feature flag. Do not delete its output or modify historic records.
- **Writer incident:** stop new provider writes, retain raw JSONL unchanged,
  capture an incident manifest, and diagnose using a derived read-only index or
  copied fixture—not a repair-in-place script.
- **Reader incident:** fall back to the previous parser for display/query use;
  keep the new reader behind a version flag until compatibility tests are fixed.
- **Contract incident:** pin the last validated contract version and adapter
  render; rollback via version selection, not manual edits to generated files.
- **Data repair:** if an append is malformed, preserve the original evidence,
  publish a separate remediation decision, and use additive quarantine or
  reader-side exclusion. Never silently delete or rewrite historical lines.

## Explicit Non-Goals

- A big-bang rewrite of `.claude/` or deletion of `.agents/`.
- Exact duplication of provider configuration syntax or hook payloads.
- Cross-platform shared monitoring writes before evidence exists.
- Migration/backfill of historic monitoring records.
- Enabling all agent workflows, simulation workflows, or autonomous Codex
  dispatch in the first implementation epic.
- Treating cache/search/context-efficiency work as part of this migration; that
  is the separately proposed context-efficiency epic.

## Proposed Ticket Groups

Create tickets only after the discovery gate closes. The implementation epic
should contain, at minimum:

1. Baseline manifest and legacy compatibility fixtures.
2. Contract core + validator for `implement-ticket`.
3. Claude contract conformance adapter/tests (no behavior change).
4. Codex guidance/skills arrangement plus real hook-payload fixture capture.
5. Linux common monitoring writer + additive reader/query/dashboard support.
6. Real Codex replay adapter and parity suite.
7. Shadow-mode comparison and isolated live-pilot guardrails.

Each ticket must declare: allowed mutation surface, historical-data invariant,
provider scope, required rollback action, and exact promotion evidence. No
ticket may combine writer implementation, historical-data remediation, and
provider live rollout.

## Completion and Deferral Disposition

The non-live delivery groups have been implemented, tested, and independently
reviewed. The remaining live pilot/activation work is intentionally deferred
under the two blocked tickets; it is not a remaining implementation omission in
this plan and must only resume with a fresh human decision.

## Related Material

- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`
- `docs/architecture/agent_orchestration_contract.md`
- `docs/ai/agents_dir_disposition.md`
- `docs/ai/monitoring_writer_decision.md`
- `docs/ai/codex_capability_matrix.md`
- `docs/ai/replay_fixture_spec.md`
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`

---

*Raised: 2026-07-21. This draft is intentionally conservative: it preserves
the stable Claude path, treats historic monitoring files as immutable evidence,
and requires replay, shadow, and pilot evidence before any provider cutover.*
