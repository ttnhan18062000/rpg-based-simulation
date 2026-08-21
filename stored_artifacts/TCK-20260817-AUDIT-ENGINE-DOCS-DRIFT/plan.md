---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT
artifact_type: plan
tags: [documentation, engine, architecture]
---

# Implementation Plan — TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT

## Summary

This ticket produces one new audit doc (`docs/audits/D25_engine_docs_drift.md`, D25 being the next
free number — `docs/audits/` currently runs through `D24_codebase_health_observatory.md`, verified
via directory listing) covering the 16 docs this investigation already deep-checked at D17 depth,
plus a lighter existence/self-consistency note over the remaining ~94 files in
`docs/engine/`, `docs/architecture/`, `docs/performance/`, and explicitly recommends (does not
file) a directory-scoped follow-up ticket for full-depth coverage of `docs/engine/contracts/` and
`docs/engine/matrices/`. Alongside the audit doc, four direct doc edits fix newly-found stale
claims (README.md's two stale lines, CLAUDE.md's kernel-loop line, architecture.md's inverted
hardware-class table gets a callout box) and one cross-link closes the loop back to
`kernel_concurrency_design_review_proposal.md`. A new living-test file
(`tests/docs/test_kernel_phase_names_consistent.py`) is added now, guarded with
`pytest.mark.xfail(strict=True)` rather than sequenced after the two seed tickets, because
`tickets/todos/kernel-concurrency-design-review/SEQUENCE.md` places this ticket first (#1) in the
batch with the seed tickets at #4/#5 having "no deps in this batch" — this ticket's own Implement
phase will complete before either seed ticket starts, so there is no later point within this
ticket's own execution to "flip it live." The doc-path-existence check is implemented now as a new,
narrowly-scoped test file, per the roadmap's explicit assignment of that item to this ticket.

## Steps

### Step 1 — Write the audit doc: header, methodology, and 16-doc classification table

**Files:** `docs/audits/D25_engine_docs_drift.md` (new)

**Change:** Create the audit doc following `docs/audits/D17_documentation_currency.md`'s format
(read that file's structure before writing — header block, methodology note stating sample depth,
per-doc classification table with `stale`/`current`/`uncertain`/`duplicate`/`contradictory` +
3-5 verifiable claims each). Frontmatter: `status: active, layer: engine, authority: P2,
audience: agent, artifact_type: audit`. Open with a methodology note stating: total surface is 110
files (`find docs/engine docs/architecture docs/performance -name '*.md' | wc -l`, verified in
investigation.md — supersedes the ticket's own "~102" estimate), this doc covers 16 at D17 depth
(listed below) plus a lighter pass over the rest, and is explicitly not claimed exhaustive per the
ticket's own Acceptance Criteria wording ("sampled at D17's own depth, not claimed exhaustive").

Classification table, one row per doc, citing investigation.md's verified findings (all evidence
below was independently re-verified during planning, file:line citations given):

| Doc | Classification | Evidence |
|---|---|---|
| `docs/engine/kernel.md` | current (canonical) | 7-phase list at lines 21-27 per investigation.md; canonical doc for phase count/names |
| `docs/engine/architecture.md` | **contradictory** | §2 "6-Phase" table with fabricated GOVERNANCE/PACKETIZATION phases, `docs/engine/architecture.md:45-58` (re-verified during planning: line 47 "Every tick executes exactly six phases", table rows at 53-58 name GOVERNANCE/PACKETIZATION, neither is a real phase in `src/engine/kernel.py`'s 7-phase sequence). Also §5 hardware-class inversion (see Step 4). |
| `docs/engine/README.md` | **stale (2 claims)** | Line 13 "6-phase orchestrator (Init, Governance, Scheduling, Packetization, Resolution, Persistence)"; line 14 "17-phase refinement sequence" — both re-verified during planning at `docs/engine/README.md:13-14` |
| `docs/engine/contracts/simulation_kernel_contract.md` | current (phase count) / **uncertain (§9)** | Phase list correct (lines 27-33 per investigation.md); §9 has 3 stale non-goal bullets contradicted by real scheduler/governor/broker code — record as unconfirmed hypothesis, do not resolve (see Step 2) |
| `docs/engine/contracts/minimal_kernel.md` | current | §9 Non-Goals (lines 52-56) correctly scoped to the single-threaded minimal kernel; source of the §9 hypothesis, not itself stale |
| `docs/engine/authoritative_pipeline.md` | current | States "37 phases" per `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py:18`'s own passing assertion; already fixed by TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT |
| `docs/engine/contracts/certification_contract.md` | current (canonical for hardware class) | §3 binary AND-rule, cross-linked by `perf_baseline_policy.md`'s own callout box |
| `docs/engine/performance_contract.md` | uncertain | Not independently re-verified beyond investigation's existence check; note as such, do not overclaim |
| `docs/engine/contracts/worker_contract.md` | current | Correctly documents bounded worker-pool concurrency; not the stale outlier in the concurrency contradiction |
| `docs/engine/project_lawbook.md` | current (canonical for pillar list) | Master pillar-list source |
| `docs/engine/project_lawbook_m10.md` | **duplicate** | Says "See project_lawbook.md for full law text" but independently restates a different 5-item pillar list instead of cross-linking only — record as a newly-found instance of the same drift class, do not fix (out of scope) |
| `docs/architecture/simulation_watchdog.md` | current | Verified during investigation to already match `src/observability/watchdog.py`; Epic C's roadmap description of it as broken is stale history — do not schedule work against it |
| `docs/performance/perf_baseline_policy.md` | current (has its own defer-callout) | §2.2 table + existing `> Known conflict, not resolved here` box at lines 30-35, re-verified during planning |
| `docs/performance/simq_isolation_overhead.md` | current | Worked numeric example independently confirms the hardware-class conflict |
| `docs/guides/simulation.md` | **stale (2 claims)** | Lines 19-20 same 6-phase/Governance/Packetization framing; line 26 cites nonexistent `src/engine/authoritative_pipeline.py` — re-verified during planning: `ls src/engine/authoritative_pipeline.py` → no such file; `src/engine/pipeline.py` exists instead |
| `CLAUDE.md` | **contradictory (1 line), current (1 line)** | Line 258 "6-phase deterministic loop... Packetization" is stale (re-verified: `CLAUDE.md:258`); line 259 "37-phase refinement sequence" is already correct (re-verified: `CLAUDE.md:259`) — do not touch 259 |

Then add a short "Remaining ~94 files (existence/self-consistency pass only)" section: state that
`docs/engine/contracts/` (34 files) and `docs/engine/matrices/` (~21 files), plus the remaining
top-level `docs/engine/`, `docs/architecture/`, and `docs/performance/` files not in the table
above, were checked only for (a) file existence matching any manifest/registry reference and (b)
no internal self-contradiction spotted on a single read-through — not cross-doc fact-checked at
D17 depth. State plainly this is a lighter pass, not a gap being hidden.

**Do NOT touch:** Any doc content outside the audit doc itself in this step — edits to
README.md/CLAUDE.md/architecture.md happen in Steps 3-4, not here.

**Verify:** No automated test covers audit-doc prose content directly; verify by re-reading the
doc against this plan's table before Implement closes the step. `tests/docs/test_doc_integrity.py`
must still pass unchanged (this doc is not added to `manifest.json`'s `mandatory_documents`).

### Step 2 — Audit doc: record the four contradictions (resolve-by-cross-reference or defer)

**Files:** `docs/audits/D25_engine_docs_drift.md` (continued)

**Change:** Add a "Known Contradictions" section with four subsections, each following the exact
pattern already established at `docs/performance/perf_baseline_policy.md:30-35`
(`> **Known conflict, not resolved here**: ...` blockquote):

1. **Concurrency contradiction** — cross-link only (already ticketed, do not re-fix): cite
   `docs/engine/kernel.md:55` vs `docs/engine/contracts/simulation_kernel_contract.md:57`, and
   `TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION` (status OPEN in
   `tickets/todos/kernel-concurrency-design-review/`).
2. **Phase-count contradiction** — cross-link to `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION`
   (status OPEN, same folder), and separately note the two new-evidence folds this ticket is
   adding directly (README.md's 17-phase line, CLAUDE.md line 258 — both fixed in Steps 3-4 of
   *this* ticket, not the seed ticket).
3. **Hardware-class conflict (OBSISO)** — state plainly that `perf_baseline_policy.md:30-35`
   already satisfies the "formally defer" requirement; this section only adds a cross-reference
   from the new audit doc to that existing box, cite `TCK-20260702-OBSISO-ISOLATION-PROOF`.
4. **`simulation_kernel_contract.md` §9 broader staleness** — record as an **unconfirmed
   hypothesis needing owner confirmation**, not a fix. State the three stale bullets
   ("No scheduler optimization" vs `src/engine/scheduler.py:33`'s `DeterministicScheduler.select_work()`
   LOD gating; "No adaptive degradation" vs `src/core/governance.py:8-16`'s `RuntimeMode` ladder;
   "No external event brokers" vs `src/simulation_quality/feed.py`'s Redis broker mode — all per
   investigation.md's own source citations, not independently re-verified in planning since these
   are code-behavior claims investigation.md already grounded in file:line reads) and the
   `minimal_kernel.md` wording-overlap hypothesis. End with: "Needs owner confirmation before any
   fix — do not silently adopt the minimal_kernel.md-scope reading."

**Do NOT touch:** `simulation_kernel_contract.md` §9's actual text — no edit, anywhere in this
ticket, changes its content. Do not add or edit any `docs/parity_ledger/*.yaml` entries for these
four items — investigation.md confirms none currently exist and the seed tickets own that AC.

**Verify:** Manual read-through against Acceptance Criteria #2 ("explicitly resolves-by-cross-
reference or formally defers ... each of the four ... cross-linking D17, P0-DOC-REPAIR, OBSISO").
Confirm all three ticket IDs (D17 = `TCK-20260618-AUDIT-D17-DOCS`, P0-DOC-REPAIR =
`TCK-20260619-P0-DOC-REPAIR`, OBSISO = `TCK-20260702-OBSISO-ISOLATION-PROOF`) appear in the doc.

### Step 3 — Direct edit: `docs/engine/README.md` (two stale lines)

**Files:** `docs/engine/README.md`

**Change:** At line 13, replace "The 6-phase orchestrator (Init, Governance, Scheduling,
Packetization, Resolution, Persistence)" with kernel.md's real 7-phase list (INIT, SCHEDULING,
COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE), matching kernel.md's own phrasing
exactly per the canonical-doc-per-topic rule (kernel.md is canonical, README.md is a satellite —
cross-link, do not independently redefine). At line 14, replace "The 17-phase refinement sequence"
with "37-phase" to match `docs/engine/authoritative_pipeline.md`'s already-corrected figure
(verified passing today via `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py:18`'s
assertion that `"37 phases"` is in that file). Both lines re-verified during planning at
`docs/engine/README.md:13-14` (exact current text quoted above in Step 1's table).

**Do NOT touch:** Any other line in README.md. Do not touch `docs/engine/kernel.md` or
`docs/engine/authoritative_pipeline.md` themselves — they are already correct (canonical sources),
this step only corrects the satellite.

**Verify:** New test `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs`
(Step 6) checks README.md no longer contains "GOVERNANCE"/"PACKETIZATION". Manual check that
"17-phase" no longer appears and "37-phase" or "37 phases" does.

### Step 4 — Direct edit: `CLAUDE.md` line 258 only

**Files:** `CLAUDE.md`

**Change:** Replace line 258's cell text "6-phase deterministic loop (Init → Governance →
Scheduling → Packetization → Resolution → Persistence)" with the real 7-phase list, matching
kernel.md. Re-verified during planning: `CLAUDE.md:258` currently reads exactly this stale text;
`CLAUDE.md:259` (the adjacent row) already correctly reads "37-phase refinement sequence for world
mutation" — confirmed unchanged and correct.

**Other writers to this file:** `CLAUDE.md` is not script-generated — confirmed via
`grep -rl "CLAUDE.md" tools/ scripts/`, which returns only tools that *read* or *reference*
CLAUDE.md (`tools/knowledge_gateway_cache.py`, `tools/agent-monitoring/generate_retro.py`, etc.),
none that write/regenerate it. `TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT`
(commit `51c97457`) previously hand-edited line 259 directly, not via a generator — this step
follows the same direct-edit pattern for line 258. No other in-flight ticket in
`tickets/inprogress/` touches CLAUDE.md (verified via directory listing during planning), so no
concurrent-write collision risk for this session.

**Do NOT touch:** Line 259, or any other line in CLAUDE.md. Do not touch the Engine Contracts
table's other rows (`authoritative_mutation_pipeline_contract.md`, `governance_logic.md`,
`performance_contract.md`, `known_limitations.md` rows) — none were flagged as stale by
investigation.md.

**Verify:** New test in Step 6 checks CLAUDE.md no longer contains "GOVERNANCE"/"PACKETIZATION".

### Step 5 — Direct edit: `docs/engine/architecture.md` §5 callout box (defer, not fix)

**Files:** `docs/engine/architecture.md`

**Change:** Immediately after the existing §5 hardware-class table (currently lines 88-93, ending
"Class C (High-Performance): Enhanced observability profiles."), insert a callout box matching
`perf_baseline_policy.md:30-35`'s exact convention:

```
> **Known conflict, not resolved here**: This table's Class A/B/C mapping is inverted relative to
> `docs/engine/contracts/certification_contract.md` §3 and `docs/performance/perf_baseline_policy.md`
> §2.2, both of which make Class A the *most* powerful tier (≥16 cores/≥32GB or "High-Performance
> Server"). This table makes Class A the *least* powerful ("Low-Power," 10 TPS) and Class C the
> most powerful — an opposite-direction conflict, not just a threshold disagreement. Newly found by
> TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT; see also the pre-existing, differently-shaped conflict
> already flagged at `docs/performance/perf_baseline_policy.md`'s own callout box
> (TCK-20260702-OBSISO-ISOLATION-PROOF). Not fixed here — pending owner decision on which mapping
> is canonical.
```

Re-verified during planning: `docs/engine/architecture.md:88-93` currently has no callout box of
any kind after this table (confirmed by reading lines 40-99 in full during planning).

**Do NOT touch:** The table's own numeric values or letter labels — this step only adds a callout
box, it does not correct, reorder, or renumber the table. Do not add/edit anything in
`certification_contract.md` or `perf_baseline_policy.md` — both stay as the (already-correct)
canonical references being cited, not edited.

**Verify:** No automated test covers this callout box (the optional test_plan.md item 4
"callout-box presence check" is explicitly not added — see Scope Guards) — verify by manual
re-read that the blockquote text and formatting match `perf_baseline_policy.md:30-35`'s
convention (leading `> **Known conflict, not resolved here**:`).

### Step 6 — New living test: `tests/docs/test_kernel_phase_names_consistent.py`

**Files:** `tests/docs/test_kernel_phase_names_consistent.py` (new)

**Change:** Add the exact test file investigation.md's "Proposed Structural Convention" section
already drafted (copy directly, do not re-derive), with one addition: wrap
`test_no_fabricated_phase_names_in_kernel_docs` in `@pytest.mark.xfail(strict=True, reason=...)`
citing both open seed ticket IDs (see Design Decisions for why xfail, not sequencing).
`test_kernel_doc_states_all_seven_real_phases` is **not** xfail-guarded — kernel.md is already
correct today (verified: `docs/engine/kernel.md:21-27` per investigation.md, canonical and
unmodified by this ticket), so this half must pass immediately, unguarded.

```python
from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent.parent
# "GOVERNANCE" is checked case-sensitive only: a case-insensitive check would false-
# positive on legitimate uses (docs/engine/contracts/governance_logic.md's citations,
# architecture.md's own "Phase Governance" section heading). This safely catches
# architecture.md's ALL-CAPS table entry today. "PACKETIZATION" has no legitimate use
# in any casing, so it's checked case-insensitively to also catch the Title-Case
# "Packetization" occurrences in README.md/CLAUDE.md/docs/guides/simulation.md that a
# case-sensitive-only check would miss (found during Review — see architecture-reviewer
# note on TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT's Review phase).
FORBIDDEN_PHASE_NAME_GOVERNANCE = "GOVERNANCE"  # case-sensitive
FORBIDDEN_PHASE_NAME_PACKETIZATION = "packetization"  # checked case-insensitively
REAL_PHASES = ("INIT", "SCHEDULING", "COLLECTION", "RESOLUTION", "CLEANUP",
               "ADVANCEMENT", "PERSISTENCE")

PHASE_NARRATING_DOCS = [
    "docs/engine/kernel.md",
    "docs/engine/architecture.md",
    "docs/engine/README.md",
    "docs/engine/contracts/simulation_kernel_contract.md",
    "docs/guides/simulation.md",
    "CLAUDE.md",
]

@pytest.mark.xfail(
    strict=True,
    reason=(
        "architecture.md still narrates a fabricated 6-phase GOVERNANCE/PACKETIZATION "
        "loop pending TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION (OPEN); remove this "
        "marker once that ticket and TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION "
        "(OPEN) both land and this test passes for real."
    ),
)
def test_no_fabricated_phase_names_in_kernel_docs():
    """GOVERNANCE and PACKETIZATION are not real _phase_* methods in src/engine/kernel.py.
    This exact fabricated pair independently drifted into architecture.md, README.md,
    CLAUDE.md, and docs/guides/simulation.md after being fixed once in kernel.md
    (TCK-20260619-P0-DOC-REPAIR) — TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT."""
    for rel_path in PHASE_NARRATING_DOCS:
        text = (ROOT / rel_path).read_text()
        assert FORBIDDEN_PHASE_NAME_GOVERNANCE not in text, (
            f"{rel_path} contains fabricated phase name {FORBIDDEN_PHASE_NAME_GOVERNANCE!r}"
        )
        assert FORBIDDEN_PHASE_NAME_PACKETIZATION not in text.lower(), (
            f"{rel_path} contains fabricated phase name 'packetization' (any casing)"
        )

def test_kernel_doc_states_all_seven_real_phases():
    """The canonical doc (kernel.md) must name all 7 real phases — guards against a future
    partial/stale rewrite in the other direction."""
    text = (ROOT / "docs/engine/kernel.md").read_text()
    for phase in REAL_PHASES:
        assert phase in text, f"kernel.md missing real phase name {phase!r}"
```

Note: after Steps 3-4 land (README.md, CLAUDE.md fixed), `architecture.md` alone still contains
GOVERNANCE/PACKETIZATION (Step 5 only adds a callout box, does not remove the fabricated names —
that fix belongs to the out-of-scope seed ticket). So
`test_no_fabricated_phase_names_in_kernel_docs` is expected to keep failing (xfail) through this
ticket's own closure — this is correct, not a bug in the plan.

**Other writers to this shared test-collection area:** `tests/docs/__init__.py` and the other 8
files in `tests/docs/` (`test_doc_integrity.py`, `test_contributor_guardrails.py`,
`test_design_patterns_currency.py`, four `test_phaseN_*.py` files, `test_redaction_retention_policy_doc.py`
— confirmed via directory listing) are untouched by this step; this is a net-new file, no merge
conflict with any of them. No other ticket in `tickets/inprogress/` currently adds a file to
`tests/docs/` (verified via directory listing during planning).

**Do NOT touch:** `tests/docs/test_doc_integrity.py` or `docs/engine/manifest.json` in this step —
this is a deliberately separate, parallel mechanism, not an extension of the existing
`monitored_terminology` pattern (see Design Decisions).

**Verify:** `pytest tests/docs/test_kernel_phase_names_consistent.py -v` — expect
`test_no_fabricated_phase_names_in_kernel_docs` to report `XFAIL` (strict) and
`test_kernel_doc_states_all_seven_real_phases` to report `PASS`.

### Step 7 — New test: doc-path-existence check

**Files:** `tests/docs/test_doc_path_existence.py` (new)

**Change:** Add a new test that extracts repo-relative path-shaped strings from every `.md` file
under the three ticket-scoped directories only (`docs/engine/`, `docs/architecture/`,
`docs/performance/` — not all of `docs/**`, see Scope Guards) and asserts each resolves via
`Path(...).exists()`. Heuristic: regex-match backtick-quoted or bare tokens matching
`(src|tests|tools|docs)/[\w./-]+\.\w+` (a file-extension-bearing path under one of the four known
top-level source/doc roots). Exclude:
- Any doc whose frontmatter `status` is not `active` (parse the YAML frontmatter block, skip if
  `status != active`) — covers intentionally-historical docs.
- The `docs/archive/` directory entirely, if any path under audit happens to reference it.
- Any match inside a fenced code block that is illustrative pseudocode rather than a real citation
  — out of scope to detect heuristically; if this causes false positives during Implement, narrow
  the regex further rather than hand-exempting individual strings (keep the exemption mechanism
  structural: frontmatter status, not a hardcoded path allowlist, to avoid the same class of silent
  drift this ticket exists to prevent).

This test is what would have caught `docs/guides/simulation.md:26`'s
`src/engine/authoritative_pipeline.py` citation — re-verified during planning that this exact path
does not exist (`ls src/engine/authoritative_pipeline.py` → "No such file or directory") while
`src/engine/pipeline.py` does exist. Since Step 3-4-5 do not touch `docs/guides/simulation.md`
(it's not in this ticket's four direct-edit list — see Design Decisions on why it's flagged but not
edited), this test is expected to **fail** on that one citation immediately after being added,
unless Implement also fixes `docs/guides/simulation.md:26` as part of this step (recommended: fix
it inline here, since it's a one-line, unambiguous, non-controversial existence-check fix,
distinct from the phase-count prose fix which stays deferred to the seed ticket).

**Other writers to this shared resource:** `docs/**/*.md` is written by every ticket in this repo
that touches docs — this test does not lock or claim ownership of any file, it only reads at test
time, so there is no write-collision risk. The risk is a *future* ticket adding a new doc with a
dead path reference and this test catching it (working as intended, not a collision).

**Do NOT touch:** `docs/engine/manifest.json` — this check is intentionally a separate file, not
folded into the manifest's existing `mandatory_documents`/`forbidden_terms`/`monitored_terminology`
schema (see Design Decisions).

**Verify:** `pytest tests/docs/test_doc_path_existence.py -v` passes after the
`docs/guides/simulation.md:26` path citation is corrected (either by this step directly, or —
if Implement judges that out of this step's footprint — filed as a one-line addendum to Step 3's
README.md edit batch; either placement is acceptable, but the citation must be fixed somewhere in
this ticket's Implement pass since AC requires the new test to pass, not merely exist).

### Step 8 — Cross-link: `docs/plans/kernel_concurrency_design_review_proposal.md`

**Files:** `docs/plans/kernel_concurrency_design_review_proposal.md`

**Change:** In the "Known documentation drift (see C2, C3, C8 in the parent proposal for
follow-up)" section (currently lines 304-311, confirmed present during planning, listing the same
3 items: concurrency contradiction, phase-count contradiction, hardware-class conflict), add one
line after the existing 3-item list: "**Update (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT, closed
2026-08-2x):** full audit recorded at `docs/audits/D25_engine_docs_drift.md`, including a 4th newly-
found item (architecture.md's inverted hardware-class table) and 2 direct fixes (README.md,
CLAUDE.md) folded in beyond this list's original 3." Do not renumber or remove the original 3-item
list — it stays as historical record of what C8 originally named.

**Other writers to this file:** This is the C1-C8 origin document; `TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC`
(#6 in SEQUENCE.md, depends on tickets #4/#5) will likely also touch this file later in the same
batch for its own "Part 1 — Design Philosophy" content. This step's edit is additive (one new line
in an existing section) and does not touch any section that ticket #6's design-doc work would
plausibly also edit (its own scope is the C1 design philosophy content, not the C8 known-drift
list) — low collision risk, but flag for whoever runs ticket #6 to re-check this section wasn't
clobbered by a stale rebase.

**Do NOT touch:** Any other section of this file (Parts 1-5, References, etc.) — this ticket's
scope is the one cross-link only.

**Verify:** Manual read; no automated test covers this file's prose content.

### Step 9 — Audit doc: parity-ledger gap note (no fix)

**Files:** `docs/audits/D25_engine_docs_drift.md` (continued)

**Change:** Add a short "Parity Ledger Notes" section citing `docs/parity_ledger/substrate.yaml`
`SUB-008` (re-verified during planning at `docs/parity_ledger/substrate.yaml:74-81`: `status:
legacy_verified`, `priority: P0`, `test_path: null`, `text: "Engine phase order preserves gameplay
semantics and subsystem tick integrity."`) — state that this P0 entry has no passing `test_path`
today, that CLAUDE.md's own rule requires P0 entries to have one, and that this is a pre-existing
gap this ticket flags but does not fix (adding a test for SUB-008 is not in this ticket's scope).
Also note `SUB-307`/`SUB-308`/`SUB-309` as a likely parity-ledger metadata gap (missing
`test_path` field despite `kernel.md` citing a real test,
`tests/architecture/test_phase_domain_permissions.py`) — noted for completeness only.

**Do NOT touch:** `docs/parity_ledger/substrate.yaml` itself — no YAML edits in this ticket.

**Verify:** Manual read-through; no test covers this note's content directly.

### Step 10 — Audit doc: enforcement-mechanism section + follow-up-ticket recommendation

**Files:** `docs/audits/D25_engine_docs_drift.md` (continued)

**Change:** Add the "Proposed Structural Convention + Enforcement Mechanism" content from
investigation.md verbatim (the canonical-doc-per-topic table plus the two-part enforcement
mechanism description), since it's already fully drafted and satisfies Acceptance Criteria #3.
Then add a closing "Recommended Follow-Up" section stating precisely:

> **Follow-up ticket recommendation (not filed by this ticket):** `TCK-<date>-AUDIT-ENGINE-CONTRACTS-MATRICES-DRIFT`,
> tier `standard`, layer `engine`, scoped to full D17-depth (3-5 verifiable claims/doc) coverage of
> `docs/engine/contracts/` (34 files) and `docs/engine/matrices/` (~21 files) — the ~55 files this
> ticket's lighter existence/self-consistency pass did not deep-check. Rationale: these are
> narrower, single-topic contract docs individually less likely to carry cross-doc narrative
> contradictions than the broad docs this ticket already deep-checked, but have not been verified
> at D17 depth by any ticket to date. This ticket's own Out of Scope clause explicitly permits this
> split ("Full D17-depth audit of all 102 files if Plan-phase confirms breadth exceeds one ticket —
> may split into directory-scoped follow-ups"). **This ticket's Implement phase does not create
> that follow-up ticket file** — filing it (via the `create-tickets` skill) is a separate, later
> action, left to whoever picks up this recommendation.

**Do NOT touch:** Do not actually run `create-tickets` or write a new ticket file for the follow-up
during this ticket's Implement phase — that would exceed this ticket's own chore-tier scope (audit
+ doc edits + one living test), and the ticket's Out of Scope clause frames the split as a
recommendation Plan/Implement documents, not executes.

**Verify:** Manual read; Acceptance Criteria #1's "sampled at D17's own depth, not claimed
exhaustive" is satisfied by this section explicitly naming what was and wasn't covered.

## Scope Guards

- Do not fix the Collection-concurrency contradiction (`kernel.md` vs
  `simulation_kernel_contract.md` §9's concurrency framing) — owned by
  `TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION`.
- Do not fix the 6-phase vs 7-phase contradiction beyond the two new-evidence folds this plan
  names (README.md, CLAUDE.md line 258) — the core contradiction fix is owned by
  `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION`.
- Do not resolve the hardware-class conflict (OBSISO or the new architecture.md inversion) — both
  get callout boxes only, no corrected numeric values.
- Do not resolve the `simulation_kernel_contract.md` §9 hypothesis — record only, no edit to §9's
  text anywhere in this ticket.
- Do not edit `docs/architecture/simulation_watchdog.md` — already fixed by Epic B; treating it as
  broken would be acting on stale roadmap-doc history, not current investigation.md findings.
- Do not touch `CLAUDE.md:259` — already correct (37-phase), editing it would indicate work from
  stale ticket-text evidence rather than this investigation's verified correction.
- Do not touch `docs/engine/project_lawbook_m10.md`'s independent 5-item pillar restatement — noted
  in the audit doc as a newly-found duplicate instance, not fixed (would be new unscoped work).
  restating it as duplicate is descriptive, not a fix commitment.
- Do not fold the doc-path-existence check into `docs/engine/manifest.json` /
  `tests/docs/test_doc_integrity.py` — keep it a separate file (Step 7); do not modify
  `manifest.json`'s existing `mandatory_documents`/`forbidden_terms`/`monitored_terminology` keys.
- Do not scope the doc-path-existence check beyond `docs/engine/`, `docs/architecture/`,
  `docs/performance/` — this ticket's own directory scope, not all of `docs/**`.
- Do not add the optional "callout-box presence check" test (test_plan.md item 4) — explicitly
  declined as a minor, low-priority item test_plan.md itself left to Plan's discretion (a
  single-string grep on a prose convention is brittle and the ticket's AC does not require it;
  Steps 5/9's manual-read verification is sufficient).
- Do not add or edit any `docs/parity_ledger/*.yaml` entries — this ticket defers, it does not fix,
  so no parity-status transition applies.
- Do not file the recommended follow-up ticket (`AUDIT-ENGINE-CONTRACTS-MATRICES-DRIFT`) as part of
  this ticket's Implement pass — document the recommendation only (Step 10).

## Dependency Map

All 10 steps operate on disjoint files except where noted:
- Steps 1, 2, 9, 10 all edit the same new file (`docs/audits/D25_engine_docs_drift.md`) — must run
  in order 1 → 2 → 9 → 10 (each appends a new section; no reordering hazard, but write
  sequentially to avoid merge-in-place confusion).
- Steps 3, 4, 5, 8 each touch a distinct existing file (README.md, CLAUDE.md, architecture.md,
  kernel_concurrency_design_review_proposal.md respectively) — fully independent of each other and
  of Steps 1/2/9/10.
- Step 6 (new test file) has no file dependency on Steps 3-5's content — it's written once, xfail
  from the start, and does not require Steps 3-4 to land first (unlike the "sequence after seed
  tickets" alternative this plan rejected). It can run any time after Step 1 conceptually, but has
  no hard ordering requirement.
- Step 7 (doc-path-existence test) should run after Step 3 (or include its own fix to
  `docs/guides/simulation.md:26`) so the test passes on first run rather than landing red.
- No step depends on the two out-of-scope seed tickets landing first.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Audit doc enumerates every doc across the three directories (~102/110 files) with classification, sampled at D17 depth, not claimed exhaustive | Steps 1, 10 | Manual read-through; no automated test covers audit-doc prose |
| Audit explicitly resolves-by-cross-reference or formally defers each of: concurrency, phase-count, hardware-class, §9 staleness — cross-linking D17, P0-DOC-REPAIR, OBSISO | Step 2 | Manual read-through confirming all 3 ticket IDs present |
| Concrete structural convention WITH enforcement mechanism, with at least one example wired into a living test | Steps 6, 10 | `pytest tests/docs/test_kernel_phase_names_consistent.py -v` |
| Any newly-found P1-vs-P1 contradiction NOT fixed in this ticket recorded via callout-box, citing this ticket's ID | Step 5 (architecture.md hardware-class inversion) | Manual read; matches `perf_baseline_policy.md:30-35` convention |
| (Scope, from ticket body) README.md's two stale phase claims fixed | Step 3 | `test_no_fabricated_phase_names_in_kernel_docs` (xfail overall, but README.md's own contribution to the forbidden-name set is removed) + manual "17-phase" absence check |
| (Scope) CLAUDE.md line 258 fixed, line 259 untouched | Step 4 | Manual diff; same living test's forbidden-name check |
| (Scope) guides/simulation.md fold-in | Step 7 (path-existence fix) | `pytest tests/docs/test_doc_path_existence.py -v` |
| (Scope) doc-path-existence check implemented now | Step 7 | `pytest tests/docs/test_doc_path_existence.py -v` |
| (Scope) kernel_concurrency_design_review_proposal.md cross-link | Step 8 | Manual read |

## Design Decisions

### 1. Audit breadth: adopt the investigation's scope-down recommendation

**Decision:** Cover the 16 docs already deep-checked in investigation.md (kernel.md,
architecture.md, simulation_kernel_contract.md, minimal_kernel.md, authoritative_pipeline.md,
README.md, certification_contract.md, performance_contract.md, worker_contract.md,
project_lawbook.md, project_lawbook_m10.md, simulation_watchdog.md, perf_baseline_policy.md,
simq_isolation_overhead.md, docs/guides/simulation.md, CLAUDE.md) at D17 depth in the audit doc,
plus a lighter existence/self-consistency pass over the remaining ~94, and explicitly recommend
(without filing) a follow-up ticket for full-depth `docs/engine/contracts/` +
`docs/engine/matrices/` coverage.

**Rationale:** The ticket's own Out of Scope clause explicitly permits this split ("may split into
directory-scoped follow-ups") conditioned on "Plan-phase confirms breadth exceeds one ticket."
Investigation confirms the real count is 110, not the ticket's ~102 estimate, and that the 16
already-checked docs already meet or exceed D17's own 9-doc precedent depth. Re-doing that same
depth across the full 110 within this ticket's remaining budget would either violate the
"D17's own depth" sampling instruction (by going shallower per doc to cover more files) or blow the
standard-tier ticket's realistic scope. The `docs/engine/contracts/` and `docs/engine/matrices/`
subdirectories are individually narrower single-topic contract docs — lower prior probability of
cross-doc narrative contradiction than the broad docs already checked (which is exactly where all
4 real contradictions found so far live). Filing the actual follow-up ticket is left out of this
ticket's Implement pass because ticket creation is a distinct action (the `create-tickets` skill)
outside a chore-tier docs ticket's natural footprint — the plan documents the recommendation
precisely enough (title pattern, tier, layer, exact file counts, rationale) that whoever picks it
up doesn't need to re-derive scope.

### 2. Living-test sequencing: add now with `xfail(strict=True)`, do not sequence Implement after the seed tickets

**Decision:** Add `tests/docs/test_kernel_phase_names_consistent.py` now, with
`test_no_fabricated_phase_names_in_kernel_docs` wrapped in `pytest.mark.xfail(strict=True,
reason=...)` citing both open seed ticket IDs. Do not delay this ticket's Implement phase until
the seed tickets close.

**Rationale:** `tickets/todos/kernel-concurrency-design-review/SEQUENCE.md` (read in full during
planning) places this ticket (`TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`) at position **#1** in the
8-ticket batch, explicitly marked "no deps in this batch," while the two seed tickets
(`TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION`, `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION`)
sit at positions **#4** and **#5**, also independently marked "no deps in this batch." Since
`implement-epic` executes SEQUENCE.md's tickets in listed order, this ticket's own Implement →
Test → Verify → Finalize pipeline will run and complete *before* either seed ticket's pipeline
even starts. That makes option (a) — "sequence this ticket's Implement after both seed tickets
land" — not something this plan can adopt without unilaterally overriding a batch-ordering file
this ticket doesn't own; doing so would also stall this ticket indefinitely relative to its stated
batch position for no benefit within this ticket's own scope. Option (b) (xfail now) has a useful
side effect precisely because of `strict=True`: once tickets #4/#5 land later in the same batch and
remove the fabricated phase names from architecture.md, this test will unexpectedly pass (XPASS),
and `strict=True` turns an XPASS into a hard failure — forcing whichever session implements ticket
#4 or #5 to notice this test and remove the xfail marker as part of closing their own work, rather
than the drift-guard silently going stale a second time (the exact "fixed once, re-drifted
independently" failure pattern this whole ticket exists to prevent, now self-enforcing at the test
level). This is noted in the xfail `reason=` string itself so it's discoverable without re-reading
this plan.

## Anti-Drift Notes

- The `simulation_watchdog.md` doc is already fixed (Epic B) — investigation.md verified this
  directly; do not schedule any work against it or describe it as broken in the audit doc, even
  though the roadmap doc (`architecture_resilience_remediation_roadmap.md`) still describes it as
  needing a fix. That roadmap text is pre-fix history.
- CLAUDE.md's alleged "32-phase" claim (named in the ticket body and the roadmap doc) does not
  exist in the live file — `CLAUDE.md:259` already correctly reads "37-phase." Do not "fix" this;
  it was already fixed by `TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT` before this
  ticket ran. The real, still-open CLAUDE.md issue is line 258 (kernel-loop phase count), addressed
  in Step 4.
- `test_no_fabricated_phase_names_in_kernel_docs` is *expected* to report `XFAIL` at this ticket's
  own closure, not `PASS` — do not treat a lingering XFAIL as this ticket having failed its own
  acceptance criteria. The AC requires the test to exist and be wired in, not for it to pass yet
  (the underlying contradiction it guards is explicitly out of scope to fix here).
- No new `docs/parity_ledger/*.yaml` entries or status transitions in this ticket — it defers, it
  does not fix, so CLAUDE.md's "if logic changes, update the parity ledger" rule does not trigger
  (no logic changed; docs-only).
- Per CLAUDE.md's After-Work checklist: since this ticket creates/modifies files under `docs/`,
  `make knowledge-index-update` must run before Finalize closes the ticket.

## Deviations (recorded during Implement)

1. **`tests/docs/test_doc_path_existence.py` does not pass cleanly on first run — it is
   `xfail(strict=True)`, not a clean `PASS`.** The plan's Step 7 assumed (based on
   investigation.md's single worked example, `docs/guides/simulation.md`'s
   `authoritative_pipeline.py` citation — itself outside this test's own directory scope) that the
   test would pass once that one citation was fixed. Running the test for real against the three
   scoped directories surfaced **34 dead path citations across 17 files**, not one. 22 were
   real renames/relocations, confirmed via unique-match search and fixed directly during Implement
   (e.g. `tests/engine/test_worker_integrity.py` → `tests/unit/kernel/test_worker_integrity.py`,
   `docs/guidelines/v2_intentional_divergences.md` → `docs/guidelines/intentional_divergences.md`,
   `docs/engine/contracts/sweep_configuration.md` → `docs/archive/engine_contracts/sweep_configuration.md`).
   Two bugs in the check itself were also found and fixed: a missing regex word-boundary that
   mis-truncated `dashboard-frontend/src/...` paths (false positive), and a missing `src/legacy/`
   exemption for `docs/engine/legacy_replacement_ledger.md`'s intentionally-dead historical entries
   (also false positive). The remaining **12 citations were left unfixed** — zero-candidate
   searches (no renamed file found anywhere in the tree) indicate most were never implemented
   rather than simply moved, and one has 4 ambiguous candidates; resolving any of them with
   confidence requires per-doc investigation at the depth this plan's own Design Decision #1
   already reserved for the recommended follow-up ticket, not this chore-tier ticket's Implement
   pass. These 12 are now tracked via `pytest.mark.xfail(strict=True, reason=...)` on
   `test_doc_path_citations_exist`, the identical pattern already used by Step 6's
   `test_no_fabricated_phase_names_in_kernel_docs`, and are itemized in
   `docs/audits/D25_engine_docs_drift.md`'s "Recommended Follow-Up" section as concrete backlog for
   that ticket. No test assertion or check logic was weakened to force a pass — every citation the
   test flags is either fixed, or genuinely deferred and disclosed, never hidden.
2. **A pre-existing, unrelated test regression was discovered, not caused by broken logic, but
   directly triggered by this ticket's approved Step 4 edit.**
   `tests/docs/test_prescan_mandate_instruction_draft.py::test_draft_does_not_modify_claude_md_or_agent_md_files`
   (from the already-closed `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`) asserts
   `git diff --stat HEAD -- CLAUDE.md .claude/agents/*.md` is empty — a permanent regression guard
   left in the suite after that ticket closed, which will fail for **any** future commit that
   touches `CLAUDE.md`, not just this one. This ticket's Step 4 (`CLAUDE.md:258` fix) is required,
   approved scope; the plan's own Step 4 risk analysis confirmed no *other in-flight* ticket
   touches `CLAUDE.md`, but did not anticipate this leftover guard from an already-*closed*
   ticket. Not fixed here — editing another ticket's test file is outside this ticket's Do-NOT-
   touch-bounded scope; flagged for a separate hotfix to loosen or remove that guard.
