---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC
artifact_type: plan
tags: [architecture, engine, documentation]
---

# Implementation Plan — TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC

## Summary

Land Appendix A (`docs/plans/kernel_concurrency_design_review_proposal.md:192-367`) as a standalone
doc at `docs/architecture/kernel_concurrency_design_philosophy.md`. The base text is the **current
repo copy** of Appendix A's prose (already carrying the RNG-pointer fix from a prior closed
ticket), not the stale fetched artifact's prose — the artifact predates two in-repo fixes
(investigation Risks item 1). Into that base text, splice the 4 verbatim mermaid diagrams recovered
in `investigation.md`'s "Recovered Diagram Source" section (not 2, despite the ticket AC's and the
proposal's own undercount — investigation confirms the true count is 4). Two internal staleness
items get fixed in place (the "Known documentation drift" section's items 1/2, and the
`concurrency_limit` pointer in Part 4), four existing docs get a cross-link back to the new doc at
already-identified anchors, the parent proposal gets a matching C1 completion annotation, and the
registry/index commands run with honest reporting of `make knowledge-index-update`'s known sandbox
failure.

## Steps

### Step 1 — Create the new doc with corrected frontmatter and body

**Files:** `docs/architecture/kernel_concurrency_design_philosophy.md` (new)

**Change:**
Create the file with this frontmatter (confirmed against sibling
`docs/architecture/simulation_watchdog.md:1-6`, read directly — `status: active, layer:
architecture, authority: P1, audience: developer`, no `last_verified` field):

```yaml
---
status: active
layer: architecture
authority: P1
audience: developer
---
```

Body: copy verbatim from `docs/plans/kernel_concurrency_design_review_proposal.md:200-366` (line
367 is the fence's own closing ` ``` ` delimiter, not content — do not copy it) (the
`# Kernel Concurrency Model & Design Philosophy` title through the end of `## References` —
i.e. everything inside the fence *except* the fence's own frontmatter at lines 193-198, which this
step's frontmatter above replaces). This range already contains the two in-repo-only fixes (Part
3's RNG pointer at lines 277-281 already reads "now resolved" — no change needed there) that the
externally-fetched artifact does not have; do not pull any prose from the artifact, only the 4
diagrams (see below).

Confirmed no dead references: every path cited in `## References` (lines 352-366) — 8
`src/engine/*.py`/`src/core/*.py`/`src/platform/rng.py` files, `src/perf/long_run_harness.py`,
`tests/perf/test_perf_regression_baseline.py`, 5 `docs/engine/*.md` files, 6
`docs/engine/contracts/*.md` files, `docs/performance/perf_baseline_policy.md`,
`src/api/ws/stream.py` — was verified to exist on disk directly during Plan (`test -e` on all 27
paths, all `OK`). No new dead citations will be introduced by this step.

**Do NOT touch:** `docs/plans/kernel_concurrency_design_review_proposal.md` itself in this step
(handled in Step 9); do not carry over the artifact's `<pre class="mermaid">` HTML wrapper syntax
anywhere — diagrams go in as standard ` ```mermaid ` fences (Step 1b below).

**Verify:** `test -f docs/architecture/kernel_concurrency_design_philosophy.md`;
`python3 tools/validate_frontmatter.py docs/architecture/kernel_concurrency_design_philosophy.md --content-type doc` exits 0.

---

### Step 1b — Splice the 4 recovered mermaid diagrams into their Part locations

**Files:** `docs/architecture/kernel_concurrency_design_philosophy.md` (same file as Step 1 — do
this as part of the same authoring pass, not a separate commit-worthy edit)

**Change:** Use the exact verbatim mermaid source from `investigation.md`'s "Recovered Diagram
Source" section — do not re-derive or paraphrase (per investigation's explicit instruction). Insert
each as a fenced ` ```mermaid ` block at these anchors (anchor text quoted from the current repo
prose, `kernel_concurrency_design_review_proposal.md`, confirmed by direct read):

1. **Diagram 1 (Part 1, `flowchart LR`, priority order)** — insert between the paragraph ending
   `"...it is not stated as a rule anywhere."` (end of Part 1's first paragraph, source line ~221)
   and the paragraph beginning `"Every mechanism traced below is a specific engineering
   answer..."` (source line ~223).
2. **Diagram 2 (Part 2, `flowchart TB`, tick loop + Collection fanout)** — insert between the
   paragraph ending `"...requires having all of them before sorting any of them."` (source line
   ~237) and the paragraph beginning `"This is fork-join, not asyncio/anyio..."` (source line
   ~239).
3. **Diagram 3 (Part 3, `sequenceDiagram`, race-safety sequence)** — insert between numbered item 3
   ("Output collisions are prevented structurally...") ending `"...protected by an explicit
   threading.Lock."` (source line ~276) and the paragraph beginning `"Open question, now resolved
   (TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION..."` (source line ~277).
4. **Diagram 4 (Part 4, `stateDiagram-v2`, RuntimeMode ladder)** — insert between the "Slow loop —
   RuntimeMode" paragraph ending `"...so the engine doesn't flap between modes."` (source line
   ~292) and the sentence `"Each mode is a pre-composed policy bundle (`src/engine/policy.py`):"`
   that introduces the mode table (source line ~294).

**Do NOT touch:** diagram content itself — use the recovered source exactly as captured in
`investigation.md`, character-for-character (labels, arrows, `\n` line-break syntax inside node
labels, everything).

**Verify:** `grep -c '^```mermaid' docs/architecture/kernel_concurrency_design_philosophy.md`
returns `4` (not `2` — see Acceptance Criteria Map below for why this overrides the ticket AC's and
`test_plan.md`'s literal "2" wording).

---

### Step 2 — Fix the two stale items in the new doc's "Known documentation drift" section

**Files:** `docs/architecture/kernel_concurrency_design_philosophy.md`

**Change:** In the copied `## Known documentation drift` section (source
`kernel_concurrency_design_review_proposal.md:338-350`), items 1 and 2 currently carry no
resolution annotation while item 3 already has one (source lines 347-350:
`**Update (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT, closed 2026-08-21):** ...`). Add matching
`**Update (...)**` annotations, update-in-place per investigation Risks item 2's recommendation
(not deletion — deletion would erase institutional memory of what was wrong and how it was fixed).
Source these annotations from the parent proposal's own C2/C3 `**Update**` blocks, read directly at
`kernel_concurrency_design_review_proposal.md:47-52` (C2) and `:65-70` (C3):

- After item 1 ("Concurrency framing contradiction..."), add:
  `**Update (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION, closed 2026-08-21):** resolved — §9
  was corrected to a narrower, accurate statement: concurrency is bounded to the COLLECTION phase
  only, RESOLUTION applies all proposals through a single deterministic serial commit order;
  kernel.md, simulation_kernel_contract.md, and bounded_concurrency_contract.md now agree.`
- After item 2 ("Phase-count contradiction..."), add:
  `**Update (TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION, closed 2026-08-21):** resolved —
  architecture.md's fabricated GOVERNANCE/PACKETIZATION table was corrected to the real 7-phase
  list, the identical defect in docs/guides/simulation.md was also fixed, and the
  xfail(strict=True) marker was removed from tests/docs/test_kernel_phase_names_consistent.py,
  which now genuinely passes.`

**Do NOT touch:** item 3's existing annotation (already correct, leave verbatim).

**Verify:** manual read-check during Verify (no automated test asserts this section's content, per
`test_plan.md`'s Anti-Drift Test Guards — "Verify must check them by direct read, not by test
pass/fail").

---

### Step 3 — Fix the `concurrency_limit` open-question pointer in Part 4

**Files:** `docs/architecture/kernel_concurrency_design_philosophy.md`

**Change:** Part 4's current text (source `kernel_concurrency_design_review_proposal.md:305-308`)
reads: `` `concurrency_limit` goes *down* as pressure rises because everything else already shrank
the batch by then — fewer, less-contended workers on a smaller batch beats fighting for cores on an
already-stressed system (see C6 in the parent proposal — this rationale isn't written down anywhere
else). `` This is stale: `bounded_concurrency_contract.md:49-76` §5.1 (read directly during
investigation) now contains the fuller, code-verified version of this rationale, and
`src/engine/policy.py`'s `GovernorPolicy.from_mode()` docstring also documents it (per closed
`TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE`). Replace the parenthetical with the same "now
resolved" treatment Part 3's RNG pointer already received (source lines 277-281, pattern to match):

`` `concurrency_limit` goes *down* as pressure rises because everything else already shrank the
batch by then — fewer, less-contended workers on a smaller batch beats fighting for cores on an
already-stressed system. Open question, now resolved (TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE,
closed 2026-08-21, see C6 in the parent proposal): the full rationale is written down in
`GovernorPolicy.from_mode()`'s docstring (`src/engine/policy.py`) and
`docs/engine/contracts/bounded_concurrency_contract.md` §5.1 ("Why `concurrency_limit` Decreases as
`RuntimeMode` Escalates") — see that section for the mechanism rather than restating it here. ``

**Do NOT touch:** do not paste `bounded_concurrency_contract.md` §5.1's fuller mechanistic
explanation (the phase-budget/cadence/scheduling breakdown) into this doc — link to it instead, per
investigation's Anti-Drift Hazards ("do not let the new doc's Part 4 duplicate §5.1's explanation
... link to it instead of restating, per the C8 audit's own cross-link-rather-than-restate
recommendation").

**Verify:** manual read-check (same as Step 2 — no automated test covers this prose).

---

### Step 4 — Cross-link from `docs/engine/kernel.md`

**Files:** `docs/engine/kernel.md`

**Change:** Insert a "See also" line after the two bullets under
`## ⚡ Concurrency & The Resolution Bottleneck` (confirmed at lines 53-57, read directly: the
"Concurrent Collection" and "The Singular Bottleneck" bullets), before the `---` separator that
follows:

```
See also: [`docs/architecture/kernel_concurrency_design_philosophy.md`](../architecture/kernel_concurrency_design_philosophy.md)
for the full design-philosophy narrative behind this section — why Collection is fork-join instead
of asyncio/anyio, how race-safety is structurally enforced, and how the RuntimeMode ladder degrades
gracefully under load.
```

Relative path confirmed: `docs/engine/kernel.md` → `docs/architecture/...` is `../architecture/...`
(sibling directories under `docs/`).

**Other writers to this file:** `kernel.md` was last touched by the now-closed
`TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION` (§9 cross-doc reconciliation, per Step 2's C2
annotation) — that ticket is closed and merged, not concurrently in-flight. `git status` at Plan
time shows no pending modification to this file from another session. This step only appends one
line after the existing bullets; it does not touch the `## ⚡ Concurrency...` heading or either
bullet, so it cannot re-collide with that prior ticket's §9 edit (different section of the file).

**Do NOT touch:** the two existing bullets, the heading text, or any other section of `kernel.md`.

**Verify:** `grep -n "kernel_concurrency_design_philosophy" docs/engine/kernel.md` returns exactly 1
match.

---

### Step 5 — Cross-link from `docs/engine/contracts/bounded_concurrency_contract.md`

**Files:** `docs/engine/contracts/bounded_concurrency_contract.md`

**Change:** Insert a "See also" line after §5.1 ends (confirmed by direct read: §5.1 runs lines
49-76, ending `"...this contract's worker pool is what consumes it."`, followed by a blank line
then `## Non-Goals` at line 78) and before `## Non-Goals`:

```
See also: [`docs/architecture/kernel_concurrency_design_philosophy.md`](../../architecture/kernel_concurrency_design_philosophy.md)
Part 4, for the design-philosophy narrative this section's mechanism sits inside (RuntimeMode
ladder, PhaseBudgetGovernor, and why concurrency is the last lever pulled, not the first).
```

Relative path confirmed: `docs/engine/contracts/...` → `docs/architecture/...` is
`../../architecture/...` (two levels up to `docs/`, then into `architecture/`).

**Other writers to this file:** §5.1 itself was added by the now-closed
`TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE` (per its C6 update annotation in the parent
proposal). That ticket is closed; no other ticket is currently in-flight against this file per
`git status`. This step appends after §5.1's last line and before `## Non-Goals`, so it does not
re-edit §5.1's existing content (Step 3 above deliberately links to this section rather than
restating it, avoiding a second class of drift here).

**Do NOT touch:** §5.1's existing text (this is the canonical, fuller version — the new doc links
to it, per Step 3), the `## Non-Goals` heading, or any other section.

**Verify:** `grep -n "kernel_concurrency_design_philosophy" docs/engine/contracts/bounded_concurrency_contract.md` returns exactly 1 match.

---

### Step 6 — Cross-link from `docs/engine/contracts/worker_contract.md`

**Files:** `docs/engine/contracts/worker_contract.md`

**Change:** Insert a "See also" line after the `## Purpose` section's single paragraph (confirmed
at lines 10-11, read directly: `"This contract defines safe concurrency for the engine. This
contract ensures that parallel execution improves throughput without introducing resource blowups
(payload leakage) or semantic drift (determinism loss)."`) and before `## 1. Payload Discipline
(Compact Packets)` (line 13, verified — a blank line at 12 separates it from the Purpose paragraph):

```
See also: [`docs/architecture/kernel_concurrency_design_philosophy.md`](../../architecture/kernel_concurrency_design_philosophy.md)
Part 3, for why this contract's laws (payload discipline, result semantics, deterministic
equivalence) structurally prevent race conditions.
```

**Other writers to this file:** `docs/engine/manifest.json` lists this file as one of 16
`mandatory_documents` with `required_headers: ["Purpose", "Backpressure & Fallback Law"]`, enforced
by `tests/docs/test_doc_integrity.py::test_document_structural_compliance` — this test is the other
"writer-adjacent" constraint on this file (it doesn't write, but it gates any edit). No ticket is
currently in-flight against this file per `git status`. This step inserts between the `## Purpose`
paragraph and `## 1. Payload Discipline`, touching neither the `Purpose` heading nor the
`Backpressure & Fallback Law` heading (located later in the file) — confirmed safe against the
manifest requirement.

**Do NOT touch:** the `## Purpose` heading text, the `## Backpressure & Fallback Law` heading text
(wherever it appears later in the file), or any other heading — this is the highest-risk file in
this ticket (see Anti-Drift Notes).

**Verify:** `grep -n "kernel_concurrency_design_philosophy" docs/engine/contracts/worker_contract.md` returns exactly 1 match; `python3 -m pytest tests/docs/test_doc_integrity.py::test_document_structural_compliance -q` passes.

---

### Step 7 — Cross-link from `docs/engine/contracts/concurrent_integrity_contract.md`

**Files:** `docs/engine/contracts/concurrent_integrity_contract.md`

**Change:** Insert a "See also" line after the `## Purpose` section's single paragraph (confirmed
at lines 10-11, read directly: `"This document defines the operational lifecycle laws for the
engine. It ensures that startup, persistence, runtime status, and shutdown behave as trustworthy
contract paths, maintaining the non-authoritative boundary for all observational work."`) and
before `## Scope` (line 13):

```
See also: [`docs/architecture/kernel_concurrency_design_philosophy.md`](../../architecture/kernel_concurrency_design_philosophy.md)
Part 4/5, for how this contract's operational-lifecycle laws are a concrete instance of the
engine's broader Progressive Degradation design.
```

**Other writers to this file:** no other ticket currently in-flight against this file per
`git status`. This file is not in `docs/engine/manifest.json`'s mandatory-headers list (only
`worker_contract.md` is, per Step 6) — lower risk. This step inserts between `## Purpose` and
`## Scope`, touching neither heading.

**Do NOT touch:** the `## Purpose` and `## Scope` headings, or any other section.

**Verify:** `grep -n "kernel_concurrency_design_philosophy" docs/engine/contracts/concurrent_integrity_contract.md` returns exactly 1 match.

---

### Step 8 — Combined cross-link acceptance check (all 4 files)

**Files:** none (verification-only step)

**Change:** none.

**Verify:** run the exact command from `test_plan.md`'s "New Tests Required" section:

```
grep -rn "kernel_concurrency_design_philosophy" docs/engine/kernel.md docs/engine/contracts/bounded_concurrency_contract.md docs/engine/contracts/worker_contract.md docs/engine/contracts/concurrent_integrity_contract.md
```

must return exactly 4 matches (one per file, from Steps 4-7). This directly operationalizes the
ticket's AC: "All three concurrency contracts ... contain a cross-link" + "kernel.md contains a
grep-verifiable cross-link."

---

### Step 9 — Add the C1 completion annotation to the parent proposal

**Files:** `docs/plans/kernel_concurrency_design_review_proposal.md`

**Change:** `## C1 — Land the kernel concurrency & design-philosophy doc` (lines 22-35) is currently
the only one of C1/C2/C3/C6/C7/C8 with no `**Update (...)**` annotation — C2 (lines 47-52), C3
(lines 65-70), C6 (lines 129-134), C7 (lines 148-157), and C8 (lines 347-350) all have one. Add,
after line 35 (end of C1's body paragraph, before the `## C2` heading at line 37):

```
**Update (TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC, closed 2026-08-2X):** resolved. Landed at
`docs/architecture/kernel_concurrency_design_philosophy.md` (status: active, authority: P1,
audience: developer), with all 4 mermaid diagrams (not the 2 this section's own intro implied),
cross-linked from `kernel.md` and all three concurrency contracts, and the two stale internal
"Known documentation drift" items updated in place.
```

(Implement fills in the actual close date.) This is not explicitly named in the ticket's own Scope,
but investigation's "Docs Requiring Update" flags it as needed for the proposal doc's own internal
self-consistency (5 of 6 addressed items already annotated; leaving C1 silently unannotated once
this ticket closes would itself be a fresh instance of the doc-drift class this whole
proposal/C8-audit exists to prevent).

**Other writers to this file:** C2, C3, C6, C7, C8's annotations were each added by their own
now-closed tickets — all closed 2026-08-21, none currently in-flight per `git status`. This step
adds a 6th, independent annotation block after C1's body and before `## C2`; it does not touch any
existing C2-C8 content, including their own Update annotations.

**Do NOT touch:** Appendix A itself within this file (lines 182-367) — Steps 1-3 operate on the
*new* doc's copy, not this source file's copy; the source file's Appendix A fence is left as the
historical record of what was originally drafted, unedited.

**Verify:** `grep -n "TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC" docs/plans/kernel_concurrency_design_review_proposal.md` returns at least 1 match (the new annotation, plus the doc's own frontmatter/self-reference if any).

---

### Step 10 — Run `make docs-registry`

**Files:** `docs/REGISTRY.yaml` (regenerated, not hand-edited)

**Change:** Run `make docs-registry`. This regenerates the entire registry file from a scan of all
frontmatter-tagged docs — it is not a manual append, and no other ticket edits this file by hand
(per CLAUDE.md: "`docs/REGISTRY.yaml` is regenerated unconditionally as part of Finalize's
post-migration self-check ... Always stage the regenerated file"). Running it here (mid-Implement,
per this ticket's own Scope: "Run make docs-registry ... after landing") is redundant with but
harmless alongside Finalize's own unconditional regeneration later in the pipeline — both runs
produce the same deterministic output from the same doc-tree scan, so there is no conflict between
"writers."

**Do NOT touch:** do not hand-edit `docs/REGISTRY.yaml`; if the new doc is missing from the
regenerated output, the fix is in the new doc's frontmatter/tags, not the registry file.

**Verify:** `make docs-registry` exits 0; `grep -n "kernel_concurrency_design_philosophy" docs/REGISTRY.yaml` shows the new doc indexed under layer `architecture`.

---

### Step 11 — Run `make knowledge-index-update` and report the true exit status

**Files:** none (index rebuild, external command)

**Change:** Run `make knowledge-index-update`. Per investigation's Anti-Drift Hazards and
`test_plan.md`'s Anti-Drift Test Guards, this command is **confirmed to fail in this sandbox** due
to a network block on `huggingface.co` (verified by repeated direct attempts earlier in this same
session, per investigation). This is an environment limitation, not a defect in this ticket's
content. Implement must run the command for real and record its actual exit code and output —
never silently mark this ticket's corresponding AC ("`make knowledge-index-update` completes such
that search_docs ... surfaces the new doc") as passed without a real, current run showing success.
If it fails as expected, report it as a known environment limitation in `Implementation Notes`, not
as a silently-skipped or fabricated pass.

**Do NOT touch:** do not modify the knowledge-index tooling or its network config to work around
the block — that is out of scope and would be routing around a gate rather than fixing substance
(CLAUDE.md Hard Rules).

**Verify:** actual command output/exit code recorded in the ticket's `Implementation Notes`
verbatim, whichever way it goes.

---

### Step 12 — Final verification pass

**Files:** none (verification-only step)

**Change:** none.

**Verify (all must be checked, per investigation's Anti-Drift Hazards and `test_plan.md`'s
Scoped Pytest Commands):**

1. `worker_contract.md`'s two manifest-mandatory headers (`## Purpose`, `## Backpressure & Fallback
   Law`) are unchanged — `grep -n "^## Purpose\|^## Backpressure & Fallback Law" docs/engine/contracts/worker_contract.md` still returns both, unmodified text.
2. `python3 -m pytest tests/docs/ tests/unit/docs/ -m "not slow" -q` passes, including
   `tests/docs/test_doc_integrity.py` (all three named tests:
   `test_manifest_file_existence`, `test_document_structural_compliance`,
   `test_terminology_alignment`) and `tests/docs/test_doc_path_existence.py::test_doc_path_citations_exist`
   (still `xfail(strict=True)` at exactly its pinned 12 dead citations — the new doc's References
   section must not add a 13th; Step 1 already confirmed all 27 cited paths exist on disk).
3. `python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py tests/tools/test_layer_registry.py tests/tools/test_tag_registry.py -q` passes.
4. Step 8's combined grep (4 cross-link matches) and Step 1b's mermaid count grep (4 diagrams)
   both re-confirmed after all edits are complete, not just when each step individually landed.

**Do NOT touch:** do not edit any test file or its assertions to make a failure disappear — if
something in this final pass fails, that is a real signal to fix the actual doc content, per
CLAUDE.md's Gate Integrity rule.

## Scope Guards

- Do not resolve `TCK-20260817-STATE-DESIGN-PRIORITY-ORDER`'s scope. That ticket (currently at
  `tickets/todos/kernel-concurrency-design-review/TCK-20260817-STATE-DESIGN-PRIORITY-ORDER.md`, not
  yet started) depends on this ticket landing first and intends to quote/cross-link Part 1's prose
  from the new doc — leave Part 1 quotable as landed by Step 1. Do not edit
  `docs/engine/project_lawbook_m10.md` from inside this ticket.
- Do not let the new doc's Part 4 restate `bounded_concurrency_contract.md` §5.1's fuller
  mechanistic explanation of `concurrency_limit` — Step 3 links to it, does not duplicate it.
- Do not disturb `worker_contract.md`'s two `docs/engine/manifest.json`-mandatory headers
  (`Purpose`, `Backpressure & Fallback Law`) — Step 6 inserts strictly between existing sections.
- Do not fix the pre-existing 12-item dead-citation list in `tests/docs/test_doc_path_existence.py`
  — out of scope; this ticket's obligation is only to not add a 13th.
- Do not touch `docs/audits/D25_engine_docs_drift.md`'s stale citation of
  `TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION` as "OPEN" (investigation Task 8, flagged for
  awareness only — not in this ticket's Related Docs).
- Do not resolve C4/C5's items from the parent proposal (RuntimeMode as a Scoped-Claims dimension,
  lawbook precedence ordering) — those are separate tickets (C5 = `STATE-DESIGN-PRIORITY-ORDER`,
  C4 unassigned in this ticket's Related Tickets).
- Do not attempt to fix the `huggingface.co` network block in Step 11 — report the true result.

## Dependency Map

- Step 1 must complete before Step 1b, 2, 3 (all operate on the file Step 1 creates).
- Steps 1b, 2, 3 are independent of each other but all must land before Step 8's combined
  verification (Step 8 does not depend on them directly, but Step 12's final pass does).
- Steps 4, 5, 6, 7 are fully independent of each other and of Steps 1-3 (different files) — can be
  done in any order, but Step 8 depends on all four being complete.
- Step 9 is independent of all doc-content steps (different file) but conventionally done after
  Step 1 exists (its annotation references the new doc's landed path).
- Step 10 (docs-registry) depends on Step 1 (the new doc must exist with valid frontmatter to be
  indexed).
- Step 11 (knowledge-index-update) depends on Step 1 for the same reason; independent of Steps 2-9.
- Step 12 depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| New doc under docs/architecture/ contains all 5 Parts + both mermaid diagrams from Appendix A | Steps 1, 1b — note: "both" in the ticket AC is superseded by investigation's confirmed count of 4 real diagrams (not 2); Plan lands all 4, per the explicit task instruction and investigation's Risks item 1 resolution | `grep -c '^```mermaid' docs/architecture/kernel_concurrency_design_philosophy.md` == 4; manual read confirms all 5 Part headings present |
| Frontmatter status field is one of {authoritative, active, historical, archive}, never 'draft' | Step 1 | `python3 tools/validate_frontmatter.py docs/architecture/kernel_concurrency_design_philosophy.md --content-type doc` exits 0 |
| docs/engine/kernel.md contains a grep-verifiable cross-link to the new doc | Step 4 | `grep -n "kernel_concurrency_design_philosophy" docs/engine/kernel.md` (1 match) |
| All three concurrency contracts contain a cross-link to the new doc | Steps 5, 6, 7 | Step 8's combined grep (4 matches total) |
| `make docs-registry` exits 0 with the new doc indexed under layer architecture/engine | Step 10 | exit code 0; grep on `docs/REGISTRY.yaml` |
| `make knowledge-index-update` completes such that search_docs surfaces the new doc | Step 11 | actual command output recorded — expected to fail in this sandbox (network block), reported honestly, not fabricated as passing |

## Anti-Drift Notes

- The externally-fetched artifact (`https://claude.ai/code/artifact/5b90c23d-5251-411d-983e-4160973475f6`)
  is **stale prose, current diagrams**: use only its 4 diagrams verbatim (already captured in
  `investigation.md`), never its prose (it predates the RNG-pointer fix and both "Known
  documentation drift" resolution annotations already applied to the repo's Appendix A). Steps 1-3
  are structured specifically to prevent this artifact's stale text from silently overwriting the
  repo's already-correct text.
- `worker_contract.md` (Step 6) is the single highest-risk file in this ticket — it is one of 16
  `docs/engine/manifest.json` `mandatory_documents` entries with `required_headers: ["Purpose",
  "Backpressure & Fallback Law"]`, enforced by
  `tests/docs/test_doc_integrity.py::test_document_structural_compliance`. A misplaced insertion
  (inside either heading's block, or a renamed/reflowed heading) breaks this test.
- The ticket's own AC text ("both mermaid diagrams") and `test_plan.md`'s "Mermaid diagram presence
  check" (`grep -c ... should return 2`) are both now known-stale relative to investigation's
  confirmed count of 4 — Step 1b's Verify line uses 4, not 2. This was cross-checked against the
  ticket's literal AC wording per the fact-verification requirement and is a deliberate, evidence-
  based correction, not an oversight; call this out explicitly in Verify/Finalize reporting so it
  isn't mistaken for a Plan error.
- `tests/docs/test_doc_path_existence.py::test_doc_path_citations_exist` carries `xfail(strict=True)`
  pinned to exactly 12 known-dead citations (confirmed by direct read of the reason string at
  `tests/docs/test_doc_path_existence.py:38-58`). Every one of the 27 paths cited in the new doc's
  `## References` section was individually confirmed to exist on disk during Plan — this count must
  not change during Implement (e.g. do not add a new citation to the References section without
  re-verifying it exists).
- `make knowledge-index-update`'s failure is environmental, not a ticket defect — do not attempt to
  route around the `huggingface.co` network block, and do not report the corresponding AC as passed
  without a real, current, successful run.
