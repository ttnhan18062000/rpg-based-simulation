---
status: active
layer: ai
authority: P2
audience: developer
maturity: proposed-future-epic
date: 2026-07-31
tags: [ai, workflows, agent-monitoring, process-improvement, testing]
---

# Idea: Parity Ledger SQLite Index and Context Integration

> **Maturity: PROPOSED FUTURE EPIC.** This proposal improves parity-ledger
> retrieval, maintenance, and evidence health. It does not authorize a
> mandatory new workflow gate, a broad rewrite of historic ledger entries, a
> live Codex runtime action, or a replacement of the current reviewable YAML
> source without separate approval.

## Decision summary

Build a local, gitignored SQLite index over the parity ledger and make it a
first-class deterministic source for context packets. Keep the existing YAML
ledger as the reviewable, version-controlled source of truth. The first
delivery is **read-only Phases 0-2 only**: baseline, importer/index/health,
and deterministic impact-query equivalence. A record-oriented YAML mutation
tool is deliberately deferred behind a separate go/no-go decision after that
read-path hypothesis has been proved on real tickets. Agents must never edit
the database as the authoritative write path.

```text
docs/parity_ledger/*.yaml       reviewed canonical state
        │
        │ validated import + deterministic links + generation hash
        ▼
parity-index/parity.db          local derived read model, gitignored
        │                 ├── B-tree impact/test/constraint queries
        │                 └── FTS intent discovery, never a correctness gate
        ▼
ParityCandidateProvider
        ▼
ContextPacket / parity-phase evidence packet
        ▼
provider-neutral workflow adapters, initially shadow/advisory
```

This follows the project’s existing `agent-monitoring-index/monitoring.db`
pattern (derived, rebuildable SQLite over text-source records) and the
`knowledge-index/retrieval_cache.db` pattern (hash/generation based
invalidation). It deliberately does **not** use `knowledge-index/knowledge.db`
or its `sqlite-vec` extension for deterministic parity gates.

## Investment gates and sequencing

Only the following work is eligible for the first ticket batch:

1. Phase 0 baseline and v1 architecture decisions.
2. Phase 1 read-only import/index/health proof.
3. Phase 2 deterministic impact API and legacy-equivalence proof.

No mutation writer, structured-reference v3 rollout, workflow change, skill
regeneration, context-packet integration, or Codex-facing work is authorized
by that first batch. Each later phase needs the preceding exit evidence and a
fresh ticketing decision. This is intentional: the core hypothesis is that the
index selects better, narrower obligations than the present regex scan; it
must be proven before this project invests in write-path machinery or
cross-provider adoption.

## Why this is needed

The ledger is durable and useful, but its present retrieval model scales poorly
for both people and agents:

- It contains 1,936 entries over nine YAML files, with several very large
  subsystem files.
- Source-to-ledger impact selection currently derives links by regex extraction
  from free-text `v2_evidence`; it can miss renamed, differently formatted, or
  symbol-only references.
- The implementation workflow has a hard-coded canonical-file list that does
  not cover every ledger shard (notably `faction.yaml`).
- The declared schema requires evidence/test paths for `verified` and
  `divergent` entries, while the historic corpus contains many legacy entries
  without a `test_path`. This is an evidence-health gap, not a reason to make
  the entire corpus suddenly fail.
- The completed context-retrieval work can assemble a `parity_ledger_entry`
  candidate only from a hand-built fixture. It does not ingest the live ledger.

The target outcome is not merely faster search. It is a smaller, cited,
deterministically selected parity context for the particular ticket, phase,
changed symbols, and risk level.

## Goals

1. Make exact parity impact queries fast and deterministic for changed paths,
   symbols, tests, constraints, entry IDs, and tickets.
2. Decide, based on observed Phase 0-2 evidence, whether new/touched ledger
   entries need a validated record mutation interface or a lighter lineage
   preservation guard.
3. Supply real parity candidates to the existing context-packet machinery,
   bounded by phase/scenario/token policy.
4. Detect stale, malformed, broken, orphaned, and untested evidence links
   without retroactively claiming that old records are verified.
5. Preserve Git-readable review, stable entry IDs, and the existing YAML
   corpus throughout the migration.
6. Measure whether parity packets reduce broad ledger reading without reducing
   parity/test/architecture correctness.
7. Keep Claude Code and Codex on the same semantic parity process through the
   provider-neutral contract and generated guidance surfaces.

## Non-goals and hard boundaries

- Do not make a checked-in SQLite binary the only source of truth in the first
  implementation.
- Do not bulk-rewrite, renumber, delete, or backfill all historic entries.
- Do not use vector or semantic similarity to decide that a parity entry is
  affected. It may suggest candidates for human review only.
- Do not add a universal workflow preamble that injects the full ledger into
  every task.
- Do not make a missing legacy test path an immediate closure blocker for an
  unrelated ticket. New and touched P0 entries are governed first; corpus-wide
  remediation is separate, measured work.
- Do not alter the authoritative 32-phase simulation mutation pipeline or use
  this agent-tooling work to claim simulation behavior changed.
- Do not enable Codex hooks or introduce a new provider-specific writer. Use
  the existing provider-neutral retrieval-event/writer boundary when and only
  when a later approved phase needs observability.

## Current foundation to reuse

| Existing component | Reuse | Limitation this epic closes |
|---|---|---|
| `docs/parity_ledger/*.yaml` and `schema.json` | Canonical current state, stable IDs, human review | Free-text links and whole-file reading are inefficient. |
| `tools/parity_ledger_scan.py` | Compatibility baseline for P0 source-path impact | Regex/prose dependence and hard-coded shard coverage. |
| `tools/gate_checks/parity_updater_static.py` | Existing workflow cross-reference behavior | Uses derived text mapping rather than structured links. |
| `tools/agent-monitoring/build_index.py` | Derived/local/rebuildable SQLite operational model | Its `raw_json` rehydration model is not sufficient for high-selectivity parity joins. |
| `tools/retrieval_cache.py` | Versioned cache keys, stale rejection, privacy-safe metadata | Needs a parity corpus generation input. |
| `tools/context_packet_assembler.py` | Candidate and bounded-packet shape | Its parity adapter accepts fixtures only. |
| `tools/retrieval_events.py` and retro views | Provider-neutral, metadata-only effectiveness measurement | No parity-selection/reconciliation event semantics yet. |
| `agent-orchestration/` and generated `AGENTS.md` | Canonical provider-neutral workflow/role guidance | Current parity semantics must be extended there before provider-local instructions change. |

## Target data model

`parity-index/parity.db` is a derived index, generated from the reviewed YAML
files and optional structured verification artifacts. It is ignored by Git and
rebuildable from scratch. The first schema must use ordinary SQLite and FTS5
only; the implementation must verify FTS5 availability and retain an exact-ID/
path fallback if unavailable.

| Table/view | Purpose | Key fields |
|---|---|---|
| `ledger_generation` | Rebuild provenance and invalidation source | schema version, source manifest hash, built timestamp, importer version |
| `entries` | One current canonical entry | entry ID, shard, subsystem, text, priority, status, proof type, support boundary, canonical fragment hash |
| `code_refs` | Deterministic code linkage | entry ID, repo-relative path, relation, cited source hash; v1 is path-level only |
| `test_refs` | Test linkage and health state | entry ID, test file, optional node ID, relation, cited test hash/availability state |
| `constraint_refs` | Mechanics/engine/ADR/policy linkage | entry ID, document path, heading/anchor, relation |
| `ticket_refs` | Ticket/stored-artifact provenance where structured | entry ID, ticket ID, artifact path, relation |
| `entry_fts` | FTS5 search projection | ID, text, subsystem, status, support-boundary terms; discovery only |
| `entry_health` view | Derived health classification | unparseable ref, absent file, stale hash, missing test, legacy/unstructured, duplicate ID |
| `impact_candidates` view/query | Bounded deterministic selection | requested changed path/symbol/test → entry ID, selection reason, priority/status |

The index stores references, hashes, fields needed for selection, and concise
canonical text. It does not store raw agent conversations, tool payloads, or
unredacted monitoring content.

### Structured reference evolution

The first importer must accept the current `v2_evidence` and `test_path`
formats without changing their meaning. It extracts only references that can be
parsed with high confidence and labels all other text `legacy_unstructured`.
It must never invent links from prose. **V1 resolves the Graphify decision to
path-level links only.** It does not depend on Graphify symbol resolution,
whose update/rebuild reliability is currently insufficient for a load-bearing
parity gate.

For entries that are added or materially touched after adoption, introduce
additive structured fields such as:

```yaml
code_refs:
  - path: src/example/module.py
    relation: implements
test_refs:
  - path: tests/example/test_module.py
    node: test_expected_behavior         # optional
constraint_refs:
  - path: docs/mechanics/example.md
    anchor: conservation
    relation: governs
last_verified: 2026-07-31
```

Existing prose remains intact as rationale/history. Structured and free-text
representations will coexist indefinitely for historic and newly touched
entries; that recurring author/review cost is real, not a temporary migration
cost. Therefore structured fields are limited to machine-queryable references,
while `text`/`v2_evidence` retain narrative rationale. The v3 field names,
authoring burden, and transition rules require a separate post-Phase-2 decision;
no automatic mass conversion is permitted.

## Read path and context integration

### Deterministic parity queries

Provide a small provider-neutral library and CLI, with a stable machine output
schema:

```text
parity-index build [--check]
parity-index impact --changed-path … [--symbol …] [--test …]
parity-index entry ENTRY-ID
parity-index search --query … --filters …
parity-index health [--subsystem …] [--priority P0]
```

`impact` is the correctness path. It uses exact code/test/constraint links,
returns deterministic order (priority, status severity, stable entry ID), and
includes an explicit selection reason. FTS search is discovery-only and must
mark its results as non-deterministic suggestions that require a human/agent to
validate before a gate relies on them.

### Context packet adapter

Add a live `candidate_from_parity_index()`/provider module beside the existing
fixture adapter. It must:

1. Query `impact` first whenever changed paths or symbols are known.
2. Add an FTS candidate only for intent-based planning when exact impact has no
   result, and mark it `discovery-candidate`, never gate-evidence.
3. Re-read the selected YAML fragment and compare its hash to the indexed hash
   before constructing a packet. A mismatch rejects the stale result and
   requests/requires index refresh according to the scenario policy.
4. Map parity `priority` and parity `status` into the already-decided
   `parity_ledger_entry` packet vocabulary without coercing them to
   `docs/REGISTRY.yaml` freshness values.
5. Include linked tests and constraints as separate cited items only within the
   packet budget; summarize excluded candidates by reason/count.

The packet-cache key gains `ledger_generation`, normalized changed-path/symbol
set, scenario, policy version, and requested budget. Any source manifest/hash
change stale-rejects the query/packet cache entry. Cache rows remain hash/ID/
metadata only, per the retrieval retention/redaction policy.

### Phase-specific selection policy

Parity context is not a universal default. Initial policy:

| Workflow phase | Input | Packet contents | Mode |
|---|---|---|---|
| Investigate | ticket related code areas / known paths | bounded candidate obligations and governing constraints | shadow first |
| Architecture-Verify | implemented changed paths and risk | P0/P1 affected entries, constraints, unresolved health flags | shadow first |
| Test | changed paths and selected entries | linked tests plus missing/stale test-link flags | shadow first |
| Parity | actual `files_changed` and symbols | exact impact result, current entry state, required mutation/health outcome | can replace regex pre-selection only after equivalence evidence |

No packet may replace direct YAML/source/test reads for a high-impact decision.

## Write and management path — deferred decision

The database enables efficient lookup and validation; it is not directly edited
by agents. A Phase-3 decision must compare two remedies before committing to a
write path. The decision is prompted by a real recent failure mode: a status
change removed prior evidence text from `WORLD-076`, which was caught and
repaired by the existing review process. The alternatives are:

1. a narrow static lineage-preservation guard that flags a status change away
   from `verified` when the old evidence is no longer preserved in the new
   evidence/divergence fields; or
2. a record-oriented mutation tool that validates and applies narrowly scoped
   YAML mutations.

The mutation tool is **not** assumed to win. If the static guard closes the
observed failure mode with lower maintenance cost, retain direct reviewed YAML
editing and do not build a new writer. If evidence selects the mutation-tool
option, its proposed interface is:

```text
parity-record validate mutation.json
parity-record propose mutation.json --out staging_artifacts/<ticket>/parity_mutation.yaml
parity-record apply mutation.json
```

`mutation.json` has a versioned schema: operation (`add`, `update`,
`record-verification`), entry ID or deterministic new-ID request, expected
canonical fragment hash/revision, status/priority/proof fields, structured
references, ticket ID, and divergence/support-boundary information when needed.

`apply` must:

1. validate schema, unique ID/prefix/shard rules, transition rules, referenced
   file/node syntax, and P0 requirements for new/touched entries;
2. reject an optimistic-concurrency hash mismatch rather than overwriting a
   concurrent YAML edit;
3. create a narrow textual YAML diff only for the affected entry/shard;
4. run source validation and `parity-index build --check`/rebuild; and
5. emit an auditable mutation report with before/after hashes and no raw agent
   prompt text.

The initial writer, if approved, may require an agent to supply human-readable
`text` and prose evidence; structured references make only the
machine-relevant portion deterministic. A later, separately approved phase may
introduce append-only verification-history records, but this proposal does not
force a second source of truth now.

## Workflow, skill, and provider integration

The parity ledger is agent-working infrastructure. These changes begin only
after the read-path and context phases have separately passed their gates.
Update instructions in the following order to preserve provider-neutral
semantics:

1. **Canonical contract first.** Extend `agent-orchestration/` with the parity
   index/write/health vocabulary, selection policy, terminal/gate behavior,
   and a declared intentional divergence policy. Do not put semantic rules only
   in `.claude/` or `.codex/`.
2. **Generate provider guidance.** Update the Codex guidance generator inputs
   and regenerate root `AGENTS.md`/the declared `.agents/skills/` artifacts.
   Never hand-edit generated `AGENTS.md`.
3. **Claude agent/workflow.** Update `.claude/agents/parity-updater.md` and
   `.claude/workflows/implement-ticket.js` to request the indexed packet,
   use the record mutation report, and distinguish deterministic impact from
   FTS discovery. Retire the hard-coded ledger-shard list only after comparison
   evidence proves dynamic index coverage.
4. **Shared skills.** Update the contract-declared `implement-ticket`,
   architecture, testing, and agent-monitoring-retro skill guidance, then
   generate/synchronize the provider-specific companion assets. Do not create
   two hand-maintained semantic skill copies.
5. **Settings/configuration.** No hook registration or provider-specific
   configuration is needed for index build/query. The only initial operational
   control is a fail-open `PARITY_CONTEXT_SHADOW_ENABLED`-style feature flag
   or equivalent provider-neutral adapter setting. Any configuration surface
   must be documented as disabled by default and have a one-action rollback.
6. **Codex parity.** Codex uses the same library/CLI and context-packet/event
   schema once its runtime activation path is approved. This is an explicit
   schedule dependency on `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` and its
   child sequence, not an implementation assumption. The plan must not pretend
   this is live Codex runtime evidence before that sequence completes.

## Observability and effectiveness evaluation

Extend the existing retrieval-event family rather than inventing a parallel
writer. Events must contain metadata only:

- `ledger_generation`, index/query version, request scenario/phase, changed
  path/symbol count, cache state/reason, latency, candidate/selected counts;
- selected priority/status counts, exact-impact versus discovery counts, stale
  rejection and health-flag counts, packet budget/estimated return size; and
- adequacy verdict plus deterministic later joins to Parity/Test/Verify gate
  results where available.

Never record ledger excerpts, raw queries, raw YAML, raw source, or tool
payloads in monitoring.

The dashboard/retro needs views for:

- impact-query latency and cache hit/stale-rejection rate;
- candidates selected versus entries actually updated;
- exact-impact coverage and FTS discovery false-positive/acceptance rate;
- missing/stale/broken P0 and non-P0 link counts over time;
- packet size/search-count proxy versus parity failures, rework, and test
  outcomes; and
- provider-separated results once more than one provider has real traffic.

Promotion from shadow to a workflow-provided packet requires the existing
context-retrieval promotion thresholds plus parity-specific proof that the
index catches every reference selected by the legacy scan on a representative
fixture corpus, and that no newly observed missed obligation is attributable to
the packet narrowing.

## Delivery sequence

### Phase 0 — Baseline and v1 architecture decision

- Capture an immutable manifest of all current ledger files, entries, IDs,
  status/priority counts, source/test parse coverage, and current legacy scan
  output for fixed changed-path fixtures.
- Decide YAML-to-index source ownership, FTS5 availability/fallback, shard/ID
  rules, output schema, the v1 path-level-only link boundary, and CLI/module
  ownership (`tools/parity_index.py`/`tools/parity_record.py` versus a package
  under `tools/parity_ledger/`).
- Record the current schema-versus-historic-data discrepancy explicitly;
  classify entries rather than silently changing statuses.
- Define the Phase-2 equivalence fixture corpus and success criteria before
  implementation; it must include the currently excluded `faction.yaml` case.

### Phase 1 — Read-only importer, index, and health report

- Build `parity-index/parity.db` from every current ledger shard, with an
  input manifest and atomic replacement of the derived database.
- Implement schema/import errors, duplicate-ID checks, link parsing confidence,
  health classifications, standard SQL indexes, and FTS fallback.
- Prove builds are deterministic for unchanged source and never modify YAML.

### Phase 2 — Deterministic impact API and legacy-equivalence proof

- Implement exact `impact`, `entry`, and `health` APIs/CLI output.
- Compare index results to current `parity_ledger_scan` and
  `parity_updater_static` behavior on a versioned fixture set; document every
  intentional improvement/difference, including all-shard coverage.
- Keep the existing workflow gates unchanged; this is a read-only shadow
  selection source.

### Gate A — Read-path payoff review

- Use the read-only impact query on a predeclared set of real tickets or
  ticket-like fixtures and review false negatives, false positives, selection
  size, and analyst effort against the existing scan.
- Proceed to any write/context work only if the index demonstrates a material
  precision, coverage, or context-size advantage without a regression in
  obligation recall. Otherwise retain the present ledger and close or backlog
  the later phases.

### Phase 3 — Maintenance-mechanism decision

- Produce a standalone, reviewable decision comparing the lighter static
  lineage-preservation guard to `parity-record` on observed failure modes,
  implementation/maintenance burden, concurrent edit safety, and expected
  evidence quality.
- Resolve the v3 structured-reference authoring contract only if it is required
  by the selected mechanism or proven read-path value; explicitly account for
  permanent coexistence with free-text evidence.
- This phase may decide **not** to create a mutation tool.

### Phase 3b — Selected maintenance mechanism (conditional)

- If Phase 3 selects the static guard, implement it with focused regression
  fixtures and preserve direct YAML authoring.
- If Phase 3 selects `parity-record`, implement validate/propose/apply with
  optimistic concurrency, atomic YAML write/rollback, and a structured mutation
  artifact.
- For either choice, require structured links only where evidence exists for
  new/touched entries; leave untouched historic entries explicit legacy records.

### Phase 4 — Context adapter and cache integration

- Build the live parity-index candidate provider and hash revalidation path for
  `ContextPacket`; replace fixture-only coverage with real-ledger integration.
- Extend retrieval cache invalidation and event wrappers using ledger generation
  and source hashes.
- Add offline retrieval fixtures: known changed paths/symbols must return the
  expected authoritative P0/P1 entries, tests, and constraints within a bounded
  packet budget.

### Phase 5 — Workflow/skill shadow integration

- Extend the canonical orchestration contract and generated guidance.
- Wire the packet in shadow/advisory mode for the named phases only. It must
  fail open, never alter a gate result, and never inject content into a working
  agent prompt until the promotion gate passes.
- Update Claude instruction surfaces through generation/conformance checks.
  Codex guidance may be generated and structurally checked, but any live Codex
  parity claim is blocked on the separate runtime-activation epic.

### Phase 5a — Promotion-audit design decision

- Create a dedicated decision record for the parity-specific fixture corpus,
  shadow sample duration/floor, recall audit, and attribution method before
  evaluating promotion. Do not choose these values opportunistically after
  observing shadow results.
- Budget this as its own standard ticket, following the precedent of
  `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS`; it is not an inline task in
  the Phase-5 implementation ticket.

### Phase 6 — Selective promotion and legacy scan retirement

- Evaluate the promotion thresholds using real shadow evidence and a reviewed
  parity-specific recall/false-negative audit.
- For approved scenarios only, make the exact index result the pre-selection
  source for the Parity phase while retaining direct source reads and a one-flag
  rollback to the legacy scan.
- Remove hard-coded shard lists and regex-only dependency from workflow gates
  only after backward-comparison evidence, migration notes, and human approval.

### Phase 7 — Continuous evidence health

- Run scheduled/on-demand health reports, maintain evaluation fixtures, and
  enrich links when an entry is naturally touched.
- Use retro/dashboard evidence to tune packet budgets and decide whether a
  future append-only verification-history store is justified.

## Verification matrix

| Area | Required proof |
|---|---|
| Source safety | Build/check commands leave all parity YAML byte-identical; malformed input leaves no partial DB/YAML change. |
| Index correctness | Row/ID/status/priority parity with source; duplicate and unparseable records are reported deterministically. |
| Impact correctness | Fixture changed paths/symbols select expected entries with stable reasons/order; unknown paths return explicit no-match, never a fabricated subsystem. |
| Health | Broken source/test references, stale hashes, missing structured links, and legacy gaps are classified without coercing status. |
| Maintenance decision | The static lineage guard and `parity-record` alternatives are compared against the observed evidence-loss failure; only the selected option receives implementation tests. |
| Mutation safety (if selected) | Validate/propose/apply rejects stale revision, invalid ID, invalid reference, duplicate ID, and incomplete touched P0 evidence; successful mutation is a narrow textual diff. |
| Context | Live parity candidates re-read/hash-check source; cache rejects stale ledger generation; budget/excluded summaries meet `ContextPacket` contract. |
| Workflow | Shadow path is fail-open, disabled by default, cannot affect terminal status, and preserves legacy behavior with the flag off. |
| Provider parity | Canonical contract/generator tests prove Claude and Codex receive equivalent parity semantics; live-provider metrics are marked unavailable until real traffic exists. |
| Observability/privacy | Event schema tests permit only IDs/hashes/counts/scores/reason codes; retro/dashboard aggregation works with missing/legacy fields. |
| Rollback | Removing the derived DB or disabling the shadow flag leaves YAML, historic monitoring, and legacy workflow behavior unchanged. |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| A database becomes an opaque second source of truth | YAML remains canonical; DB is ignored, manifest-backed, rebuildable, and never edited directly. |
| Old prose cannot be parsed reliably | Parse only high-confidence references; report `legacy_unstructured`; do not infer links. |
| New P0 enforcement blocks unrelated work | Apply strict structured-link/test validation to new or touched entries first; track backlog health separately. |
| FTS results are mistaken for compliance evidence | Mark discovery candidates distinctly; gates use exact structured impact only. |
| Context packets hide a missing obligation | Shadow first, compare to legacy scan/evaluation fixtures, require source-hash revalidation and promotion evidence. |
| New workflow ceremony outweighs benefit | Scope packets to parity-relevant phases; measure search-count/packet-size and gate-quality outcomes. |
| Mutation tool adds more machinery than it saves | Gate it behind Phase-2 payoff evidence and a dedicated comparison with the focused static lineage guard. |
| Structured/free-text duplication creates permanent maintenance cost | Restrict structured fields to machine-queryable references, preserve prose as rationale, and require the Phase-3 decision to justify each new authoring field. |
| Graphify instability affects index correctness | V1 is path-level only; symbol-level Graphify linkage remains deferred until its generation/reliability contract is proven. |
| Provider drift | Contract-first semantics, generated guidance, adapter conformance tests, and provider-separated metrics. |
| Codex activation is delayed | Keep early phases provider-neutral/read-only; make live Codex parity an explicit external scheduling dependency rather than a hidden blocker. |
| SQLite corruption/partial rebuild | Build to a temporary file, validate, atomically replace; source YAML remains recoverable authority. |

## Open decisions before tickets are created

1. Should structured verification history remain only in ticket artifacts for
   this epic, or is an append-only parity-evidence text source justified now?
2. After Phase 2, does the observed evidence-loss risk justify `parity-record`,
   or does the lighter lineage-preservation static check suffice?
3. If structured references are approved, what exact field names and
   status-transition rules are adopted for the v3 YAML schema?
4. Which test references may be auto-validated as pytest node IDs versus
   retained as file-level references due to existing multi-test string formats?
5. Symbol-level Graphify resolution is explicitly deferred from v1. What
   reliability/contract evidence is required before a later phase reopens it?
6. What user-facing CLI ownership/location best fits existing tooling:
   `tools/parity_index.py`/`tools/parity_record.py` or a package under
   `tools/parity_ledger/`?
7. Which representative fixture corpus and sample duration are sufficient for
   the separately ticketed parity-specific shadow-to-promotion audit?

## Related material

- `docs/parity_ledger/schema.json`
- `tools/parity_ledger_scan.py`
- `tools/gate_checks/parity_updater_static.py`
- `.claude/agents/parity-updater.md`
- `.claude/workflows/implement-ticket.js`
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
- `docs/engine/contracts/context_packet_contract.md`
- `tools/context_packet_assembler.py`
- `tools/retrieval_cache.py`
- `tools/agent-monitoring/build_index.py`
- `docs/observability/retrieval_retention_redaction_policy.md`
