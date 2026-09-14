---
status: active
layer: ticket
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE
phase: open
date: 2026-09-14
tags: [registry, process-improvement]
---

# Investigation — TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE

**Scope of this investigation**: per this ticket's own Scope/AC, this is an investigation producing
a recommendation for peer/user review — **no implementation happens here.** The ticket's own words:
"Measuring how accurate `related_code_areas` actually is across the existing ticket corpus is
probably the real first step... it hasn't been done." This investigation does that measurement
directly, then evaluates the two most concrete candidate options against it.

## Measurement 1 — does `docs/REGISTRY.yaml` even index open tickets?

Read `tools/generate_registry.py` directly rather than assume. Its own module docstring (line 5)
states it "walks `docs/` ... and `tickets/done/`." Confirmed in code: `_collect_tickets()` (the
function populating each entry's `related_code_areas` field) globs `root/tickets/done/*.md` only
(`generate_registry.py:266,277` — `Walk root/tickets/done/*.md (flat)`). Verified by querying the
live, freshly-regenerated `docs/REGISTRY.yaml` directly:

```python
entries = yaml.safe_load(Path('docs/REGISTRY.yaml').read_text())
tickets = [e for e in entries if e['type'] == 'ticket']
open_tickets = [e for e in tickets if e['path'].startswith('tickets/todos/')
                or e['path'].startswith('tickets/inprogress/')]
# len(tickets) == 1958, len(open_tickets) == 0
```

**Finding: zero open tickets are indexed in `docs/REGISTRY.yaml` today.** The "registry cross-
matching" candidate option, as literally described in this ticket's own Scope ("since the registry
already indexes tickets by code area, a query at close time could surface open tickets touching the
same files"), cannot work as-is — the registry has no rows for `tickets/todos/`/`tickets/inprogress/`
tickets to surface. This option requires extending `generate_registry.py`'s ticket-collection walk
to also index open tickets (real tooling cost, not previously counted against this option) before
it can do anything at all.

## Measurement 2 — how populated is `## Related Code Areas` across the actual open-ticket corpus?

Since the registry can't answer this (it doesn't see open tickets), read the 58 real open-ticket
files directly (`tickets/todos/**/*.md` + `tickets/inprogress/*.md`, excluding `SEQUENCE.md`) using
the same parsing functions the registry itself uses (`generate_registry.parse_body_section` +
`parse_related_code_areas`), so this measurement is apples-to-apples with how the registry option
would actually read the field:

| | Count | Fraction |
|---|---|---|
| Total open tickets | 58 | 100% |
| Empty `## Related Code Areas` | 31 | **53.4%** |
| Non-empty `## Related Code Areas` | 27 | 46.6% |

Average areas per non-empty ticket: 2.96.

**Finding: the field is sparse — over half of open tickets declare zero code areas.** This is the
exact failure mode this ticket's own Scope anticipated without measuring: "If the field is sparse
or stale itself, this option silently misses exactly the cases it exists to catch." It does. A
close-time sweep that only checks the closing ticket's diff against open tickets' own declared
`Related Code Areas` would be blind to 31 of 58 (53%) open tickets regardless of what those tickets
actually touch, no matter how the registry-indexing gap above is fixed.

## Measurement 3 — where the field IS populated, is it accurate (not stale)?

For the 27 non-empty tickets (80 total citation entries), checked whether each backtick-quoted
citation that looks like a file path (contains `/` or ends `.py`/`.md`) actually exists on disk
today: **79 of 80 exist; the one "miss" is `agent-monitoring/data/<ISO-week>/{runs,events}.jsonl`**,
a templated glob-shaped path in the citation itself, not a genuinely stale reference (the `<ISO-
week>` placeholder is expected, not a typo or rename). **Effectively 0 genuinely stale file-path
citations among populated tickets.** So the field's defect is sparsity, not inaccuracy-when-present
— when someone does fill it in, it stays correct.

## What this changes about the two most concrete options

The ticket's own Scope frames the tradeoff as "re-verify at pickup (fixed cost, works today) vs.
registry cross-match (near-zero cost, but unmeasured precision)." The measurements above change
that framing:

- **Registry cross-match, as literally scoped, is not "near-zero cost."** It needs (a) extending
  `generate_registry.py` to index open tickets (real, first-time tooling work — Measurement 1), and
  even then (b) its precision is capped at 46.6% coverage by the field's own sparsity
  (Measurement 2) — not a marginal gap, a majority miss.
- **A close-time sweep is still worth pursuing, but not gated on `Related Code Areas` population.**
  A sweep that searches the FULL TEXT of every open ticket body (not just the declared `Related
  Code Areas` section) for mentions of the closing ticket's own git-touched file paths does not
  depend on any ticket having filled in a structured field at all — it works against whatever prose
  already exists in Scope/Request Summary/Related Code Areas/anywhere else in the body. This is a
  variant of the ticket's own "back-reference sweep" option (its Scope text already allows "shared
  Related Code Areas file paths **or keyword overlap**" — the keyword-overlap half is the one this
  measurement recommends leaning on, not the structured-field half).
- **This full-text variant was not costed or measured by the original ticket text** — it is a
  refinement surfaced by actually measuring the structured-field option's real precision, not a
  new fourth mechanism invented independently of the investigation.

## Context requested by peer review (`agent-working-design`, 2026-09-14)

This ticket's own mechanism — a ticket's central claim going stale without anything checking it —
is now independently described in three places, not one:

1. This ticket itself (three concrete cases: `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-
   MISSING`, `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH`,
   `TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK`).
2. `docs/plans/agent_infrastructure/reachability_verification_findings.md` Finding 6 ("agent
   summaries wrong at a material rate; only independent code reading caught it").
3. `docs/ai/agent_definition_gap_audit_2026-08-04.md`'s 2026-09-14 deferred-check addendum: a
   six-week-overdue re-measurement against that document's own pre-fix baseline
   (2026-07-20→08-05: 15 published/17 reproduced Review failures, 25 Verify failures) found the
   equivalent-length window 2026-08-29→09-14 still carrying **13 Review failures, at least 5 of
   which are the same "unverified factual claim about existing code" pattern** the 2026-08-05 fix
   targeted — "the volume fell; the mechanism did not." Verify's *targeted* sub-patterns (AC-
   checkbox-miss, stale-Status, Completion-Summary-gap) genuinely closed, but 13 of 18 new Verify
   failures are a different, unaddressed pattern (`Files Changed`/sibling-path disclosure
   omissions).

That document also records an unresolved ±2 discrepancy re-counting its own Review baseline (15
published vs. 17 reproduced by the same method) — noted here, not smoothed over, since it means the
"13" figure above should be read as "13, ±~2" the same way the source document itself qualifies it.

This is corroborating evidence that the underlying mechanism (unverified claims surviving into
committed work) is real and recurring, not evidence for or against either candidate option's own
cost/precision tradeoff — that tradeoff is what Measurements 1-3 above address directly.
