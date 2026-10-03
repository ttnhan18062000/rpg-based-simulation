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
today: **78 of 80 exist** (2 misses, both templated/glob placeholders in the citation text itself —
`agent-monitoring/data/<ISO-week>/{runs,events}.jsonl` and a single bare filename, `Legend.tsx`,
that resolves against a component dir rather than repo root — neither is a genuine stale/renamed
reference). **Effectively 0 genuinely stale file-path citations among populated tickets.** So where
the field IS extracted, it stays correct — but see the correction below: "populated" turns out to
mean something narrower than "the author wrote real content," and that distinction changes the
whole recommendation.

## Correction to Measurement 2 (self-caught, after the peer independently reproduced and endorsed
## the original 53.4% figure)

Re-examined the 31 "empty" tickets from Measurement 2 directly, rather than trusting the aggregate
count. **29 of the 31 have real, path-shaped bullet content — they are simply not backtick-quoted.**
Example (`TCK-20260905-CHORE-CARRYFORWARD-DERIVER-CONSOLIDATION.md`, counted "empty" by Measurement
2): `- src/domains/culture/{model,deriver,exporter}.py` — a genuine, correct, existing path, written
as a plain bullet with no backticks around it.

`generate_registry.py::parse_related_code_areas()` — the function Measurement 2 deliberately reused
because it IS the registry's own extraction logic — only recognizes backtick-quoted tokens
(`_BACKTICK_RE = re.compile(r"`([^`]+)`")`, `generate_registry.py:66`). A bullet line with a real
path but no backticks around it yields nothing to this function, and is therefore invisible to the
registry today regardless of how well the author actually filled the field in.

**Re-measured cleanly, separating "backtick-extracted" from "non-backtick bullet content," and
checking existence on both, correctly stripping backticks/prefixes before the filesystem check
(the first pass of this correction under-counted "exists" by leaving literal backtick characters
in the path string — caught and fixed before recording the number below):**

| | Count | Accuracy where checkable |
|---|---|---|
| Backtick-extracted (what the registry sees today) | 27/58 tickets (46.6%) | 78/80 entries exist (97.5%) |
| Non-backtick bullet content (registry's blind spot) | 29/58 tickets (50.0%) additional | 201/209 entries exist (96.2%; remaining "misses" are brace-expansion/glob artifacts in the citation itself, not renames) |
| Genuinely empty (no bullets, or an explicit "None") | 2/58 tickets (3.4%) | — |

**Corrected true content-population rate: 56 of 58 open tickets (96.6%) have real, accurate
`## Related Code Areas` content** — not 46.6% as Measurement 2's raw number implied. The field is
not sparse. **The defect is that the registry's own extraction regex requires backtick-quoting that
roughly half of ticket authors don't use, and silently drops everything else — an extraction bug in
`generate_registry.py`, not an authorship-discipline gap.**

This does not reverse Measurement 1 (the registry still doesn't index open tickets at all) or the
recommendation against building registry cross-matching *exactly as scoped today* — but it changes
*why*, and it opens a cheaper path the original framing missed: fixing `parse_related_code_areas`
to also recognize plain `- path` bullets (not requiring backticks) would raise registry-visible
coverage from 46.6% to ~96% on its own, with no change in author behavior required. Combined with
extending the registry's ticket walk to include open tickets (Measurement 1's own gap), registry
cross-matching becomes a two-part, bounded fix rather than "blocked on getting people to fill in a
field they mostly already fill in." See the revised recommendation in `plan.md`.

**Disclosure**: an earlier draft of this investigation reported 53.4% as the field's sparsity
without this correction, and the peer session independently reproduced that exact number and (after
first suspecting the opposite bug in their own competing 9.5% measurement) endorsed 53.4% as "the
meaningful figure" before this correction was found. The 53.4% figure was not wrong as *"fraction of
open tickets currently visible to the registry's own extractor"* — that number is still accurate and
still supports Measurement 1's conclusion. It was incomplete as *"fraction of open tickets that
genuinely lack Related Code Areas content,"* which is the number that actually matters for choosing
between "fix the extractor" and "build something else entirely."

## What this changes about the two most concrete options

The ticket's own Scope frames the tradeoff as "re-verify at pickup (fixed cost, works today) vs.
registry cross-match (near-zero cost, but unmeasured precision)." The measurements above — including
the Measurement 2 correction — change that framing, and change it differently than the first-pass
53.4% number alone would have:

- **Registry cross-match, as literally scoped today, is still not "near-zero cost" and still isn't
  recommended as-is.** It needs extending `generate_registry.py` to index open tickets at all
  (Measurement 1 — unaffected by the correction, still a real gap). On its own, extending only the
  indexing scope would still cap visible coverage at 46.6%, because the extractor it would reuse
  requires backtick-quoting most authors don't use.
- **But the corrected Measurement 2/3 numbers mean the "sparse field" framing was wrong, and the
  cheaper fix is different from what the first-pass number suggested.** The field itself is 96.6%
  populated with accurate content (Measurement 2 correction). The gap is a narrow extraction regex,
  not an authorship-discipline problem. `generate_registry.py::parse_related_code_areas()` could be
  widened to also recognize plain `- path` bullets (not just backtick-quoted ones) — a small,
  bounded, mechanical fix — and combined with extending the indexing scope (Measurement 1), registry
  cross-matching would become viable at close to the field's true 96.6% coverage, not 46.6%. This
  is now a genuine third concrete option, cheaper than it first appeared, not eliminated by the data.
- **A close-time full-text sweep remains a real, independently-viable alternative** — it searches
  every open ticket's whole body text for mentions of the closing ticket's git-touched paths, so it
  needs neither the extractor fix nor the registry's indexing extension. It is the ticket's own
  "back-reference sweep" option's keyword-overlap half (Scope text: "shared Related Code Areas file
  paths **or keyword overlap**"). Its main advantage over "fix the extractor + extend indexing" is
  not needing two separate registry-side changes; its main disadvantage is building a second index
  path outside the registry rather than fixing the registry's existing one.
- **Recommendation, revised**: bring both the "fix the extractor + extend indexing" option and the
  "full-text sweep" option to review as the two live candidates, not "sweep vs. do nothing." The
  registry-fix option looks cheaper now than the original 53.4% framing suggested (it is a targeted
  regex fix plus a scope extension, not a fight against widespread non-compliance), so it deserves
  equal consideration, not elimination.

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
