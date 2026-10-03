---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-STATE-DESIGN-PRIORITY-ORDER
artifact_type: investigation
tags: [documentation, architecture]
---

# Investigation — TCK-20260817-STATE-DESIGN-PRIORITY-ORDER

## Current Behavior

**`docs/engine/project_lawbook_m10.md`** (read in full, 38 lines). Its "Architectural Pillars"
section (lines 16-23) lists exactly the 5 pillars named in the ticket — Determinism, Authoritative
Apply, Bounded Resources, Hardware-Class Honesty, Observability Separation — as a flat numbered
list with **no stated precedence or trade-off order**. Immediately after the list is `## Table of
Contents` (line 24). The insertion point for a precedence statement is therefore **between line 23
(end of the pillar enumeration) and line 24 (`## Table of Contents`)** — either as a new paragraph/
subsection inside "Architectural Pillars" or as a short new `##` section directly after it, before
the Table of Contents. The doc's own `## Purpose` (lines 10-14) already contains a cross-link
pattern to follow: "See `project_lawbook.md` for the full law text and parity proofs" — plain
backtick-path prose, not `[label](path)` markdown-link syntax.

**`docs/engine/project_lawbook.md`** (read in full, 64 lines). Its "Architectural Pillars" section
(lines 13-33) is a **different list**: 4 items (The Authoritative Heart, Resource Envelopes,
Graceful Degradation, Deterministic Proof), each with its own Law/Enforcement/Isolation-or-
Classification-or-Shedding sub-bullets — structurally and substantively unlike m10's flat 5-item
list. Neither the names, the count, nor the wording match. See "Docs Requiring Update" and "Anti-
Drift Hazards" below for how this bears on this ticket.

**`docs/architecture/kernel_concurrency_design_philosophy.md`** (read in full, 256 lines, landed by
the now-DONE `TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC`). Part 1, "Design Philosophy: what we're
actually optimizing for" (lines 18-36), already states the reconstructed order in prose plus a
`flowchart LR` mermaid diagram:
```
1. Determinism (never traded away)
2. Resource-Safety (survive real hardware without crashing)
3. Performance (use available headroom, never borrow from 1 or 2)
4. Auditability (prove 1-3 actually held)
```
Part 1's own text says this ordering is "implicit, reconstructed from three documents plus code —
it is not stated as a rule anywhere." That sentence is the load-bearing detail for this ticket:
once `project_lawbook_m10.md` states the order as a rule, this sentence becomes literally false and
needs updating in the same change (see "Docs Requiring Update").

**`docs/engine/contracts/harness_architecture.md`** (read in full, 45 lines). "Core Principles"
(lines 13-17) states exactly: "1. Absolute Determinism ... 2. Resource Boundaries ... 3.
Auditability ..." — confirmed verbatim. No "Performance" step. This doc's scope (`# Certification
Harness Architecture`, "a proof-oriented runner designed to verify... architectural integrity and
logic compliance") is about *verifying* determinism/resource-safety/auditability after the fact,
not about live runtime performance trade-offs — the harness doesn't itself make performance
decisions under pressure, so omitting "Performance" is a real scope difference, not a contradiction
of the reconstructed order. Its 3-item order (Determinism → Resource Boundaries → Auditability) is
a strict subsequence of the 4-item order with "Performance" removed — order-consistent, not
conflicting.

**`docs/engine/architecture.md`** (read in full, 130 lines). §3 "Resource-Safe Execution Laws"
lists 3 laws (Bounded State, Non-Blocking Persistence, Progressive Degradation) with no
precedence/trade-off statement between them and no claim about where they rank relative to
Determinism or Auditability — does not conflict, doesn't state an order at all. §5 already
self-flags an unrelated, pre-existing hardware-class table inversion (Class A "Low-Power" vs.
Class A "High-Performance" elsewhere) attributed to `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` —
unrelated to this ticket's scope, not touched.

**`docs/engine/contracts/certification_contract.md`** (read in full, 51 lines). §5 "Reporting Law"
states "No modification of kernel laws for benchmark vanity" (§6) and forbids unscoped performance
claims — consistent with, but does not itself state, the Auditability-last framing. No explicit
precedence order present; no conflict.

## Mechanics / Engine Constraints

This is a documentation-only ticket (per Scope/Out of Scope); no `docs/mechanics/` chapter governs
document precedence-ordering itself. The relevant engine-contract constraint is `docs/engine/
project_lawbook_m10.md`'s own status as "Authoritative laws governing the V2 simulation engine" —
CLAUDE.md names it the master index for `docs/engine/`. That authority, plus the design doc's own
"the engine contracts define the laws... [this doc] narrate[s] the model" framing (kernel_
concurrency_design_philosophy.md Purpose, lines 12-16), is why the lawbook is the natural home for
the terse "rule" statement and the design-philosophy doc is the natural home for the full reasoning
— matching what `SEQUENCE.md` (see "Prior Work") already decided.

## Docs Requiring Update

- `docs/engine/project_lawbook_m10.md`: add the precedence/trade-off order (Determinism →
  Resource-Safety → Performance → Auditability, or a maintainer-confirmed alternative) inside or
  immediately after "Architectural Pillars" (insertion point: between line 23 and line 24), stated
  tersely and cross-linking `docs/architecture/kernel_concurrency_design_philosophy.md` Part 1 as
  the fuller narrative, per this ticket's own scope and `SEQUENCE.md`'s explicit design intent.
- `docs/architecture/kernel_concurrency_design_philosophy.md`: Part 1's sentence "This ordering is
  implicit, reconstructed from three documents plus code — it is not stated as a rule anywhere"
  becomes stale the moment `project_lawbook_m10.md` states the order as a rule, and needs a small
  correction (e.g. "...now stated as a rule in `project_lawbook_m10.md`'s Architectural Pillars
  section, which this Part expands on") plus an explicit "this doc is the single source of truth
  for the reasoning; the lawbook states the terse rule" designation, to satisfy AC4's "one
  designated single source of truth, the other cross-linking it." This falls inside this ticket's
  Out-of-Scope carve-out ("this ticket edits project_lawbook_m10.md (**or a doc it links to**), not
  docs/architecture/") once `project_lawbook_m10.md`'s new cross-link makes this doc "a doc it
  links to" — see "Risks and Open Questions" for why this reading needs explicit planner
  confirmation rather than being assumed silently.

`docs/engine/project_lawbook.md` is **not** listed above — see "Anti-Drift Hazards" for why it is a
real, already-known, pre-existing drift that this ticket's scoped edit neither worsens nor fixes.

## Parity Ledger Overlap

None. This ticket documents an already-implemented, already-verified-consistent ordering of
existing engine behavior (fork-join barrier, RuntimeMode ladder, work-debt ledger, certification
reporting law) — it changes no code and introduces no new behavior, so no `docs/parity_ledger/*`
entry's `status`/`v2_evidence` needs updating. Grepped `docs/parity_ledger/` for "pillar",
"precedence", and "design.priority" — no matches in any of the 8 subsystem YAMLs.

## Prior Work

- **`tickets/todos/kernel-concurrency-design-review/SEQUENCE.md`** (still present at that path,
  batch not yet fully closed) is decisive on the open design question this ticket's brief raises:
  "TCK-20260817-STATE-DESIGN-PRIORITY-ORDER's lawbook edit is meant to **cross-link the design
  doc's 'Part 1 — Design Philosophy' as the single source of truth** for the reconstructed priority
  order, rather than independently drafting near-duplicate prose." This directly answers
  investigation point 3: **Part 1 of `kernel_concurrency_design_philosophy.md` is the designated
  single source of truth**; `project_lawbook_m10.md` states a short rule and cross-links to it
  rather than restating the full reasoning.
- **`docs/plans/kernel_concurrency_design_review_proposal.md`** C5 (lines 116-132) is this ticket's
  origin item; its "Update" line is still empty (unresolved), confirming this ticket is the first
  to act on C5.
- **`tickets/done/TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC.md`**: closed 2026-08-21. Its own Out
  of Scope explicitly states "Rewriting the lawbook's pillar precedence ordering (covered by
  TCK-20260817-STATE-DESIGN-PRIORITY-ORDER)" — confirms no overlap, this ticket's scope was
  deliberately carved out of that one.
- **`tickets/done/TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT.md`**: closed 2026-08-21, recorded at
  `docs/audits/D25_engine_docs_drift.md`. Per the ticket brief, this audit found the
  `project_lawbook_m10.md` vs. `project_lawbook.md` pillar-list divergence as "a newly-found
  instance of the same drift class this ticket audits for" and **explicitly left it unfixed**,
  out of its own scope. Confirmed still real (see "Current Behavior" above: 5 items vs. 4 items,
  different names, different structure). Not re-litigated or fixed here — this ticket does not
  touch `project_lawbook.md`.

## Risks and Open Questions

- **Blocking open question — file-scope reading of "not docs/architecture/"**: this ticket's Out of
  Scope says "this ticket edits `project_lawbook_m10.md` (or a doc it links to), not
  `docs/architecture/`." Taken as a blanket restriction, this would forbid fixing Part 1's now-stale
  "not stated as a rule anywhere" sentence in `kernel_concurrency_design_philosophy.md` — leaving a
  freshly-false statement in an `authority: P1` doc as a direct result of this ticket's own edit,
  which is itself a new, self-inflicted drift. Taken as the more literal reading — "docs/
  architecture/" is barred *except* via the explicit "(or a doc it links to)" carve-out, and once
  `project_lawbook_m10.md` cross-links `kernel_concurrency_design_philosophy.md`, that doc qualifies
  — the small correction is in scope. This investigation recommends the second reading (it is the
  only one that satisfies AC4's "the other cross-linking it" requirement, and it fits the
  parenthetical's literal wording), but flags it as requiring explicit planner confirmation rather
  than being assumed, since the two readings produce materially different file-change sets.
- **Terminology mapping is not 1:1 and is not stated anywhere**: the reconstructed order's 4 terms
  (Determinism, Resource-Safety, Performance, Auditability) do not map one-to-one onto the 5
  pillars' names (Determinism, Authoritative Apply, Bounded Resources, Hardware-Class Honesty,
  Observability Separation). "Resource-Safety" plausibly spans 3 of the 5 pillars (Authoritative
  Apply, Bounded Resources, Hardware-Class Honesty) and "Auditability" maps to Observability
  Separation, but this mapping has never been stated explicitly anywhere in the docs read for this
  investigation, including Part 1 itself. AC2 requires naming Performance "explicitly as a ranked
  priority" — the plan should decide whether the lawbook edit needs to spell out this pillar-to-
  order-term mapping explicitly, or whether stating the 4-term order alongside the unchanged 5-item
  pillar list (without an explicit mapping) satisfies the acceptance criteria as literally written.
- **Reconstruction, not confirmed maintainer intent** (already flagged in the ticket's own
  Assumptions): both this ticket and `kernel_concurrency_design_philosophy.md` Part 1 state the
  order is *reconstructed* from code/docs, not confirmed by a maintainer. If landed as stated, the
  lawbook would assert a reconstructed inference as authoritative law without a maintainer
  sign-off step. The ticket's own Scope allows for this ("If the maintainer-confirmed order
  deviates from the reconstructed one, state the deviation and rationale... rather than silently
  substituting it") — implying the reconstructed order may be landed as-is absent a contradicting
  maintainer statement, but this should be stated as a reconstruction, not asserted as settled fact
  with unqualified confidence, in the lawbook text itself.

## Anti-Drift Hazards

- **Do not touch `docs/engine/project_lawbook.md`.** Its differently-shaped, differently-named,
  differently-counted pillar list is real, pre-existing, already-found-and-explicitly-left-unfixed
  drift (`TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`). This ticket's scoped edit to
  `project_lawbook_m10.md` neither worsens nor improves that drift — it adds precedence-order
  content to the *5-pillar* list only, without touching or re-deriving the *4-item* list in
  `project_lawbook.md`. Resist the temptation to "fix" or reconcile the two while already editing
  the exact section where the discrepancy lives — that is a separate, unscoped ticket's job.
- **Do not independently re-derive or paraphrase the order.** The whole point of this ticket per
  `SEQUENCE.md` is to cross-link Part 1 rather than draft new prose that can drift from it over
  time — the class of bug this entire 8-ticket batch exists to prevent (C8: "a single canonical doc
  per topic with all others required to cross-link rather than restate"). Any wording of the order
  itself that appears in `project_lawbook_m10.md` must be verbatim-identical to Part 1's mermaid/
  prose labels ("Determinism", "Resource-Safety", "Performance", "Auditability" — exact strings),
  not synonyms or reworded equivalents.
- **Do not silently touch `harness_architecture.md` to add "Performance."** Its 3-step order is
  scoped to the test harness (verification, not runtime trade-offs) and is order-consistent with
  the 4-step engine order as a subsequence — adding a "Performance" step there would be scope creep
  into a doc this ticket's own Related Docs/Assumptions explicitly says only to check for
  consistency, not edit.
- **Do not re-open C2/C3/C4/C6/C7/C8's already-closed drift items** while editing the design-
  philosophy doc's "Known documentation drift" section area — those are all resolved and closed;
  only Part 1's single stale sentence identified above is in scope.
