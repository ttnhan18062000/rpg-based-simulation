---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS
artifact_type: test_plan
tags: [architecture, documentation]
---

# Test Plan — TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS

Documentation/recording ticket; no code under test.

- AC 1 (evidence cited): checked by re-running the registry query recorded in investigation.md (the four
  mechanisms' `systems:` values and the derived-set membership) and reading the temporal axis proposal.
- AC 2 (durable and cross-linked): `docs/plans/mechanism_tier_model_initiative.md` status block names the evidence
  and points at this ticket; the ticket's Implementation Notes carry the finding.
- AC 3 (no schema or registry change): `git diff` for the ticket shows no change under `registries/` or `src/`.
