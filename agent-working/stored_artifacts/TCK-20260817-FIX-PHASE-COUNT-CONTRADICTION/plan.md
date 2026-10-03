---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION
artifact_type: plan
tags: [documentation, engine]
---

# Implementation Plan — TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION

## Summary
This is a docs-only reconciliation. `docs/engine/architecture.md` §2 (lines 45–58, read directly
and confirmed) still carries a fabricated 6-phase table with GOVERNANCE (row 2) and PACKETIZATION
(row 4) that do not correspond to any real `_phase_*` method on `Kernel`
(`src/engine/kernel.py::_tick_once_inner`, confirmed by investigation.md lines 15–29: the 7 real
phases in order are INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE).
The plan rewrites that table and its surrounding heading/prose to match, adds a reconciling note to
`substrate_baseline_contract.md` §4 (confirmed by direct read: lines 26–37, "MUST execute the
following 6 phases" — INIT through ADVANCEMENT, with PERSISTENCE separately described in an
"Observational Boundary" subsection at lines 36–37 as non-authoritative), adds a new parity ledger
entry, and — as the plan's one scope decision — also fixes `docs/guides/simulation.md` lines 19–20
and 25 (confirmed by direct read) because the living test
`tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs`
(confirmed by direct read, lines 18–25) checks that file too, and the ticket's own dispatch intent
is for the `xfail` marker removal to produce a real pass, not a new real failure. `docs/engine/README.md`,
`docs/engine/kernel.md`, `docs/engine/contracts/simulation_kernel_contract.md`, and `CLAUDE.md` are
all confirmed already clean (zero `GOVERNANCE`/`packetization`-any-casing grep hits, re-verified
directly in this session) and require no edits — do not touch them.

## Design Decisions

### Decision: fix `docs/guides/simulation.md` in this ticket (investigation's option (a))
The ticket body's Scope/Related Docs/Acceptance Criteria never name `docs/guides/simulation.md`.
However:
- The living test's `PHASE_NARRATING_DOCS` list (`tests/docs/test_kernel_phase_names_consistent.py`
  lines 18–25, confirmed by direct read) includes `docs/guides/simulation.md`.
- Direct read of `docs/guides/simulation.md` lines 19–20 confirms it still reads: "Every simulation
  run is a deterministic 6-phase loop (Init → Governance → Scheduling → Packetization → Resolution →
  Persistence) repeated per tick." and line 25: "`src/engine/kernel.py` — the 6-phase loop" — the
  identical fabricated defect this ticket exists to fix, just in a third file.
- The `xfail` marker's own `reason=` string (test file lines 29–34, confirmed by direct read) cites
  only this ticket and the already-closed `TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION` as
  blockers to remove once both land — implying the dispatcher expected this ticket's closure to make
  the full `PHASE_NARRATING_DOCS` loop pass, including `docs/guides/simulation.md`.
- If this file is left unfixed, Step 3 (marker removal) would convert a designed `strict-xfail` catch
  into an ordinary `AssertionError` on `docs/guides/simulation.md` — not the "real pass" the marker
  removal is supposed to produce.

Decision: adopt option (a). Fix only the phase-name/phase-count sentence and the "6-phase loop" label
on line 25 of `docs/guides/simulation.md`, alongside `architecture.md`, in Step 2 below. Do **not**
touch line 26 (`src/engine/pipeline.py — the 17-phase mutation sequence`) — that is a separate,
pre-existing 17-vs-37 pipeline-count mismatch against `docs/engine/README.md`'s "37-phase refinement
sequence" claim, unrelated to kernel-tick phase names, and out of this ticket's scope per
investigation.md's Risks section. This scope addition is recorded here and must also appear in
`Implementation Notes` on the ticket itself when Implement runs.

## Steps

### Step 1 — Fix `docs/engine/architecture.md` §2 heading and prose
**Files:** `docs/engine/architecture.md` (lines 45–47)
**Change:** Read directly, confirmed current text:
- Line 45: `## 2. The 6-Phase Deterministic Kernel Loop`
- Line 47: `Every tick executes exactly six phases in a strict, contract-enforced sequence. This "Law of Ticks" is fixed and immutable.`

Change line 45 to `## 2. The 7-Phase Deterministic Kernel Loop` and line 47 to `Every tick executes
exactly seven phases in a strict, contract-enforced sequence. This "Law of Ticks" is fixed and
immutable.` No other wording on these two lines changes.
**Do NOT touch:** Line 43 (`---` separator), line 49 (`### Phase Sequence & Contracts` heading), or
anything before line 45.
**Verify:** `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs`
(after Step 3's marker removal); no standalone test covers heading/prose text alone, so this step's
correctness folds into the Step 3 verification.

### Step 2 — Replace the fabricated phase table rows in `docs/engine/architecture.md` §2, and fix `docs/guides/simulation.md`'s matching sentence
**Files:** `docs/engine/architecture.md` (lines 51–58), `docs/guides/simulation.md` (lines 19–20, 25)
**Change:**
For `architecture.md`, the current table (read directly, confirmed):
```
| Phase | Responsibility | Permissions (READ / MUTATE) |
| :--- | :--- | :--- |
| **1. INIT** | Increments simulation clock and resets per-tick buffers. | `state.world_time` / `state.world_time` |
| **2. GOVERNANCE** | Evaluates resource pressure (RAM/CPU) and calculates the **Degradation Mode**. | `status.signals`, `profile` / `governor.policy` |
| **3. SCHEDULING** | Identifies entities due to act and selects work based on the **Work Debt** budget. | `state.entities`, `policy` / `tick_work` |
| **4. PACKETIZATION** | Offloads AI deliberation tasks to the `WorkerPool` using compact packets. | `tick_work`, `policy` / `worker_results` |
| **5. RESOLUTION** | **Authoritative Update**. Converts results into `StateUpdate` and applies it via `ApplyPath`. | `worker_results` / `state.authoritative` |
| **6. PERSISTENCE** | **External Phase**. Streams `TraceEvent` records to the `ReplayManager`. | `state.hash`, `policy` / `disk/stream` (I/O only) |
```
Replace with a 7-row table using kernel.md's real phase order and each phase's actual owner/purpose
per `docs/engine/kernel.md`'s existing "Phase Domain Permissions" table (lines 144–158) and
`substrate_baseline_contract.md` §4 (lines 29–34) for the Responsibility column.

**Explicit translation rule (per Review finding — the original three recycled cells for
COLLECTION/CLEANUP/ADVANCEMENT were invented, copied from the fabricated GOVERNANCE/PACKETIZATION
rows' own Permissions cells, not actually sourced from kernel.md):** kernel.md's table has three
columns (Read domains / Write domains / Emit domains); architecture.md's table has one
("Permissions (READ / MUTATE)"). Translate by: READ cell = kernel.md's Read-domains column,
verbatim; MUTATE cell = kernel.md's Write-domains column, verbatim, plus Emit-domains appended with
a comma if the phase has any (RESOLUTION, ADVANCEMENT, and PERSISTENCE are the phases with
non-empty Emit domains per kernel.md's table; INIT, SCHEDULING, COLLECTION, and CLEANUP have empty
Emit domains — this only affects the explanatory rule text, not the output cells, since RESOLUTION
and PERSISTENCE are exempted from the translation rule below and keep their pre-existing wording;
only ADVANCEMENT's cell is actually affected, and it already correctly includes `events`). INIT, SCHEDULING, RESOLUTION, and PERSISTENCE keep their existing,
already-correct concrete-identifier wording (`state.world_time`, `tick_work`, etc. — these rows were
never fabricated, only COLLECTION/CLEANUP/ADVANCEMENT need new content since they're replacing
GOVERNANCE/PACKETIZATION):
```
| **1. INIT** | Increments simulation clock and resets per-tick buffers. | `state.world_time` / `state.world_time` |
| **2. SCHEDULING** | Identifies entities due to act and selects work based on the **Work Debt** budget. | `state.entities`, `policy` / `tick_work` |
| **3. COLLECTION** | Offloads AI deliberation tasks to the `WorkerManager` (bounded concurrent pool) using compact packets. | `entity, schedule` / `proposals` |
| **4. RESOLUTION** | **Authoritative Update**. Converts results into `StateUpdate` and applies it via `ApplyPath`, incrementing the state generation. | `worker_results` / `state.authoritative` |
| **5. CLEANUP** | Internal metrics and state finalization. | `platform, infra` / `infra` |
| **6. ADVANCEMENT** | Signal recording and tick seal (`RuntimeStatus`). | `entity, lifecycle` / `lifecycle, events` |
| **7. PERSISTENCE** | **External Phase, non-authoritative**. Streams `TraceEvent` records to the `ReplayManager`. | `state.hash`, `policy` / `disk/stream` (I/O only) |
```
COLLECTION/CLEANUP/ADVANCEMENT's Permissions cells now use kernel.md's own domain-name vocabulary
directly (`entity, schedule`, `platform, infra`, `entity, lifecycle` / `lifecycle, events`) rather
than invented concrete-identifier values — this is a deliberate, disclosed shift in that column's
naming style for exactly these three rows, not an oversight; INIT/SCHEDULING/RESOLUTION/PERSISTENCE
were never fabricated and keep their pre-existing wording unchanged. Do not further invent
Permissions-column values beyond what's written here — if kernel.md's table has since changed,
re-read it and use its current wording verbatim rather than this plan's snapshot.

For `docs/guides/simulation.md`, current text (read directly, confirmed):
- Lines 19–20: `Every simulation run is a deterministic 6-phase loop (Init → Governance → Scheduling → Packetization → Resolution → Persistence) repeated per tick.`
- Line 25: `` `src/engine/kernel.py` — the 6-phase loop``

Change lines 19–20 to: `Every simulation run is a deterministic 7-phase loop (Init → Scheduling →
Collection → Resolution → Cleanup → Advancement → Persistence) repeated per tick.` Change line 25 to:
`` `src/engine/kernel.py` — the 7-phase loop``. Leave the rest of the paragraph (the
"Given the same seed..." sentence and the "authoritative mutation pipeline" sentence) and line 26
(the 17-phase pipeline claim) untouched.
**Do NOT touch:** `docs/guides/simulation.md` line 26 (17-vs-37 pipeline count mismatch — separate,
pre-existing, out of scope per Design Decisions above); any other line in either file; `kernel.md`'s
own "Phase Domain Permissions" table (read-only reference for this step, not edited).
**Verify:** `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs`
(after Step 3's marker removal) and `tests/docs/test_kernel_phase_names_consistent.py::test_kernel_doc_states_all_seven_real_phases`
(guards that kernel.md itself, untouched, still names all 7 phases).

### Step 3 — Remove the `xfail` marker from the living test
**Files:** `tests/docs/test_kernel_phase_names_consistent.py`
**Change:** Delete the entire `@pytest.mark.xfail(strict=True, reason=(...))` decorator block (lines
27–35, confirmed by direct read) immediately above `def test_no_fabricated_phase_names_in_kernel_docs():`
(line 36). Leave the function body, its docstring, and `test_kernel_doc_states_all_seven_real_phases`
entirely unchanged. This step must run only after Steps 1 and 2 are complete — removing the marker
before the docs are fixed would turn a designed `strict-xfail` (XPASS-is-a-failure) guard into an
immediate ordinary `AssertionError`.
**Do NOT touch:** The `PHASE_NARRATING_DOCS` list, `FORBIDDEN_PHASE_NAME_GOVERNANCE`/
`FORBIDDEN_PHASE_NAME_PACKETIZATION` constants, `REAL_PHASES` tuple, or
`test_kernel_doc_states_all_seven_real_phases`.
**Verify:** `pytest tests/docs/test_kernel_phase_names_consistent.py -v` — both tests pass with no
`xfail`/`XPASS` marker present in output.

### Step 4 — Add a reconciling cross-reference note to `substrate_baseline_contract.md` §4
**Files:** `docs/engine/contracts/substrate_baseline_contract.md`
**Change:** §4 "Kernel Orchestration Law" (lines 26–37, confirmed by direct read) currently states
"The `Kernel` MUST execute the following 6 phases in strict sequential order" (line 27), lists INIT
through ADVANCEMENT (lines 29–34), then a separate "### Observational Boundary" subsection (lines
36–37) describing PERSISTENCE as non-authoritative. This wording is correct and code-verified
(`src/engine/phases.py::get_authoritative_phases()` per investigation.md lines 31–38) — do not alter
it. Insert one new sentence immediately after line 37 (end of the "Observational Boundary"
paragraph), before the `## 5. Authoritative Apply Law` heading, e.g.: "*Cross-reference: this 6-phase
authoritative count plus the PERSISTENCE hook together form the 7 phases named in
[`docs/engine/kernel.md`](../kernel.md) and [`docs/engine/architecture.md`](../architecture.md) — the
two framings are equivalent, not contradictory: this section enumerates only the
authoritative-mutation-eligible subset (`get_authoritative_phases()`), while the other docs enumerate
all 7 phases the `Kernel` executes per tick.*"
**Do NOT touch:** The "MUST execute the following 6 phases" sentence (line 27), the numbered list
(lines 29–34), the "Observational Boundary" heading or its existing sentence (lines 36–37), or any
other section of this file (§5 Authoritative Apply Law, §6 Deterministic Work-Order Law, etc.).
**Verify:** No automated test covers this file's prose (confirmed: no `PHASE_NARRATING_DOCS` entry
for this file). Verify manually by re-reading the edited section to confirm the "MUST execute the
following 6 phases" sentence and numbered list are byte-identical to before, and only the new sentence
was appended.

### Step 5 — Add a new parity ledger entry to `docs/parity_ledger/infrastructure.yaml`
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** The file's highest existing ID is `INFRA-366` (confirmed by direct grep in this session;
line 10747), which is the sibling `TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION` ticket's entry and
explicitly excludes this ticket's phase-count scope in its own `support_boundary` field (confirmed by
direct read, lines 10768–10772). Append a new entry with `id: INFRA-367` (next sequential ID,
`^[A-Z]+-[0-9]{3}$` pattern per `docs/parity_ledger/schema.json`, confirmed by direct read) at the end
of the file, following the same field shape as `INFRA-366`:
```yaml
- id: INFRA-367
  text: 'docs/engine/architecture.md §2 and docs/guides/simulation.md stated a fabricated 6-phase
    kernel loop (INIT, GOVERNANCE, SCHEDULING, PACKETIZATION, RESOLUTION, PERSISTENCE) with two
    phase names (GOVERNANCE, PACKETIZATION) that do not correspond to any real _phase_* method on
    Kernel, contradicting docs/engine/kernel.md and docs/engine/contracts/simulation_kernel_contract.md
    (both already correct at 7 phases: INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT,
    PERSISTENCE). Corrected architecture.md and docs/guides/simulation.md to the real 7-phase list and
    added a cross-reference note to substrate_baseline_contract.md §4 reconciling its 6-authoritative-
    phase framing (PERSISTENCE excluded as non-authoritative) with the 7-phase count used elsewhere.'
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: 'src/engine/kernel.py::Kernel._tick_once_inner (7 _phase_* calls in order: init line
    364, scheduling line 379, collection line 388, resolution line 397, cleanup line 403, advancement
    line 407, persistence line 426) + src/engine/phases.py::TickPhase (7-value IntEnum) and
    get_authoritative_phases() (6-item authoritative-only subset excluding PERSISTENCE)'
  proof_type: contract
  test_path: tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs,tests/integration/kernel/test_simulation_kernel_contract.py::test_authoritative_phase_list
  divergence_note: null
  support_boundary: 'Documentation-only correction (TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION) --
    no production code changed. Complements INFRA-366 (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION),
    which explicitly deferred this phase-count scope. Does not touch the 17-vs-37 mutation-pipeline-
    count mismatch (docs/guides/simulation.md line 26 vs docs/engine/README.md), a separate
    pre-existing issue.'
```
Verify line-count/ID uniqueness by re-grepping `^- id: INFRA-` after the edit to confirm `INFRA-367`
appears exactly once and no existing ID was disturbed.
**Do NOT touch:** `INFRA-366` or any other existing entry in this file.
**Verify:** `python3 tools/ledger_validator.py` equivalent / whatever schema-validation step Finalize
runs (per project convention) against `docs/parity_ledger/infrastructure.yaml` passes with the new
entry; manually confirm the new entry parses as valid YAML and matches `schema.json`'s required
fields (`id`, `text`, `status`, `priority`, plus `v2_evidence`+`test_path` required for `status:
verified`, both present here).

### Step 6 — Final repo-wide grep verification
**Files:** None edited; verification only.
**Change:** Run `grep -rn "GOVERNANCE" docs/engine/` and `grep -rni "packetization" docs/engine/` and
confirm the only remaining "Governance"-adjacent hits are: (a) `architecture.md`'s "### Phase
Governance" heading (line 61, title-case, legitimate, untouched by Steps 1–2), and (b) any reference
to `docs/engine/contracts/governance_logic.md` or `GovernorPolicy` elsewhere in `docs/engine/`
(legitimate, unrelated, confirmed by investigation.md's Anti-Drift Hazards). Confirm zero
`packetization` hits in any casing anywhere under `docs/engine/`. This satisfies the ticket's AC #3
literally ("grep for 'PACKETIZATION'/'GOVERNANCE' as phase names returns zero matches across
docs/engine/").
**Do NOT touch:** Nothing is edited in this step — it is a read-only confirmation gate before
closing the ticket.
**Verify:** The grep commands above return only the expected legitimate matches; combined with
`pytest tests/docs/test_kernel_phase_names_consistent.py tests/integration/kernel/test_simulation_kernel_contract.py tests/integration/kernel/test_milestone_a_closure.py -v`
(per test_plan.md's Scoped Pytest Commands) passing in full.

## Scope Guards
Do NOT touch, under any step of this plan:
- `tests/integration/kernel/test_milestone_a_closure.py` — its `test_final_kernel_law_compliance`
  6-mandated-phase assertion (no PERSISTENCE) is a legitimate, different convention
  (authoritative-only, matching `get_authoritative_phases()`), explicitly Out of Scope on the ticket.
  Do not edit its docstring or assertions.
- `docs/engine/contracts/substrate_baseline_contract.md` §4's "MUST execute the following 6 phases"
  sentence and its numbered INIT–ADVANCEMENT list (lines 27–34) — correct and code-verified; Step 4
  only appends a new sentence after the existing "Observational Boundary" paragraph, never rewrites
  §4's substance.
- `docs/engine/architecture.md`'s "### Phase Governance" section heading (line 61) and any
  "Governor"/"GovernorPolicy" reference elsewhere in the file — legitimate, unrelated uses of the word
  "Governance"; only the two table rows (GOVERNANCE, PACKETIZATION row content) and the heading/prose
  at lines 45/47 are in scope.
- `docs/guides/simulation.md` line 26 (`src/engine/pipeline.py — the 17-phase mutation sequence`) —
  the 17-vs-37 pipeline-count mismatch is a separate, pre-existing, out-of-scope contradiction; do not
  fix it under this ticket even though it sits one line below an in-scope edit.
- `docs/systems/ai_system.md` — already archived to `docs/archive/systems/ai_system.md`
  (confirmed in investigation.md), not a "phase-narrating living doc," correctly excluded from
  `PHASE_NARRATING_DOCS`, handled by a different already-closed ticket
  (`TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT`). Do not edit the archived copy.
- `docs/engine/README.md`, `docs/engine/kernel.md`, `docs/engine/contracts/simulation_kernel_contract.md`,
  `CLAUDE.md` — all re-confirmed clean by direct grep in this planning session (zero
  `GOVERNANCE`/`packetization`-any-casing hits). No edits needed or permitted under this plan.
- `src/engine/phases.py::TickPhase` enum and `get_authoritative_phases()`, and `src/engine/kernel.py`'s
  `_phase_*` methods / `_tick_once_inner` — this is a docs-only ticket; the enum is documented
  "FROZEN (Resource Phase 4 Milestone 1)" and must not be touched.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-366` entry — read-only reference for Step 5's
  field-shape precedent; do not modify it.

## Dependency Map
- Step 1 and Step 2 touch the same file (`architecture.md`) in adjacent regions (heading/prose vs.
  table) and can be done together as one edit pass, but are listed separately because they are
  independently verifiable text spans; Step 2 also touches `docs/guides/simulation.md` (independent
  file, no ordering constraint against Step 1).
- Step 3 (marker removal) **depends on** Steps 1 and 2 both being complete — removing the marker
  before the docs are fixed produces an immediate real test failure rather than a clean pass.
- Step 4 (substrate_baseline_contract.md note) is independent of Steps 1–3; can be done any time,
  including in parallel with Steps 1–2.
- Step 5 (parity ledger entry) should follow Steps 1–4 so its `text`/`v2_evidence` fields describe
  work that has actually landed, but has no functional/test dependency on them.
- Step 6 (final grep verification) **depends on** all of Steps 1–5 being complete — it is the closing
  gate, not an independent step.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| architecture.md §2 no longer contains GOVERNANCE or PACKETIZATION as phase names; phase list matches the 7 real `_phase_*` methods, same order | Step 1, Step 2 | `tests/docs/test_kernel_phase_names_consistent.py::test_no_fabricated_phase_names_in_kernel_docs` (post Step 3), Step 6 grep |
| README.md's Core Loop bullet no longer says 'Init, Governance, Scheduling, Packetization, Resolution, Persistence'; matches the 7-phase list | Already satisfied — no step needed (confirmed clean by direct read/grep in this session and in investigation.md) | `test_no_fabricated_phase_names_in_kernel_docs`, Step 6 grep |
| kernel.md + simulation_kernel_contract.md + corrected architecture.md/README.md all state the same 7 phases; grep for 'PACKETIZATION'/'GOVERNANCE' as phase names returns zero matches across docs/engine/ | Step 1, Step 2 (architecture.md); kernel.md/simulation_kernel_contract.md/README.md already clean | `test_no_fabricated_phase_names_in_kernel_docs`, Step 6 grep |
| substrate_baseline_contract.md §4 explicitly notes its 6-phase+hook framing is equivalent to (not contradicting) the 7-phase numbering elsewhere | Step 4 | Manual re-read verification (no automated test covers this file's prose) |

## Anti-Drift Notes
- The Permissions column in Step 2's new architecture.md table must be sourced from kernel.md's
  existing "Phase Domain Permissions" table (lines 144–158) and/or `substrate_baseline_contract.md`
  §4's phase descriptions (lines 29–34) — do not invent new permission semantics for COLLECTION,
  CLEANUP, or ADVANCEMENT that aren't already stated somewhere in the existing, code-verified docs.
- `_phase_advancement()` internally also invokes `_phase_observability()` as a sub-step (investigation.md
  lines 24–25) — this is not a separate top-level `tick_once` phase and must not be added as an 8th
  row to any table.
- This is the third recorded recurrence of the same fabricated GOVERNANCE/PACKETIZATION phrase
  (kernel.md in June 2026, then architecture.md/README.md/CLAUDE.md/docs/guides/simulation.md
  discovered in August 2026 — investigation.md Prior Work). The living test added in Step 3 is the
  structural fix meant to prevent a fourth recurrence; do not weaken its assertions (e.g. narrowing
  `PHASE_NARRATING_DOCS`, or making the `GOVERNANCE`/`packetization` checks case-insensitive-off or
  case-sensitive-only in a way that would miss a future Title-Case reintroduction) while implementing
  this plan.
- Verify the exact current text of every "current text" quote in this plan against the live files
  before editing — this plan was written against a specific read of each file in this planning
  session; if another concurrent session has since touched any of these files, re-read before editing
  rather than trusting this plan's quoted text verbatim.

## Deviations
- **Step 6 grep verification**: the plan's literal Step 6 instruction says to "confirm zero
  `packetization` hits in any casing anywhere under `docs/engine/`." Implementation found one
  pre-existing hit that the plan did not anticipate: `docs/engine/contracts/substrate_baseline_contract.md`
  line 31, `3. **COLLECTION**: \`WorkerManager\` - Work packetization and execution (Local/Concurrent).`
  This line predates this ticket (confirmed unchanged by this ticket's Step 4 edit, which only appended
  a sentence after the "Observational Boundary" paragraph, well below line 31) and uses "packetization"
  as an ordinary English noun describing what the COLLECTION phase does (turning work into packets),
  not as a fabricated phase name — `substrate_baseline_contract.md` is not in `PHASE_NARRATING_DOCS`
  and this line does not affect `test_no_fabricated_phase_names_in_kernel_docs`, which passes cleanly.
  This is treated the same as the plan's own carved-out exception for architecture.md's "### Phase
  Governance" heading (a legitimate, non-fabricated use of the word) — not a new occurrence of the
  documented drift pattern, so no additional edit was made. Recorded here rather than silently treating
  the "zero hits anywhere" instruction as satisfied.
