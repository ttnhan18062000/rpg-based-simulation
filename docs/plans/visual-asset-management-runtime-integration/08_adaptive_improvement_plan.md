---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, cap-b, feedback, evidence, coordination]
---

# AM-M8 — Adaptive Improvement Coordination

## Outcome

Preserve the existing optional CAP-B sequence: B0 evidence recording; B1 manually curated local-signal
reuse; conditional B2 automated bounded retrieval plus the full held-out CAP-B evaluation; and optional,
conditional B3 broader transfer to a new held-out target. M8 adds only the boundary to asset management; it
neither re-plans CAP-B nor makes adaptive improvement a production requirement.

## Repository evidence and assumptions

The [Aseprite plan package](../aseprite-mcp-pixel-art/README.md) already owns B0–B3 and its `CAP-B*`
gates. No proven reusable rule corpus, retrieval system, embeddings, scorer or useful transfer signal is
assumed. Existing reviews require the cheaper manually curated test before automated retrieval can be
justified and separately authorized; retrieval always remains optional.

## Prerequisites and dependencies

- Planning uses the existing B0–B3 documents; execution follows their separate authorization boundaries.
- B0 records evidence only. B1 tests a small manually curated reuse set.
- B2 automated bounded retrieval and its full held-out CAP-B evaluation are conditional on valid useful
  signal from B1 and new authorization.
- B3 broader transfer to a new held-out target is optional and conditional on B2 results and new authorization.
- CAP-B may consume CAP-A evidence, but CAP-A is deliverable without CAP-B.
- AM-M0–M7 and production integration neither require nor automatically consume CAP-B.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM8-W01` | Ownership crosswalk | B0–B3 plans and CAP-B gates are linked without duplicated criteria or reordered prerequisites |
| `AM8-W02` | Evidence-state boundary | Review/score/session evidence cannot become art, a rule, adopted source or active release automatically |
| `AM8-W03` | Reuse handoff boundary | Any suggested rule/reference remains immutable, attributable, bounded and subject to human drawing/adoption review |
| `AM8-W04` | Cheap-test guard | Automated retrieval is explicitly unscheduled when B1 lacks valid useful signal |
| `AM8-W05` | Independence proof | CAP-B failure does not invalidate CAP-A, manual experiments, AM contracts or production assets |
| `AM8-W06` | Privacy/security crosswalk | Retention, redaction, prompt/input provenance, poisoning resistance and deletion ownership remain explicit |

## Applicable gates

All evidence and execution results are governed by the existing `CAP-B` gates in the Aseprite package.
M8 passes no `AM-C*` or CAP gate. Production adoption still requires AM-C03/C04/C08 and later applicable
gates, regardless of any adaptive score.

## Retained evidence

Crosswalk revision, ownership/state diagram, source links, reviewer findings and unresolved `UNVERIFIED`
facts. B0–B3 raw evidence, scores, rule revisions and held-out results remain in the evidence locations
specified by their owning plans.

## Security and recovery

Treat prompts, critiques, scores, references and learned rules as untrusted data. Require provenance,
redaction, bounded schemas/labels, authorization and immutable revision links. Prevent evidence from
embedding secrets, arbitrary paths/URLs, executable instructions or unreviewed licenses. Recovery disables
reuse/retrieval and returns to the prior approved manual rule revision; source art/runtime releases do not
change.

## Explicit non-goals

- Implementing evidence storage, retrieval, embeddings, scoring or automated adaptation.
- Replacing human review, allowing score-triggered adoption/activation, or training a generative-art model.
- Making CAP-B mandatory for CAP-A, art experiments, asset management or production rendering.
- Choosing schemas, models, thresholds, sample sizes or broader-transfer scope here.

## Authorization required to start

This coordination draft is authorized. B0, B1, B2 and B3 each retain the start authority declared by their
own plans. In particular, B2/B3 require later evidence-dependent authorization and are not scheduled now.

## Result classification

| Result | M8 condition |
|---|---|
| `PASS` | Crosswalk preserves B0→B1→conditional B2→conditional B3, human gates and all independence boundaries |
| `FAIL` | It mandates retrieval without B1 signal, permits automatic promotion, or couples CAP-B failure to CAP-A/production validity |
| `BLOCKED` | Existing B0–B3 ownership or state boundaries cannot be identified |
| `INCONCLUSIVE` | Evidence/reuse terminology remains ambiguous enough to allow implicit promotion or gate bypass |

## Rollback, abandonment, and stop conditions

Remove this crosswalk and keep the CAP-B package isolated. For future execution, stop after B1 on `FAIL`
or `INCONCLUSIVE` unless one bounded rerun for a named evidence defect is separately approved. Disable any
later reuse/retrieval route and restore the last human-approved rule revision. Never roll back or invalidate
CAP-A/manual art/production releases merely because CAP-B stops.

## Decisions remaining unfrozen

Whether CAP-B proceeds; evidence schema/retention; rule representation; curation method; retriever,
embeddings, scorer and thresholds; held-out tasks; feedback sources; broader transfer; all art and production
asset/runtime decisions.

## Existing execution owners

- [B0 evidence-only recording](../aseprite-mcp-pixel-art/03_b0_evidence_recording_plan.md)
- [B1 manually curated reuse](../aseprite-mcp-pixel-art/04_b1_manual_advisory_reuse_plan.md)
- [B2 automated retrieval](../aseprite-mcp-pixel-art/05_b2_automated_retrieval_plan.md)
- [B3 broader transfer](../aseprite-mcp-pixel-art/06_b3_broader_transfer_plan.md)
