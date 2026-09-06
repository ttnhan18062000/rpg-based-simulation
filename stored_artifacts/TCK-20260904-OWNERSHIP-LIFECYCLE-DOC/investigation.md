---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260904-OWNERSHIP-LIFECYCLE-DOC
artifact_type: investigation
tags: [ai, documentation, governance]
---

# Investigation — TCK-20260904-OWNERSHIP-LIFECYCLE-DOC

## Current Behavior

### The draft M3 table (`telemetry_retention_epic.md`, lines 93-109)

Read directly. Confirmed both findings the ticket brief asserts:

1. **Missing column, confirmed.** The prose at line 95-97 says: "record an accountable role (not
   a person...), an update trigger, a staleness signal, and a removal condition" — four things
   named. The table header at line 99 is:
   `| Subsystem | Accountable role | Update trigger | Staleness signal |` — only 4 columns total
   (Subsystem + 3 of the 4 named attributes). `Removal condition` is entirely absent from the
   header and from both drafted data rows (lines 101-102). This is a real header/prose mismatch,
   not a formatting nit.
2. **Dangling citation, confirmed.** Line 96: "an accountable role (not a person — see the
   roadmap's shared role vocabulary)". `grep -n -i "role vocabulary\|shared role"` across
   `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` and every other file in
   that directory returns **zero matches outside `telemetry_retention_epic.md` itself** (the only
   hit is the citation line quoted above, in the citing document, not the cited one). `roadmap.md`
   (316 lines, read in full) has no role-vocabulary section, no "role" glossary, nothing a citation
   could resolve to. The two roles actually used in the table — "Agent Configuration Maintainer"
   and "Workflow Runtime Maintainer" — appear **nowhere else** in any of the 8
   `ai_first_hardening_epics/*.md` files (`grep -rn "Maintainer\b"` returns only the two table-row
   hits in `telemetry_retention_epic.md`), confirming they were invented ad hoc for this table and
   never defined.

### The 2 already-drafted rows and their source subsystems

- **Capability-envelope baseline** — `governance_capability_policy_epic.md`'s M2 (lines 62-83,
  read directly): a committed baseline file for `settings.local.json`'s approved capability
  envelope, plus an auditable diff script. Explicitly documented limitation: "no confirmed
  mechanism in the current harness to enforce the ⊆ relationship automatically at runtime" — the
  diff script is human/CI-run tooling, not a runtime guarantee. This grounds the drafted row's
  "Agent Configuration Maintainer" role and "diverges from a working local file" staleness signal
  — both make sense against the actual mechanism (a point-in-time diff, not a live enforcement).
- **Ticket-claim detection log** — `workflow_reliability_epic.md`'s M2 (line 76, header confirmed:
  "Ticket-claim detection logging (Bucket B — experiment/measurement, not a committed ticket)").
  This is Bucket-B experimental measurement work, not yet a committed/shipped subsystem — the
  drafted row's "Continuous" trigger / "Zero incidents after 30 days" staleness signal are
  observation-window language appropriate to an experiment, not a shipped artifact.

### The 5 other new/changed subsystems this batch created (each ticket read directly)

1. **Bash secret-exposure advisory hook — `TCK-20260904-BASH-SECRET-SCAN-HOOK`
   (`tickets/inprogress/`, read in full).** `## Status: BLOCKED`, `phase: blocked`. Hard-blocked on
   two unmet prerequisites: (a) a re-ratification decision superseding
   `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE`'s "no changes authorized" ruling on the knowledge-gateway
   module, and (b) `scan_for_secrets()` extraction out of
   `tools/knowledge_gateway_redaction.py`, which is itself gated on (a). Zero code has been
   written for this subsystem — it does not exist yet as a running artifact.
2. **Tools frontmatter rollout — `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`
   (`tickets/done/`, read in full).** DONE, but only Wave 1 (11 of 16 `.claude/agents/*.md` files
   now carry `tools:`). Wave 2 (`architecture-reviewer`, `security-reviewer`, `planner`) and Wave 3
   (`implementer`, `parity-updater`) remain open, gated on each prior wave's real observation
   window (`roadmap.md` lines 69-77 confirms this partial-progress framing as of 2026-09-05). This
   is a real, live, partially-shipped subsystem with an explicit further-rollout lifecycle still in
   flight — not a one-shot artifact.
3. **AST import-boundary enforcement — `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`
   (`tickets/done/`, read in full).** DONE, dated **2026-08-17** — this predates the AI-First
   Hardening batch entirely (the batch's own planning docs are dated 2026-09-04). `roadmap.md`
   line 31 confirms: item 4 is "**SUPERSEDED — already shipped**... found during the 2026-09-04
   `create-tickets` investigation pass" — i.e. this batch discovered the work already existed under
   a *different* epic (`TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`'s sub-epic tracking), it did
   not create it. The ticket's own Out of Scope explicitly declined "a general machine-readable
   subsystem-ownership manifest for all 38 `src/` packages" — this ticket's own scope never
   contemplated an ownership table for itself.
4. **Doc-coverage reverse-check — `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`
   (`tickets/done/`, read in full).** DONE. Extends
   `check_docs_to_update_coverage()` in `tools/gate_checks/done_checker_static.py` with a
   tier-agnostic reverse-direction check (a `docs/` path `git status` shows touched but that never
   made it into the ticket's own Files Changed/Related Docs), wired into `run_static_precheck` so
   it blocks Verify. Also added a self-check step to `doc-updater.md`'s prompt. A real, shipped gate
   inside the `implement-ticket` pipeline's Verify phase.
5. **Test-scoper hang guard — `TCK-20260904-TEST-SCOPER-HANG-GUARD`
   (`tickets/done/`, read in full).** DONE. A new `tools/agent-monitoring/subagent_stop_background_guard.py`
   wired under a genuinely new `SubagentStop` key in `.claude/settings.json` (not suffixed
   `|| true`, unlike every advisory hook, since it must not swallow its own exit-2 block signal).
   Reads the harness's own `background_tasks` payload field directly. `.claude/agents/test-scoper.md`'s
   existing prose section was deliberately kept as defense-in-depth, not superseded. A real,
   shipped, deterministic enforcement mechanism.

### Sibling artifact-retention ticket — `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION` (DONE, read
in full, plus its `stored_artifacts/.../plan.md`)

Shipped `docs/guidelines/artifact_retention_classification.md` — the M2 deliverable of the same
`telemetry_retention_epic.md` this ticket's M3 belongs to. Its `plan.md` (Step 1, lines 34-64,
read directly) gives the concrete reasoning for landing in `docs/guidelines/` rather than
`docs/ai/` or `docs/observability/`: matched `status: active` / `layer: guidelines` / `authority:
P1` against the two closest structural precedents already in that directory
(`agent_working_environment.md`, `intentional_divergences.md`), and picked `audience: agent`
following `agent_working_environment.md`'s precedent (a doc primarily consulted by agents doing
retention/cleanup work) over `intentional_divergences.md`'s `audience: developer`. This is the
direct precedent for this ticket's own file-placement decision (see below).

### The 3 existing differently-shaped ownership docs

Read `docs/testing/content_migration_test_ownership.md` in full and the headers of
`docs/simulation/domains/domain_ownership_map.md` and `docs/architecture/cognition_domain_ownership.md`.
Confirmed structurally distinct from what this ticket builds:

- `content_migration_test_ownership.md`: columns `Suite path | Marker/tier | Owns | Preserves` —
  maps `tests/` directories to the *behavior* they cover. No accountable-role, update-trigger,
  staleness-signal, or removal-condition concept anywhere in it.
- `domain_ownership_map.md`: columns `Domain | src/ path | pipeline stage | responsibility |
  owned state | contract doc` — maps `src/domains/` packages to their code contract docs. Pure
  code/architecture ownership, not a lifecycle/staleness governance table.
- `cognition_domain_ownership.md`: a 2-column mapping (`Cognition Sub-Model -> Domain Service Owner
  Package`), plus a "Decisions" section recording code-removal history (`SelfModel` cut). Again,
  code-ownership, not the accountable-role/staleness-signal/removal-condition governance shape this
  ticket's table uses.

All three answer "which test suite / package owns this behavior," never "who is accountable for
noticing this doc/config has gone stale and when should it be removed." Confirms the ticket's
Out-of-Scope framing: cross-link only, do not merge or rewrite.

## Mechanics / Engine Constraints

None. This is a pure documentation/process-governance ticket — no `docs/mechanics/` or
`docs/engine/` law is implicated; nothing in it changes simulation formulas, pipeline phases, or
runtime behavior. (Same conclusion the sibling `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`
reached for the directly-adjacent M2 milestone.)

## Docs Requiring Update

- `docs/guidelines/subsystem_ownership_lifecycle.md`: new canonical doc — the ticket's own
  deliverable; must exist with the 5-column table, the resolved role-vocabulary section, and the
  per-subsystem row-or-exclusion decisions below.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`: M3
  section (lines 93-109) must stop being the source of truth — recommend the same pattern M2 of
  this same doc already established at lines 68-91 (keep the original draft table as
  historical/superseded context, add a "M3 is shipped — see canonical doc" note pointing at the
  new doc), and the dangling "roadmap's shared role vocabulary" citation on line 96 must be
  corrected to point at the new doc's role-vocabulary section instead of a nonexistent roadmap
  section.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`:
  per this ticket's own Scope ("Update the sibling epic docs to link to the canonical doc rather
  than restating rows"), add a one-line cross-reference near its M2 (capability-envelope baseline)
  section pointing at the new canonical ownership doc for that subsystem's accountable-role/
  lifecycle row.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md`: same —
  add a one-line cross-reference near its M2 (ticket-claim detection logging) section pointing at
  the new canonical doc.

The following docs were considered and explicitly excluded from required changes:

`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (path:
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`) does not need to change:
the recommended fix for the dangling citation (see "Roadmap's shared role vocabulary" below) is to
redirect the citation to the new canonical doc's own role-vocabulary section — a change entirely
within `telemetry_retention_epic.md`'s own text — not to add a new section to `roadmap.md` itself.
`roadmap.md` is a planning/tracking index, not a governance-conventions doc; the role vocabulary is
consumed at the table (the new doc), so that is its more natural, and sufficient, home.

`docs/testing/content_migration_test_ownership.md`, `docs/simulation/domains/domain_ownership_map.md`,
and `docs/architecture/cognition_domain_ownership.md` (all three confirmed structurally distinct
above) do not need to change: this ticket's own Out of Scope limits interaction with them to a
cross-link written *from* the new doc, not edits *to* them.

`docs/guidelines/artifact_retention_classification.md` (path:
`docs/guidelines/artifact_retention_classification.md`, under `docs/guidelines/`) does not need to
change for this ticket: its Out-of-Scope bullet 3 forbids "building or populating M2's
artifact-retention classification table content," and while a one-line reverse-pointer edit into
that doc (referencing the new ownership table) is not itself forbidden by that bullet — it is a
discretionary cross-link, not a required Acceptance Criterion here — this ticket does not need to
touch it to satisfy its own Acceptance Criteria; the new doc pointing *at* it (in the meta-row
discussed below) is sufficient.

`docs/ai/README.md` (path: `docs/ai/README.md`) is not required to change: its "Document Index"
table only lists docs that physically live under `docs/ai/`, and this ticket's new doc is being
placed under `docs/guidelines/` instead (see File Placement below), so it does not belong in that
index; `docs/REGISTRY.yaml` is the actual cross-directory index and is regenerated mechanically per
CLAUDE.md's After Work step, not hand-edited here.

## Parity Ledger Overlap

None. This is a pure documentation/governance change with no runtime behavior modification —
confirmed by `grep -rn -i "ownership\|accountable role\|staleness signal"` across
`docs/parity_ledger/*.yaml`, which surfaces zero entries about this table's concept (only unrelated
gameplay "territory ownership" hits). Matches the directly-adjacent sibling ticket
`TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`'s own conclusion ("pure documentation change — no
runtime behavior changed, no new tag/layer registrations").

## Prior Work

- `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION` (DONE) — the directly-adjacent M2 sibling
  milestone of the same epic. Its `plan.md` supplies the concrete file-placement precedent this
  ticket reuses (see File Placement below) and its `tests/docs/test_artifact_retention_classification_doc.py`
  supplies the doc-structure test pattern this ticket's test plan follows.
- `TCK-20260609-TEST-OWNERSHIP-MAP`, `TCK-20260612-DOMAINS-ARCH-MAP` — produced
  `content_migration_test_ownership.md` and `domain_ownership_map.md` respectively; confirmed
  structurally distinct (see above), cross-link only.
- `TCK-20260719-AGENT-ROLE-GLOSSARY` (DONE) — a differently-scoped "role" concept (hover
  descriptions for agent *names* in the Agent Ops Dashboard's call-volume table), not accountable
  subsystem-ownership roles. Noted only to avoid confusing the two "role" vocabularies; not reused
  or referenced by this ticket's table.
- The `governance` tag (registered `registries/tag_registry.jsonl` line 74, added 2026-09-03,
  category `subsystem-topic`, note: "Agent capability/permission governance... seeded by the
  AI-first next-evolution proposal's Governance & Capability Policy epic") is already registered
  and is the same tag this ticket's own frontmatter uses — confirms no new tag registration is
  needed for `governance`. The `lifecycle` tag (registered, added 2026-09-02) is explicitly scoped
  in its own registry note to `src/systems/lifecycle_systems/` (reproduction/birth/death) — a
  different subsystem meaning entirely; **do not reuse `lifecycle` as a tag for this doc**, despite
  the word appearing in this ticket's own title, to avoid a false semantic collision.

## Risks and Open Questions

- **File placement — resolved, recommend `docs/guidelines/subsystem_ownership_lifecycle.md`.**
  `docs/ai/README.md` (read in full) frames `docs/ai/` as the "AI Tooling — Overview" — a narrow
  three-layer reference family (agents/workflows/skills) with its own `Document Index` table.
  `docs/guidelines/README.md` (read in full) frames `docs/guidelines/` as "Standards and
  conventions for developers" — the broader cross-cutting governance/process-doc family, which is
  exactly where the directly-adjacent M2 sibling deliverable
  (`docs/guidelines/artifact_retention_classification.md`) already landed, using the identical
  reasoning this ticket needs (a cross-cutting governance table, not a narrow AI-layer reference
  doc). Recommend the new doc's own frontmatter use `layer: guidelines` (not `observability`,
  which the *ticket* file uses per its own stated cross-subsystem-observability rationale — that
  rationale applies to classifying the ticket, not necessarily to the deliverable doc's directory-
  convention layer; every doc actually inside `docs/guidelines/` uses `layer: guidelines`, and
  matching that convention keeps `layer` consistent with physical placement, the same way `TCK-
  20260904-ARTIFACT-RETENTION-CLASSIFICATION`'s doc did). This is a recommendation, not something
  Investigation is authorized to make binding — Plan should confirm before Implement.
- **Roadmap's shared role vocabulary — resolved, recommend defining it inside the new doc itself.**
  Concrete proposal: a "## Accountable Role Vocabulary" section near the top of the new doc,
  defining each role in one line: **Agent Configuration Maintainer** (owns `.claude/agents/*.md`
  frontmatter scoping and the capability-envelope baseline/diff script);
  **Workflow Runtime Maintainer** (owns `.claude/workflows/*.js` pipeline logic, done-checker gate
  wiring, and pipeline-adjacent hooks); **Documentation Governance Maintainer** (owns this table
  itself and the artifact-retention-classification table — see meta-rows below). Then correct
  `telemetry_retention_epic.md` line 96's citation from "see the roadmap's shared role vocabulary"
  to point at this doc's own vocabulary section. This is the more natural home: the roles are
  *consumed* at the table, and the table now exists as a canonical, cross-referenced doc — better
  than adding a section to `roadmap.md`, which is a tracking index, not a conventions doc.
- **Bash secret-scan hook row-vs-exclusion — recommend exclusion, not a row, pending unblock.**
  Zero code exists for this subsystem yet (`BLOCKED`, `phase: blocked`, no extraction landed). A
  staleness signal or removal condition cannot honestly be written for something that has not been
  built — writing one now would be inventing metadata for nonexistent code, the same category of
  problem as the dangling citation this ticket is fixing elsewhere. Recommend an explicit
  exclusion note: "excluded — subsystem is BLOCKED (`TCK-20260904-BASH-SECRET-SCAN-HOOK`), no code
  exists yet; add a row when it ships and is unblocked." This is a genuinely new exclusion
  rationale (distinct from the weekly-shard exclusion's "owned elsewhere" rationale) — flagging
  explicitly since it sets a mild precedent for how this table should treat not-yet-built batch
  items in the future.
- **M2's artifact-retention-classification deliverable — recommend a meta-row, not a
  content-rewrite.** Out-of-Scope bullet 3 forbids "building or populating M2's... table CONTENT" —
  read literally, this is about not restating/duplicating the 8-row classification table itself. A
  single new row in the *ownership* table whose Subsystem cell is
  "Artifact-retention classification table (`docs/guidelines/artifact_retention_classification.md`,
  M2 deliverable)" does not build or populate that table's content — it assigns an accountable
  role/update-trigger/staleness-signal/removal-condition to the already-finished doc as a whole,
  which is squarely this ticket's own subject matter. Recommend: Accountable role = "Documentation
  Governance Maintainer" (same meta-role proposed above); Update trigger = "a new persistent
  artifact class is introduced anywhere in the repo (new top-level dir/file family)"; Staleness
  signal = "a merged ticket introduces such a class and it is not reflected in the 8-row table
  within the same PR"; Removal condition = "the classification table is folded into a different
  repo-wide artifact index with a migration ticket recorded here."
- **This ticket's own deliverable — recommend a self-referential meta-row.** Same "Documentation
  Governance Maintainer" role; Update trigger = "any future ticket creates, materially changes, or
  retires a subsystem this table covers"; Staleness signal = "a merged ticket changes a covered
  subsystem's shape/lifecycle without a corresponding row edit in the same PR (no automated check
  exists for this yet — accepted gap, named here rather than silently left)"; Removal condition =
  "this table is superseded by a different tracking mechanism (e.g. folded into `docs/REGISTRY.yaml`
  metadata), with a migration ticket recorded here." Closes the "who watches the watcher" gap
  explicitly rather than leaving it implicit.
- **Open question genuinely requiring a Plan-time confirmation, not resolvable here:** whether the
  removal-condition semantics for a *shipped, still-actively-changing* subsystem (e.g. the tools
  frontmatter rollout, still mid-rollout across Waves 2/3) should describe "when this row is
  removed from the table" (subsystem retired) or "when the underlying enforcement is removed"
  (e.g. `tools:` frontmatter scoping abandoned entirely) — these are different conditions for a
  subsystem that has not finished shipping. Recommend Plan treat "removal condition" as answering
  the latter (when the underlying mechanism itself would be retired/superseded) consistently across
  all rows, since that is what the M2-drafted rows' own language implies ("Baseline diverges from a
  working local file" describes mechanism staleness, not row deletion) — but this is a genuine
  interpretive decision Plan should state explicitly, not silently assume.

## Anti-Drift Hazards

- **Do not silently fix the draft M3 table's own columns in place.** The recommended pattern
  (matching M2's own precedent in the same doc) is to mark the *existing* draft table historical/
  superseded and add a pointer to the new canonical doc — not to edit the draft table's header to
  add a 5th column in place. Editing it in place would create two different "corrected" surfaces
  and risk drift between them.
- **Do not let the new doc's Accountable Role column drift into naming actual people.** The source
  epic doc is explicit ("not a person"). Enforce role-noun-only language; a test guard for this is
  in the test plan.
- **Do not treat "5+ other new subsystems" as a closed, exact-5 list.** The ticket's own Scope
  bullet says "bash secret-scan hook, tools frontmatter rollout, AST import-boundary enforcement,
  doc-coverage reverse-check, test-scoper hang guard" — exactly 5 named, but the phrase "5+" in the
  Request Summary leaves room for more if Plan/Implement discovers another in-batch subsystem this
  Investigation missed. None were found beyond these 5 plus the 2 already-drafted rows and the 2
  meta-rows (this ticket's own deliverable, M2's deliverable) during this pass.
- **Do not merge or restate the 3 existing ownership docs' content into the new one.** Confirmed
  structurally distinct above; only a cross-link belongs in the new doc.
- **Do not silently drop the AST import-boundary enforcement subsystem's discovery-history nuance**
  — it is excluded not because it's unimportant, but because it predates this batch and belongs to
  a different, already-shipped epic (`TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`). The
  exclusion reasoning should name that epic explicitly, mirroring the weekly-shard exclusion's own
  "ownership is a matter for whoever maintains the already-shipped epic's code" precedent — not
  just say "already done" without attribution.
- **Do not resolve the Bash-secret-scan-hook exclusion by inventing forward-looking staleness
  metadata for code that doesn't exist.** If Plan/Implement decides to add a preemptive row anyway
  (a legitimate alternate call), it must be explicitly labeled speculative/pre-ship, not presented
  as equivalent in confidence to the 4 shipped/drafted rows.
