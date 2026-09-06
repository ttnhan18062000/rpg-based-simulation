---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, workflows, process-improvement]
---

# Agent Orchestration Contract

*Filename/convention note: this doc follows the descriptive-slug + frontmatter +
unnumbered-title shape of the two real ADR-shaped precedents in this directory
(`simulation_watchdog.md`, `performance_optimization.md`), not the numbered
`ADR-[XXX]` / `adr-NNN-*.md` template in
`.claude/skills/architecture/trade-off-analysis.md`. That template is followed by
zero of the 9 files that existed under `docs/architecture/` before this one landed;
the frontmatter + `Status → Context → Decision → Rationale → Trade-offs →
Consequences → Revisit Trigger` shape is followed by both real ADRs. This is a
named decision for this and future `docs/architecture/` ADRs, not a silent
default.*

## Status
Proposed

## Context
This document is discovery output #2 of the 5-output exit gate defined in
`docs/plans/archive/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`
(archived — shipped)'s "Approval model and exit gate" section (lines 125-146): "A contract-format ADR,
including source ownership and adapter-generation or conformance strategy." The
parent discovery epic, `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`, is complete only
once all 5 listed outputs are reviewed and approved; this ADR does not by itself
authorize a follow-on implementation epic.

This ADR consumes three evidence-input tickets/docs, produced earlier in the same
discovery batch, as required inputs:

- `TCK-20260721-AGENTS-DIR-DISPOSITION` (`docs/ai/agents_dir_disposition.md`) —
  classifies every path under `.agents/` and settles on `.claude/` as the one
  approved active Codex/Claude instruction-and-skill location.
- `TCK-20260721-CODEX-CAPABILITY-MATRIX` (`docs/ai/codex_capability_matrix.md`) —
  re-verifies Codex's lifecycle hooks, project-trust behavior, and
  skills/configuration surfaces as of 2026-07-21.
- `TCK-20260721-MONITORING-WRITER-DECISION`
  (`docs/ai/monitoring_writer_decision.md`) — decides execution identity (§2) and
  evidences a candidate concurrent-write writer design (§3). This ADR treats §2's
  execution-identity model as an already-decided input; see the "Execution
  Identity (Consumed Input)" subsection below.

This ADR makes no final storage location or writer-implementation choice; it
records design decisions only, and creates no `agent-orchestration/` directory,
contract file, or runtime code.

## Decision

### Contract Representation and Format

The shared orchestration contract is YAML, for human-reviewable definitions,
with generated Python validation models. The source plan's `## Open Decisions`
#1 (`idea_provider_agnostic_agent_orchestration.md:428-430`) names this as its
"initial recommendation" ("YAML for reviewable definitions with generated Python
validation is the initial recommendation") without locking it in as final. This
ADR converts that recommendation into an actual decision.

**Status: Decided**

As of `TCK-20260727-CODEX-SKILL-COMPANION-ASSETS`, `skills.yaml` entries also carry an
optional `companion_assets: []` field — a list of paths relative to the skill's own
`.claude/skills/<id>/` directory, naming the non-`SKILL.md` files the skill needs alongside its
generated `SKILL.md` (e.g. reference docs, a `scripts/` subdirectory). `tools/agent_orchestration/loader.py`
validates it additively (defaults to `[]` when omitted, is not part of the required-key set), and
`tools/agent_orchestration_codex_adapter/generator.py::render_codex_guidance()` copies each
declared asset into `.agents/skills/<id>/` alongside the generated `SKILL.md`. It is a curated
per-skill allowlist, not a blind copy of every file physically present in a skill's directory —
some companion content may be intentionally excluded, and not every shipped asset is required to
be referenced by name in `SKILL.md`'s own body.

### Source Ownership

The shared contract lives under a new repository-root `agent-orchestration/`
directory, functioning as a source specification — not a second implementation —
per the source plan's proposed layout
(`idea_provider_agnostic_agent_orchestration.md:158-178`): `README.md`,
`contract.yaml`, `agents/<role>.yaml`, `workflows/<workflow>.yaml`,
`skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml`,
`intentional-divergences.md`. This directory is not created as part of this
ticket. This decision is subject to revisit if a future provider-runtime
implementation ticket surfaces contradicting evidence — see Revisit Trigger.

**Status: Decided**

### Versioning

`contract.yaml` carries a `version` field, named consistently with the
already-established `workflow_version` / `hook_schema_version` field-naming
pattern in `docs/ai/monitoring_writer_decision.md` §2 and the source plan's
monitoring-schema table (`idea_provider_agnostic_agent_orchestration.md:239-246`).
No versioning *scheme* (semver vs. simple integer generation number) is fixed
here — this is the thinnest-evidenced of the 5 decisions, with no direct
source-plan recommendation beyond the field's existence.

**Status: Proposed-pending-implementation-evidence**

### Provider-Adapter Boundary

`.claude/` and `.codex/` each translate the shared contract into provider-native
configuration. Per `idea_provider_agnostic_agent_orchestration.md:180-202`
("Thin provider adapters"): "The adapters may contain provider-specific payload
parsing, invocation, permissions, and hook registration. They may not silently
redefine workflow phases, terminal statuses, gate policy, or artifact
requirements." This is the best-specified of the 5 decisions — the source plan
gives a concrete translation table (durable guidance, subagent role, workflow
entry point, reusable skill, lifecycle hook) alongside the boundary rule itself.

**Status: Decided**

### Conformance Mechanism

Contract conformance tests must exist for both provider adapters (source plan
Workstream F, item 1), verifying each adapter's translated configuration does
not diverge from the shared contract's phases, terminal statuses, gate policy,
and artifact requirements. This is the least-constrained of the 5 decisions —
the source plan gives no further detail on test shape, location, or invocation,
and this ADR does not invent one beyond the stated principle.

**Status: Implemented — all 4 named axes (phase_order, terminal_status, gate_policy,
artifact_requirements) have conformance tests as of TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER
(2 axes) and TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST (2 axes).**

### Execution Identity (Consumed Input)

This subsection is not one of the 5 decisions above — it consumes an
already-decided input from `TCK-20260721-MONITORING-WRITER-DECISION`
(`docs/ai/monitoring_writer_decision.md:91-142`, §2 "Execution Identity Model").
Quoted verbatim:

> ### Immutable per-execution key
>
> ```
> execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"
> ```
>
> Stdlib-only (`secrets` + `time`), no new dependency. Example:
>
> ```
> claude-code-TCK-20260721-MONITORING-WRITER-DECISION-1774276800123-a1b2c3d4
> ```
>
> Generated fresh once per workflow execution. Never reused. Never treated as a
> lookup/join key across runs — two executions of the same ticket produce two
> distinct `execution_id` values by construction (the `unix_ts_ms` + random
> suffix guarantee this even for same-provider re-runs within the same
> millisecond-adjacent window).
>
> ### Human-readable run reference
>
> `run_id` is retained in its current shape/format, unchanged. It becomes a
> display/reference field rather than the execution's primary key — existing
> tooling and human readers keep the familiar `TCK-YYYYMMDD-SHORT-SCOPE` (or
> `EPIC-*`/`FOLDER-*`) shape.
>
> ### Stable cross-run join key
>
> `ticket_id` is promoted to an **explicit top-level schema field** — today it
> is only implicit inside `run_id`'s string shape. All records for all
> executions of the same ticket, by any provider, share the same `ticket_id`
> value. This is the field `TCK-20260713-MONITORING-SQLITE-INDEX`'s eventual
> read-side index and `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`'s downstream
> contract should join on — `execution_id` is never reused as a join key,
> `ticket_id` is.

The shared contract's monitoring schema carries these three fields as
already-decided inputs; this ADR does not choose their format or ownership
independently.

**Status: Consumed-as-input**

## Rationale

**Contract Representation and Format.** YAML with generated Python validation
gives non-engineer reviewers (and diff tools) a plain-text artifact to read
while still giving the runtime typed, validated structures to load — hand-written
Python models would require every review to happen in code, and pure YAML with
no validation layer would let malformed contract files reach the runtime
undetected. The source plan already steered toward this pairing; this ADR closes
the "or both" question the plan left open in favor of both, rather than picking
one exclusively.

**Source Ownership.** A dedicated repo-root `agent-orchestration/` directory
keeps the contract provider-neutral by construction — embedding it inside
`.claude/` would tie a shared specification to one provider's config surface and
invite exactly the "silently redefine" drift the Provider-Adapter Boundary
decision below forbids. A source-specification directory (not a second runtime)
also matches the source plan's explicit framing and avoids duplicating logic that
belongs in the shared runtime.

**Versioning.** Naming the field `version` and matching it to the existing
`workflow_version` / `hook_schema_version` pattern keeps one consistent
versioning vocabulary across the contract and the monitoring schema, so a future
reader does not have to learn two different version-field conventions for two
halves of the same system. The scheme itself (semver vs. integer generation) is
left open because no evidence source recommends one over the other yet — picking
one now would be inventing a decision, not recording one.

**Provider-Adapter Boundary.** Keeping adapters thin and non-authoritative over
phases/statuses/gate policy/artifact requirements is what makes "provider-neutral
contract" meaningful in practice — if either adapter could silently redefine
those semantics, the shared contract would stop being the single source of truth
and adapters would drift independently, defeating the purpose of a shared
contract at all.

**Conformance Mechanism.** Stating only the principle (conformance tests must
exist and must check divergence against the 4 named contract axes) rather than
inventing test shape/location avoids over-specifying an implementation detail
this discovery-tier ADR has no adapter code to validate against yet — the actual
test shape should be informed by the first real adapter implementation, not
guessed in advance of it.

## Trade-offs

- YAML-first means schema drift is only caught at generation/validation time,
  not authoring time — a malformed `contract.yaml` edit will not surface until
  the generated Python models are regenerated or validated, not the moment it is
  typed.
- A repo-root `agent-orchestration/` directory adds one more top-level path to
  this repo's discoverability surface (in the spirit of
  `docs/architecture/world_repository_layout.md`'s concerns about top-level path
  proliferation — noted here, not edited there).
- Thin evidence on Versioning and Conformance Mechanism means those two
  decisions carry more implementation risk than the other three: a future
  implementer will need to make additional judgment calls neither this ADR nor
  its source evidence has made yet. (Historical framing — kept as originally
  written. Conformance Mechanism's evidence gap has since been closed: see the
  updated status above and the Revisit Trigger note below.)

## Consequences

- Future provider-runtime implementation tickets should scaffold against this
  contract shape (YAML + generated Python validation, `agent-orchestration/`
  source ownership, the stated adapter boundary) rather than re-deriving it.
- Conformance tests become a gating requirement once provider adapters exist,
  per the Conformance Mechanism decision above.
- No immediate code change is required by this ADR itself — no
  `agent-orchestration/` directory, contract file, or runtime code is created as
  part of landing this document.

## Revisit Trigger
- Source Ownership (`agent-orchestration/` location) is revisited if a future
  provider-runtime implementation ticket's evidence contradicts the proposed
  layout.
- Versioning scheme is revisited once a concrete `contract.yaml` schema is
  drafted and a semver-vs-integer choice becomes load-bearing.
- Conformance Mechanism is revisited once the first provider adapter conformance
  test is actually written.
