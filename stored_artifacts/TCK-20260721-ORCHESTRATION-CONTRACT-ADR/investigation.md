---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-ADR
artifact_type: investigation
tags: [ai, workflows, process-improvement]
---

# Investigation — TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Current Behavior

### No ADR for this decision exists yet

`docs/architecture/` currently holds 9 files: `cognition_domain_ownership.md`,
`feature_pack_architecture.md`, `macro_interest_constraints.md`,
`observability_behavior_profiling_boundary.md`,
`observability_hot_path_safety_contract.md`, `performance_optimization.md`,
`simulation_watchdog.md`, `world_assembly_architecture.md`,
`world_repository_layout.md`. Zero `adr-*.md` files exist (confirmed by the
ticket's own Assumptions and independently by `ls`). This ticket's deliverable,
`docs/architecture/<name>.md`, does not exist yet — a gap to fill, not an error.

### The two real ADR-shaped precedent docs (read in full)

`docs/architecture/simulation_watchdog.md:1-46` and
`docs/architecture/performance_optimization.md:1-45` are the only two docs in
this repo that actually follow an ADR shape. Both:

- Frontmatter (lines 1-6): `status: active`, `layer: architecture`,
  `authority: P1`, `audience: developer`. No `tags` field present in either.
- Unnumbered `# <Title>` heading (`simulation_watchdog.md:8` = "# Persistent
  Simulation Watchdog"; `performance_optimization.md:8` = "# Simulation
  Performance Optimization") — no `ADR-XXX` prefix anywhere.
- Section order: `## Status` → `## Context` → `## Decision` → `## Rationale`
  → `## Trade-offs` → `## Consequences` → `## Revisit Trigger`. Both docs use
  this exact order, including the non-template `## Revisit Trigger` closing
  section neither template below has.
- `## Status` body is a single bare word (`Proposed` / `Accepted`), not the
  four-way `Proposed | Accepted | Deprecated | Superseded by [ADR-YYY]` menu
  the skill template prints literally.
- Filenames are descriptive slugs (`simulation_watchdog.md`,
  `performance_optimization.md`), not `adr-NNN-*.md`.

### The unused numbered ADR-XXX template (read in full, both copies)

`.claude/skills/architecture/trade-off-analysis.md:43-77` and
`.agents/skills/architecture/trade-off-analysis.md:43-77` are byte-identical
(diffed no differences found in the read output). Both prescribe:

- Title line `# ADR-[XXX]: [Decision Title]` (line 46).
- `## Status` body listing the four-way menu literally as template text
  (line 49).
- Section order `Status → Context → Decision → Rationale → Trade-offs →
  Consequences` — no `Revisit Trigger` section at all (lines 48-66).
- A "ADR Storage" section (lines 69-77) prescribing
  `docs/architecture/adr-001-use-nextjs.md`,
  `adr-002-postgresql-over-mongodb.md`, `adr-003-adopt-repository-pattern.md`
  as example filenames — the numbered-file convention.
- No frontmatter block anywhere in the template.

**Direct comparison confirms the ticket's own recommendation is correct**: the
numbered `ADR-[XXX]`/`adr-NNN-*.md` template is prescribed by a skill file but
followed by **zero** real docs in the repo (0 of 9 `docs/architecture/` files
use `adr-` in the filename or `ADR-` in the title). The two docs that actually
function as ADRs use frontmatter + unnumbered descriptive-slug filename +
unnumbered title + the seven-section shape above. This is a live-precedent-vs-
unused-template mismatch, not a close call.

### Evidence-input docs (read in full)

- `docs/ai/agents_dir_disposition.md` (frontmatter: `status: active,
  layer: ai, authority: P1, audience: developer`) — classifies every
  `.agents/` path into retain-and-migrate / archive-retire, and determines
  `.claude/` is the one approved active Codex/Claude instruction-and-skill
  location (lines 36-43). Explicitly a decision-record with zero file
  mutations under `.agents/` (lines 61-67, "What this doc does not do").
- `docs/ai/codex_capability_matrix.md` (same frontmatter shape) — verifies
  all ten Codex lifecycle hooks (`PreToolUse`, `PermissionRequest`,
  `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`,
  `SubagentStop`, `Stop`, `SessionStart`, `SubagentStart`), project-trust
  gating, and skills/configuration surfaces (`.agents/skills` discovery
  path, progressive disclosure, `$`-mention activation) as of 2026-07-21.
  Notes the `[agents]` subagent-role schema is only partially verified
  (pointer-only in the cached manual, §4/§7).
- `docs/ai/monitoring_writer_decision.md` (same frontmatter shape) —
  **already decides** execution identity (§2, lines 91-142): an immutable
  `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"`,
  a retained human-readable `run_id` display field, and `ticket_id` promoted
  to an explicit top-level join-key field (line 125-130, which explicitly
  names this ADR as "downstream" and states the field this ADR's contract
  "should join on"). Also recommends (not yet implements) Candidate 1 — a
  lock-file protocol (`os.O_CREAT | os.O_EXCL`) — for concurrent-write safety
  (§3, lines 146-161), evidenced only on Linux (§4).

### Source plan docs (read in full)

- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`
  — `## Proposed Architecture` §0 "Preconditions and decision gate" (lines
  112-122) lists the 5 items an ADR or the parent epic must record before any
  runtime/hook/monitoring migration starts; item 2 is "the contract
  representation (reviewable YAML, validated Python models, or both)". §1
  "Shared contract first" (lines 158-178) proposes a new repository-owned
  `agent-orchestration/` directory as a **source specification, not a second
  implementation**, with a concrete file layout (`README.md`, `contract.yaml`,
  `agents/<role>.yaml`, `workflows/<workflow>.yaml`, `skills.yaml`,
  `monitoring-schema.yaml`, `hook-events.yaml`,
  `intentional-divergences.md`). §2 "Thin provider adapters" (lines 180-202)
  defines the provider-adapter boundary: `.claude/` and `.codex/` translate
  the shared contract into provider-native config; adapters "may not silently
  redefine workflow phases, terminal statuses, gate policy, or artifact
  requirements." `## Open Decisions` #1 (lines 428-430) recommends "YAML for
  reviewable definitions with generated Python validation" as the initial
  contract-representation recommendation — a recommendation, not a locked
  choice this doc's own text treats as final.
- `..._ticket_handoff_codex.md` — Suggested Sequence row 4 (lines 58-59)
  scopes this exact ticket: "Decide contract representation, ownership,
  versioning, provider adapter boundary, execution identity, and conformance
  mechanism. This is a decision artifact, not a runtime migration," depending
  on children 1, 2, 3 (disposition, capability matrix, writer decision). Note
  this handoff doc's own phrasing still lists "execution identity" as
  something ticket 4 decides — superseded by the ticket's own corrected Scope/
  Out-of-Scope (see ticket body lines 35, 41, 47), which is authoritative over
  this now-stale handoff phrasing per the ticket's Codex-review correction.
- `..._finding_01_claude.md` — `WorkflowRegistry` (`src/lab/registry.py:31-111`)
  parses YAML frontmatter directly from `.agents/workflows/*.md` and
  `.agents/skills/*/SKILL.md`; `test_real_registry_contracts` is a currently-
  passing test coupled to that content. Relevant to this ADR only as
  background on why `.agents/` content is not treated as freely disposable —
  it does not change any of this ADR's 5 decisions, since the disposition
  ticket already resolved it by repointing the test at frozen fixtures
  (`agents_dir_disposition.md:57-59`).

### Ticket's own internal-consistency check (Codex-corrected)

The ticket body (read first, in full) is internally consistent on the
execution-identity boundary across all three sections the AC requires:
- Scope (line 35): "may specify how the shared contract carries/represents
  that identity, but must not choose its format or ownership independently."
- Out of Scope (line 41): "both are TCK-20260721-MONITORING-WRITER-DECISION's
  decisions to make; this ADR only consumes their output as a required
  evidence input."
- Acceptance Criteria (line 47): "it may specify how the shared contract
  represents/carries that identity, but does not choose its format or
  ownership independently; the ADR's Scope, Out of Scope, and Acceptance
  Criteria all state this same boundary with no contradictory wording between
  sections."

No contradiction found. This confirms the Codex-review correction mentioned in
the Request Summary (line 30) has already been applied to the ticket as
written — the investigation does not need to flag this as unresolved.

## Mechanics / Engine Constraints

Not applicable. This ticket concerns dev-tooling/agent-orchestration
infrastructure (an ADR under `docs/architecture/`), not simulation engine
mechanics. No chapter of `docs/mechanics/` or contract in `docs/engine/`
constrains this work — consistent with the identical finding in the sibling
`TCK-20260721-MONITORING-WRITER-DECISION` and `TCK-20260721-CODEX-CAPABILITY-MATRIX`
investigations (both confirmed via `mcp__knowledge-search__search_docs`, no
relevant hits for mechanics/engine content in this search either).

## Parity Ledger Overlap

None. No `docs/parity_ledger/*.yaml` subsystem (substrate, combat_movement,
strategic_cognition, town_resource, progression, social_narrative,
world_dynamics, infrastructure) covers agent-orchestration/dev-tooling
decision records. No parity ledger entry needs updating as a result of this
ticket.

## Prior Work

- **`stored_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/`** and
  **`stored_artifacts/TCK-20260721-CODEX-CAPABILITY-MATRIX/`** and
  **`stored_artifacts/TCK-20260721-MONITORING-WRITER-DECISION/`** (all done,
  same discovery batch) — establish this batch's evidence-density and
  containment precedent: exact file:line citations, explicit "read in full"
  verification style, decision-record deliverables with zero production-file
  changes, and each doc's own "What this doc does not do" closing section
  making non-scope explicit. This ADR should follow the same discipline.
- `docs/ai/monitoring_writer_decision.md` §2 (lines 91-142) is the direct,
  already-decided execution-identity input this ADR consumes — see Current
  Behavior above for the exact shape.
- No existing repo precedent for a "5 separately-labeled sub-decisions in one
  ADR" shape — `simulation_watchdog.md` and `performance_optimization.md` each
  make one decision. This ADR is structurally novel in that it must contain 5
  distinct, separately-labeled decisions (contract representation/format,
  source ownership, versioning, provider-adapter boundary, conformance
  mechanism) rather than one Decision section. Plan phase should decide how to
  subdivide the `## Decision` section (e.g. `### Decision 1: Contract
  Representation`, `### Decision 2: Source Ownership`, etc.) while keeping the
  outer Status/Context/.../Consequences skeleton the two precedent docs use.

## Risks and Open Questions

- **Exact ADR filename is not yet chosen.** The ticket's own AC (line 49)
  requires stating which convention was chosen and why, but does not name the
  literal file. Plan phase must pick one (e.g.
  `docs/architecture/agent_orchestration_contract.md`, following the
  precedent docs' descriptive-slug pattern) — flagging this here rather than
  assuming a name, per the "do not collapse investigation into exact
  coordinates too early" rule.
- **Contract representation is only a recommendation, not a locked decision,
  in the source plan** (`idea_...md:428-430`, "YAML for reviewable
  definitions with generated Python validation is the initial
  recommendation"). This ADR is the artifact that is supposed to convert that
  recommendation into an actual decision — Plan phase should treat the plan's
  wording as a strong steer, not as already-final, and should state the ADR's
  own reasoning rather than merely restating the plan's phrasing as fact.
- **Source-ownership decision has a proposed location (`agent-orchestration/`
  at repo root) but the plan explicitly marks it "proposed"** (line 160-161).
  Plan phase must decide whether this ADR locks that path in or leaves it as
  a still-open naming/location detail deferred to implementation. Given the
  ticket's Out-of-Scope line ("No runtime migration or production code change
  implementing the decided contract"), the ADR can name a location decision
  without creating the directory itself.
- **Conformance-mechanism decision has no directly-inherited recommendation**
  from any of the 3 evidence docs — the source plan only says "Add contract
  conformance tests for both provider adapters" (Workstream F item 1) at a
  very high level. This is the least-constrained of the 5 decisions and Plan
  phase has the most latitude here; the investigation surfaces this rather
  than pre-deciding it.
- **Versioning decision has no directly-inherited recommendation either** —
  the plan only says the contract needs "global invariants" and a "version"
  field in `contract.yaml` (line 167) and that adapters "may not silently
  redefine" contract semantics (implying some notion of a versioned contract
  gating adapter compatibility), but does not specify a versioning scheme
  (e.g. semver vs. simple integer generation number, matching the
  `workflow_version` / `hook_schema_version` fields already named in
  `monitoring_writer_decision.md` and the source plan's monitoring-schema
  table at lines 239-246). Plan phase should decide whether to align this
  ADR's versioning scheme with those already-named monitoring-schema version
  fields for consistency, or treat them as a separate concern.
- **This ADR's own text must not re-decide execution identity.** Already
  verified consistent in the ticket body (see Current Behavior above) — flag
  for Plan/Implement to preserve that consistency in the ADR body itself, not
  just the ticket.

## Anti-Drift Hazards

- **Do not choose or imply a final `docs/architecture/` filename convention
  silently.** The AC requires the choice be explicit and justified, not
  defaulted — an easy slip would be to just create the file and never state
  the reasoning as a labeled decision.
- **Do not re-decide execution-identity format or ownership.** This is the
  exact contradiction Codex's review already caught and the ticket text
  already corrected — the ADR body itself (not just the ticket) must not
  regress into deciding this independently, even implicitly by e.g. proposing
  a different `execution_id` string shape than `monitoring_writer_decision.md`
  §2 already specified.
- **Do not lock in a final storage location, writer implementation, or
  provider-runtime choice.** The ticket's Out of Scope and the source plan's
  §0 precondition gate both forbid this — the ADR decides representation/
  ownership/versioning/boundary/conformance as design decisions, not as
  "here is the exact file path and code that will exist."
- **Do not open or imply a provider-runtime implementation ticket.** Out of
  Scope explicitly blocks this until all 5 discovery outputs are approved —
  this ADR is discovery output #2 of 5 (per the handoff doc's numbering,
  though note this ticket is listed as item 4 in the handoff's specific
  ordering table — the discovery-epic's own "five outputs" list and the
  handoff's "five required discovery outputs" list use different orderings;
  Plan phase should cite the discovery-epic's canonical five-output list from
  the source plan (`## Proposed Architecture` → Approval model and exit gate,
  lines 129-140) rather than the handoff's sequencing table, to avoid
  numbering confusion in the ADR's own evidence-input citations).
- **Do not silently skip the registry/link-back requirement.** AC's final
  bullet requires both `docs/REGISTRY.yaml` regeneration (`make
  knowledge-index-update`) and a link from the source plan doc's own
  `## Related Material` section (`idea_provider_agnostic_agent_orchestration.md:447-459`,
  currently 11 entries, no ADR entry yet) — both steps are easy to forget
  since neither is a code change.
- **Do not touch production Claude/Codex workflows, hooks, monitoring
  writers, live ticket artifacts, or the shared monitoring JSONL corpus** —
  the containment rule inherited from the parent epic and repeated in this
  ticket's own Scope (line 33).
