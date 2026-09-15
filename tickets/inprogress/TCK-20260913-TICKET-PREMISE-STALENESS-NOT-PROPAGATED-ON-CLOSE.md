---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE
phase: open
date: 2026-09-13
tags: [registry, process-improvement]
---

# TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE

## Title
Closing a ticket updates only its own file and the working log — nothing checks whether the fix just invalidated another open ticket's stated premise

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Three tickets in one batch (`gameplay-gaps-batch`) had premises that were already stale by the
time they were picked up — not because any of the three was unusually wrong, but because each
was proven wrong only by someone re-verifying its claim against current code before implementing,
which is not a step the ticket lifecycle itself enforces or reminds anyone to take.

**Three instances, same mechanism, same batch:**

1. **`TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING`** (commit `2f72c057f`) — filed
   claiming `GroupRecord` had no reverse reference to its own contract. `GroupRecord.contract_id`
   already existed and was already load-bearing by the time this ticket was picked up. Caught by
   reading the actual code before implementing.
2. **`TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH`** (amended, not yet
   closed, via commit `54f972a26`) — filed claiming `properties["population_id"]` is "never set
   anywhere" in the catalog-native spawn pipeline. `TCK-20260911-REGION-DECLARED-POPULATION-
   SPAWNED-ENTITY-DIVERGENCE` closed *after* this ticket was filed and added exactly that tagging
   to the same two files this ticket cites as never setting it. Caught while cross-referencing an
   unrelated fix's precedent into this ticket, not by anyone specifically auditing it.
3. **`TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK`** (commit `7af3193d0`) — filed claiming
   3 `print()` calls needed a stdout→stderr fix. By the time it was picked up, 2 of the 3 had
   already been fixed by something else, without that work ever closing or updating this ticket.
   Caught by re-checking the code before implementing, same as case 1.

**In every case, the same underlying mechanism**: a *different* ticket closed, its fix touched
code or made a claim that directly invalidated an *open* ticket's own stated premise, and nothing
in the close-out process looks for that. Closing a ticket updates its own file
(`tickets/done/{id}.md`) and appends one row to `tickets/working_log.csv` — neither step checks
whether any other ticket in `tickets/todos/`/`tickets/inprogress/` cites the same code area or
makes a claim the just-landed change just falsified.

**A related-but-distinct case, not this ticket's own evidence but worth noting for scope
calibration**: `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`'s investigation found the
same *decay* shape in a different artifact — a parity ledger entry (`PROG-014`) marked `verified`
that was never actually backed by a test, discovered a third time in one file. That's not the same
mechanism as the three cases above (no other ticket closing invalidated it; it was simply never
true) — already fully covered by `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP`. Cited
here only to show this arc keeps finding decay in whatever artifact records a claim, not because
this ticket should absorb that one's scope.

## Scope
This ticket is scoped as **the question, not a chosen mechanism** — several real options exist and
none is obviously correct without weighing cost against how often this actually bites:

- **Re-verify at pickup**: before implementing, re-check the ticket's own central factual claims
  against current code — this is what actually caught all three cases above. Cost: manual
  discipline only, no tooling; relies on whoever picks up a ticket actually doing it (which
  happened here, but isn't enforced or reminded), and taxes every pickup regardless of whether
  anything decayed.
- **Back-reference sweep at close time**: when a ticket closes, search open tickets
  (`tickets/todos/`, `tickets/inprogress/`) for shared `Related Code Areas` file paths or keyword
  overlap with the just-closed ticket's own diff, and flag candidates for a human/agent to check.
  Cost: real tooling to build; risk of false positives (shared file ≠ invalidated claim).
- **`related_code_areas` cross-matching against `docs/REGISTRY.yaml`**: since the registry already
  indexes tickets by code area, a query at close time could surface open tickets touching the same
  files without needing new metadata. Cost: depends on how precisely `Related Code Areas` is
  populated today; may need tightening first.
- **A documented convention**: state explicitly in `CLAUDE.md`'s workflow rules that a ticket's own
  central factual claims must be re-verified against current code before implementation begins,
  formalizing what already happened informally in all three cases here.
- **Do nothing further, on the grounds that re-verification is already a real and demonstrated
  practice in this arc**: a legitimate option to weigh, not dismissed — three catches in one batch
  might mean the informal practice already works; more data may be needed before investing in
  tooling.

**No recommendation between the two most concrete options here — both have a real, unresolved
cost/benefit tradeoff, not a clear winner:**

- **Re-verify at pickup** taxes *every* pickup forever, including the majority of tickets where
  nothing has decayed since filing — a fixed cost paid on every single ticket to catch a defect
  that, in this batch, hit 3 of roughly a dozen tickets touched.
- **`related_code_areas` cross-match at close** only fires when something plausibly decayed, at
  essentially zero cost to the common case — but its precision depends entirely on how accurately
  `Related Code Areas` is populated across the existing ticket corpus today, and **nobody has
  measured that**. If the field is sparse or stale itself, this option silently misses exactly the
  cases it exists to catch.

**Measuring how accurate `related_code_areas` actually is across the existing ticket corpus is
probably the real first step** for choosing between these two, and it hasn't been done — this
ticket's own investigation should start there rather than guessing which option is cheaper in
practice.

## Related Shapes (naming only — not this ticket's own scope)
This is one of at least three instances of the same underlying gap, seen from different angles:
**the close/handoff path never checks outward.**

1. **Premise decay** (this ticket) — a ticket closes, its fix invalidates part of an open ticket's
   premise; nothing propagates back to the open ticket.
2. **Unfiled follow-ons** — a ticket closes citing follow-up work that never actually gets filed as
   a real ticket, so the citation points at nothing.
3. **Unpublished handoffs** — an artifact is produced for another track and never made visible
   beyond the session that wrote it, so the handoff reaches one reader and looks complete from both
   ends. Not hypothetical: this very PR's own `rpg_knowledge_investigation_closure_plan.md` cited
   `docs/plans/agent_infrastructure/reachability_verification_findings.md`, a doc written on
   another branch, at the time never pushed, cited across sessions as shared context that nobody but its author
   could actually read. It took both a sender who didn't confirm delivery and a receiver who didn't
   publish — "whose fault" is the wrong question; "neither end has a visibility check" is the right
   one.

A "does this premise still hold" check and a "was this actually published" check are the same
*kind* of mechanism — whoever eventually builds one may be able to build all three cheaply, which
is worth recording even though this ticket's own scope stays the premise-decay question only. The
handoff-visibility mechanism itself belongs to a different track, not here.

## Out of Scope
- Building any of the candidate mechanisms above — this ticket files the problem and investigates
  options; it does not implement a fix.
- Instances 2 and 3 above — named for scope calibration and future cross-reference only, not
  absorbed into this ticket's own investigation.
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP`'s own scope (a different artifact, a
  different decay mechanism — see Request Summary's note above).
- Re-litigating any of the three cases' own already-closed/already-corrected dispositions.

## Acceptance Criteria
- [x] Real investigation of tooling cost/precision for the back-reference-sweep and registry-
      cross-matching options, not just the re-verification-convention option (which requires no
      tooling and is easy to recommend by default without checking the others).
- [x] A recommendation among the options in Scope, with rationale, brought to peer/user review
      before any implementation.
- [x] No implementation without that review. (No `src/`/`tools/`/`tests/` files touched by this
      ticket — see Files Changed.)

## Related Tickets
- `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` (done — case 1)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open — case 2)
- `TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK` (done — case 3)
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` (open — related-but-distinct decay
  shape in a different artifact, see Request Summary)

## Related Docs
- `docs/REGISTRY.yaml` (a candidate mechanism's own data source — see Scope)
- `CLAUDE.md` (a candidate mechanism — documenting the convention explicitly)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `tickets/working_log.csv` (the only durable record a ticket close currently writes to)
- `tools/generate_registry.py` (owns `docs/REGISTRY.yaml`'s generation — relevant if that option is
  chosen)

## Assumptions / Open Questions
- Whether this is worth dedicated tooling at all, versus staying a documented manual convention, is
  the central open question this ticket exists to answer — not pre-judged here.

## Implementation Notes
Investigation-only, per this ticket's own AC ("No implementation without that review"). Two direct
measurements against the real corpus, not assumption:

1. `docs/REGISTRY.yaml` does not index `tickets/todos/`/`tickets/inprogress/` at all today
   (`generate_registry.py`'s ticket-collection walk is `tickets/done/*.md` only, confirmed by
   reading the code and by querying the live registry: 0 of 1958 indexed ticket entries are open
   tickets). The "registry cross-matching" option as literally scoped cannot work without first
   extending that walk.
2. **Corrected after initial publication** (peer had independently reproduced and endorsed the
   original number before this correction landed — see investigation.md's "Correction to
   Measurement 2" for the full account): the first pass measured `## Related Code Areas` as empty
   on 53.4% (31/58) of the real open-ticket corpus using the registry's own extraction function
   (`parse_related_code_areas`). Re-checking the 31 "empty" tickets directly found 29 of them have
   real, accurate path content — just not backtick-quoted, which is the only thing that function
   recognizes. **True content population is 96.6% (56/58)**; the field is not sparse. The actual
   defect is `generate_registry.py`'s extraction regex requiring backtick-quoting that roughly half
   of authors don't use — a fixable, bounded bug, not an authorship-discipline gap. Where content
   IS extracted (by any method), it is accurate: ~97% of citations, backtick or not, resolve to
   real, existing paths.

**Recommendation, revised** (full detail in `plan.md`): the corrected numbers change this from
"eliminate registry cross-matching" to "two live candidates for review": (1) fix the extraction
regex + extend the registry's indexing scope — now the *cheaper* option, since it unlocks ~96%
coverage rather than being blocked on wide-scale authorship change; or (2) a close-time full-text
keyword/path sweep against every open ticket's whole body text, which needs neither fix but builds
a second scan path outside the registry. Measurement 1 (registry doesn't index open tickets at all)
is unaffected by the correction and still rules out registry cross-matching *exactly as originally
scoped*, but no longer rules out a corrected version of it.

**This recommendation has not yet been reviewed by peer/user** — per AC, no implementation may
proceed until that review happens. Status left `BLOCKED` (investigation complete, blocked on
review) rather than `DONE`, since this ticket has not actually resolved anything yet — only
produced the evidence the resolution decision needs.

**Note on `tickets/working_log.csv`**: the working-log row already appended for this ticket's
`BLOCKED` status (via `record_hand_orchestrated_closure.py`, append-only, never rewritten) still
carries the pre-correction "53.4% empty" summary text, since that was accurate as a record of what
this ticket's Implementation Notes said at that point in time. This ticket file (not the log row)
is the authoritative, current account — the log row is a historical snapshot, correctly left
unedited per this repo's append-only convention for that file.

## Test Summary
No tests added — no code changed. See `test_plan.md` for how the investigation's own measurements
were verified (read the real parsing code, ran it against the real corpus, checked citations against
the real filesystem — all reproducible, not assumed) and how the Measurement 2 correction was itself
verified (re-derived cleanly with backtick-stripping fixed, cross-checked against the peer's
independently-reproduced original number before revising).

## Files Changed
- `staging_artifacts/TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE/` (investigation.md,
  plan.md, test_plan.md — investigation.md and plan.md amended post-publication with the Measurement
  2 correction).
- This ticket file itself (Implementation Notes/Test Summary/Files Changed/Completion Summary; AC
  checked off; `## Status` set to `BLOCKED`).
- No `src/`, `tools/`, or `tests/` files touched.

## Completion Summary
Investigation complete, corrected once post-publication. Measured, rather than assumed, that the
registry doesn't index open tickets (Measurement 1, stands unchanged) and that its own field-
extraction logic — not the underlying data — is why open-ticket coverage looked sparse (Measurement
2, corrected: true content population is 96.6%, not the original 53.4% empty figure). Revised
recommendation brings two live candidates to review instead of eliminating one outright: fix the
extraction regex + extend registry indexing (now the cheaper path), or build an independent
full-text keyword/path sweep. Recorded corroborating context from two independent documents
describing the same underlying premise-staleness mechanism this ticket investigates (reachability
findings doc Finding 6; the 2026-08-04 gap audit's 2026-09-14 deferred-check addendum, including its
own unresolved ±2 Review-count discrepancy, preserved rather than smoothed over). This ticket is
**not** implementing anything and is **not** being closed as fully resolved — left `BLOCKED`,
pending the peer/user review its own AC requires before any of the above becomes a real ticket.

## Decision — 2026-09-15 (user, via `agent-working-design`)

**This ticket's AC required a peer/user review before any implementation. That review has now
happened, and the decision is Option A: fix the extraction regex and extend registry indexing.**
Status moved `BLOCKED` → `OPEN`. It is ready to implement.

### What was chosen

Repair the registry so it can answer the question, rather than building a second scanner beside it:

1. **Widen `generate_registry.py::parse_related_code_areas()`** to recognise plain `- path` bullets,
   not only backtick-quoted tokens. Today it matches solely via
   `_BACKTICK_RE = re.compile(r"`([^`]+)`")` (`generate_registry.py:66`), so a bullet carrying a
   real, correct path without backticks yields nothing.
2. **Extend the registry's ticket walk** to index `tickets/todos/` and `tickets/inprogress/`, not
   only `tickets/done/` (Measurement 1's gap, unaffected by the Measurement 2 correction).

### Why Option A over Option B (close-time full-text sweep)

- **The sparsity that argued against it was an artefact, not a fact.** Measurement 2's original
  53.4%-empty figure measured what the *current extractor* could see, not what the corpus contains.
  True content population is **96.6%** (56 of 58 open tickets), independently reproduced from a
  different angle (57 of 59 by a path-shaped test ignoring backticks entirely, with only 28 of 59
  visible to the backtick-only parser). The field is well-populated; the reader is too strict.
- **The fix is bounded.** `parse_related_code_areas` has exactly **one** production caller
  (`generate_registry.py:306`) plus three test call sites. This is a regex widening, not a refactor.
- **Accuracy where populated is already excellent** — 79 of 80 backtick-extracted citations resolve
  to real files; the single miss is a templated glob placeholder, not a stale reference. So the
  index will be trustworthy once it can see the data.
- **Option B builds and maintains a second scan path** outside the registry to work around a defect
  inside it. Cheaper today, more surface forever.

### What this does NOT decide

- **The mechanism that consumes the index is still open.** This decision makes
  `Related Code Areas` queryable at ~96% coverage; it does not itself specify what runs at
  close time. Whether that is a back-reference sweep, an advisory report, or a gate is the
  implementer's design call, informed by what the repaired index can actually do.
- **Option C (documented convention only) was not chosen**, but nothing here prevents adding the
  convention alongside — the three cases this ticket documents were all caught by re-verification,
  and that practice should be encouraged regardless.

### Constraint carried from this batch

Whatever detector emerges **must ratchet from a measured baseline, never assert zero**. The
open-ticket corpus contains real, unfixable historical drift, and a zero-assertion is unlandable —
the constraint established repeatedly across `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` and
the `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` children.

Re-derive every number above at implementation time rather than trusting it; the corpus grows, and
two of the figures in this ticket's own history were wrong when first written.
