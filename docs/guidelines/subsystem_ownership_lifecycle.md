---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [ai, documentation, governance]
---

# Subsystem Ownership & Lifecycle

This doc is the canonical table recording, for every governance-relevant subsystem the AI-First
Hardening epics touch, an accountable role (never a person), an update trigger, a staleness
signal, and a removal condition. It is the M3 deliverable of
`docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`, shipped by
`TCK-20260904-OWNERSHIP-LIFECYCLE-DOC`. It supersedes that doc's own planning-time M3 draft table
(now marked historical there) and resolves the draft's dangling "roadmap's shared role vocabulary"
citation by defining the vocabulary here instead.

## Accountable Role Vocabulary

- **Agent Configuration Maintainer** — owns `.claude/agents/*.md` frontmatter scoping and the
  capability-envelope baseline/diff script.
- **Workflow Runtime Maintainer** — owns `.claude/workflows/*.js` pipeline logic, done-checker gate
  wiring, and pipeline-adjacent hooks.
- **Documentation Governance Maintainer** — owns this table itself and the artifact-retention-
  classification table.

## Ownership & Lifecycle Table

| Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition |
|---|---|---|---|---|
| Capability-envelope baseline (`docs/ai/capability_envelope_baseline.md` + diff script — `governance_capability_policy_epic.md` M2) | Agent Configuration Maintainer | Any new legitimate permission need | Baseline diverges from a working local file | Superseded by a genuine runtime-enforced approved-envelope check that closes the mechanism's own disclosed limitation (no confirmed mechanism today enforces the envelope relationship automatically at runtime); migration ticket recorded here |
| Ticket-claim detection log (Bucket-B experiment — `workflow_reliability_epic.md` M2) | Workflow Runtime Maintainer | Continuous | Zero incidents after 30 days | Zero double-claim incidents surface after a full quarter of operation (the epic's own kill criteria) — downgraded from "build a lock" to "keep as documented convention"; if the Experiment Specification is later killed outright rather than downgraded, record the closing ticket here |
| Tools frontmatter rollout (`.claude/agents/*.md` `tools:` scoping — `governance_capability_policy_epic.md` M3; Wave 1 shipped by `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`, Waves 2-3 pending) | Agent Configuration Maintainer | The prior wave's observation window clears with no unresolved permission regression, unblocking the next wave's ticket | A wave's ticket sits open past its gating window with no observation-window evidence recorded, or a permission-related failure surfaces that is not identifiable by agent/tool/workflow-phase | All 3 waves ship and the epic's Horizon-0 exit signal confirms zero critical workflow breakage over the stated observation window; this row is then folded into a single "shipped" note rather than tracked wave-by-wave |
| Doc-coverage reverse-check (`check_docs_to_update_coverage`'s reverse direction, `tools/gate_checks/done_checker_static.py` — shipped by `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`) | Workflow Runtime Maintainer | A new doc-touching pipeline phase/agent is added, or the Files Changed/Related Docs section-parsing contract changes | A real recurrence of a docs/ path touched-but-undeclared incident (the ITEM-INSTANCE-HISTORY/RACE-RELATIONS-MATRIX/READINESS-SPEED-FORMULA pattern) slips through Verify despite the check being wired in | A different, more general reverse-coverage mechanism (covering all touched paths, not just `docs/`) supersedes this check, closing its disclosed `docs/`-only scope limitation; migration ticket recorded here |
| Test-scoper hang guard (`SubagentStop` hook, `tools/agent-monitoring/subagent_stop_background_guard.py` — shipped by `TCK-20260904-TEST-SCOPER-HANG-GUARD`) | Workflow Runtime Maintainer | The harness's `SubagentStop` payload schema changes (e.g. `background_tasks` field renamed/reshaped), or a new hook event key is added that could supersede this mechanism | A real subagent background-hang recurrence is observed despite the hook being wired in `.claude/settings.json`, or the hook's one-time self-referential retry rate is observed to compound rather than resolve | `test-scoper.md`'s prose Background Commands section and this hook are both superseded by a first-party Claude Code feature that makes turn-end background-task blocking a harness default; migration ticket recorded here |
| Artifact-retention classification table (`docs/guidelines/artifact_retention_classification.md`, M2 deliverable of this same epic) | Documentation Governance Maintainer | A new persistent artifact class is introduced anywhere in the repo (new top-level dir/file family) | A merged ticket introduces such a class and it is not reflected in the 8-row table within the same PR | The classification table is folded into a different repo-wide artifact index; migration ticket recorded here |
| Subsystem ownership & lifecycle table (this doc) | Documentation Governance Maintainer | Any future ticket creates, materially changes, or retires a subsystem this table covers | A merged ticket changes a covered subsystem's shape/lifecycle without a corresponding row edit in the same PR (no automated check exists for this yet — accepted gap, named here rather than silently left) | This table is superseded by a different tracking mechanism (e.g. folded into `docs/REGISTRY.yaml` metadata); migration ticket recorded here |

## Excluded Subsystems

The following in-batch subsystems are deliberately **not** given a table row, with the reasoning
stated explicitly rather than left implicit:

- **Bash secret-exposure advisory hook** — excluded — subsystem is BLOCKED
  (`TCK-20260904-BASH-SECRET-SCAN-HOOK`), no code exists yet; add a row when it ships and is
  unblocked.
- **AST import-boundary enforcement** — excluded — ownership is a matter for whoever maintains the
  already-shipped `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`'s code, not re-assigned here;
  this subsystem predates the AI-First Hardening batch entirely and was only discovered
  already-shipped during this batch's own investigation pass, mirroring the `agent-monitoring/data/`
  weekly-shard layout's own exclusion precedent in `telemetry_retention_epic.md`'s M3 section.

## Related Docs (disambiguation, cross-link only)

This table answers "who is accountable for noticing this subsystem has gone stale, and when
should it be removed." It does not overlap with these structurally distinct ownership docs, which
answer "which code/test suite owns this behavior":

- `docs/testing/content_migration_test_ownership.md` — maps `tests/` suites to the behavior they
  cover (columns: Suite path | Marker/tier | Owns | Preserves).
- `docs/simulation/domains/domain_ownership_map.md` — maps `src/domains/` packages to their
  contract docs.
- `docs/architecture/cognition_domain_ownership.md` — maps cognition sub-models to their owning
  packages, plus code-removal history.
