---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC
artifact_type: plan
tags: [architecture, engine, observability]
---

# Plan — TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC

## Approach

This is a Scope-only epic (per the project's Tier Routing: "epic | Scope only — tracks child
tickets | no direct implementation"). The plan is three writes, no code changes, and explicitly
stops short of running `create-tickets` against any sub-epic.

## Steps

1. **Preserve both audits durably.** Copy `tmp/architecture_resilience_audit.md` and
   `tmp/codebase_health_observatory_audit.md` into `docs/audits/D23_architecture_resilience.md`
   and `docs/audits/D24_codebase_health_observatory.md`, following the existing `D01`-`D22`
   naming/frontmatter convention, content preserved verbatim (only the frontmatter header and
   an added "Audit Profile"/"Related dimensions"/"Remediation tracking" preamble are new — the
   audits' own findings, evidence, and prose are not altered, since altering audit findings would
   undermine their evidentiary value).

2. **Write the synthesized roadmap.** `docs/plans/architecture_resilience_remediation_roadmap.md`
   groups every risk item (R1-R8 from D23, plus D24's complexity/test/tooling findings) into
   named epics A-K, each citing its source audit section(s) so a future `create-tickets` proposal
   doc can pull evidence directly. Explicitly flag Epic C as an amendment to existing work
   (`TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`) rather than a new epic, and note sequencing (which
   epics are independent, which are gated on deployment plans, which are explicitly lower
   priority per the audits' own conditional language).

3. **Write this epic ticket + staging artifacts.** Track the investigation/prioritization work
   itself; do not create any of the 11 sub-epics' own child tickets yet.

4. **Stop here.** Per the user's explicit instruction, do not run `create-tickets` on any
   sub-epic from within this ticket. The next action is a separate decision — the user picks
   which sub-epic(s) (most likely A and/or B, the only two both audits independently rank P0) to
   formalize, and a fresh `create-tickets` proposal document gets written for that sub-epic
   specifically, producing its own investigated child tickets exactly the way
   `TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC` did earlier this session.

## Explicitly not planned

- No `create-tickets` pipeline run in this ticket.
- No code changes — this ticket touches only `docs/` and `tickets/`/`staging_artifacts/`.
- No re-scoring or re-auditing of either source audit's findings.
- No `docs/REGISTRY.yaml` manual regeneration is strictly required mid-session per project
  convention (it regenerates automatically at a ticket's Finalize phase) — but since this ticket
  adds real new docs and stays open rather than closing immediately, a manual
  `make docs-registry` preview run is reasonable so the registry reflects the new D23/D24/roadmap
  docs without waiting for this epic to close.
