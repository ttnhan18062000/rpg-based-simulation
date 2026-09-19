---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION
artifact_type: test_plan
tags: [architecture, documentation, investigation]
---

# Test Plan — TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION

Not applicable in the usual sense — investigation only, no code/schema/field/generator built, per
this ticket's own explicit scope.

The equivalent of "testing" here is internal consistency of the throwaway assignment script:
- Every one of the 93 real mechanism ids in `registries/mechanisms.yaml` is assigned (`missing`
  set is empty, confirmed by direct set-difference against the loaded registry, not assumed).
- No assigned id is a typo of a real id (`extra` set is empty, same check).
- The progression assignment (15 mechanisms) is checked against the ticket's own worked example
  in its Request Summary as a sanity cross-check that this session's judgment calls track the
  ticket author's, before trusting judgment calls made for the other 6 systems.
- Per-system rate comparisons (unverified %, `implemented_by` %) are computed against a real
  whole-registry baseline computed the same way, not asserted from memory or impression.
