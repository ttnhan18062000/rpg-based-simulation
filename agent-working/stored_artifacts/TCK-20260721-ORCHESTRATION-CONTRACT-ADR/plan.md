---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-ADR
artifact_type: plan
tags: [ai, workflows, process-improvement]
---

# Implementation Plan — TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Summary

This ticket produces exactly one new decision-record document —
`docs/architecture/agent_orchestration_contract.md` — plus the two mechanical
follow-through steps every new `docs/` file requires (registry regeneration,
link-back from the source plan). The ADR follows the two live precedent docs'
shape (frontmatter + unnumbered descriptive-slug filename + Status → Context →
Decision → Rationale → Trade-offs → Consequences → Revisit Trigger), not the
unused numbered `ADR-[XXX]` skill template. Its `## Decision` section is
subdivided into 5 explicitly labeled `###` sub-decisions (Contract
Representation/Format, Source Ownership, Versioning, Provider-Adapter
Boundary, Conformance Mechanism), each closed with a one-line evidence-weight
tag (`Status: Decided` / `Consumed-as-input` / `Proposed-pending-
implementation-evidence`) reflecting how well-specified each decision is in
the source evidence. Execution identity is handled as a separate,
explicitly-labeled "consumed input" subsection — never re-derived — citing
`docs/ai/monitoring_writer_decision.md` §2's exact `execution_id` format
verbatim. This is a pure documentation deliverable: no `src/`,
`tools/agent-monitoring/`, `.claude/`, or `.codex/` files change, and no
`agent-orchestration/` directory or contract file is created.

## Steps

### Step 1 — Author the ADR document
**Files:** `docs/architecture/agent_orchestration_contract.md` (new file)

**Change:**

Create the file with this exact structure:

1. **Frontmatter** (matches the two live precedent docs' shape plus this
   repo's now-mandatory tags):
   ```yaml
   ---
   status: active
   layer: ai
   authority: P1
   audience: developer
   tags: [ai, workflows, process-improvement]
   ---
   ```
   Use `layer: ai` — it is already registered (confirmed by the ticket's own
   AC line 45, "using an already-registered layer (e.g. ai)") and matches the
   three evidence-input docs (`docs/ai/agents_dir_disposition.md`,
   `docs/ai/codex_capability_matrix.md`, `docs/ai/monitoring_writer_decision.md`)
   this ADR synthesizes, even though the doc physically lives under
   `docs/architecture/` alongside `layer: architecture` precedents — the AC
   explicitly sanctions this. Use `authority: P1` and `audience: developer`
   to match both live ADR precedents (`simulation_watchdog.md`,
   `performance_optimization.md`) and the three evidence docs. Do **not**
   add `artifact_type:` — the precedent ADR docs do not use that field (it is
   a staging-artifact-only convention).

2. **Title** — `# Agent Orchestration Contract` (unnumbered, descriptive
   slug, no `ADR-XXX` prefix — matches both live precedents).

3. **`## Status`** — single bare word: `Proposed` (matches
   `simulation_watchdog.md`'s bare-word convention; this is a discovery-phase
   decision record, not yet an implemented runtime change, so `Proposed` is
   correct, not `Accepted`).

4. **`## Context`** — must state, in prose:
   - This is discovery output within the parent epic
     `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`. Before writing the epic-position
     sentence, read `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`
     lines 129-140 (`## Proposed Architecture` → "Approval model and exit
     gate") directly and cite **that list's own numbering/order** for where
     this ADR sits among the 5 discovery outputs. Do **not** reuse the
     `..._ticket_handoff_codex.md` sequencing table's numbering (it lists
     this ticket as item 4) — the investigation found the two documents
     order the outputs differently, and the source plan's own list is
     canonical for this citation.
   - Explicitly names and cites all three required evidence-input tickets:
     `TCK-20260721-AGENTS-DIR-DISPOSITION`, `TCK-20260721-CODEX-CAPABILITY-MATRIX`,
     `TCK-20260721-MONITORING-WRITER-DECISION` (and their doc paths
     `docs/ai/agents_dir_disposition.md`, `docs/ai/codex_capability_matrix.md`,
     `docs/ai/monitoring_writer_decision.md`).
   - One explicit sentence: "This ADR makes no final storage location or
     writer-implementation choice; it records design decisions only, and
     creates no `agent-orchestration/` directory, contract file, or runtime
     code."
   - States the filename/convention choice for this and future ADRs:
     descriptive-slug + frontmatter + unnumbered title (the two live
     precedent docs' shape), explicitly rejecting the numbered `ADR-[XXX]` /
     `adr-NNN-*.md` template in `.claude/skills/architecture/trade-off-analysis.md`
     because it is followed by zero real docs in the repo (0 of 9
     `docs/architecture/` files as of this investigation), while the
     frontmatter + Status/Context/Decision/Rationale/Trade-offs/Consequences/
     Revisit-Trigger shape is followed by both real ADR-shaped docs. State
     this as a **named decision with rationale**, not a silent default.

5. **`## Decision`** — exactly 5 `###` subsections, each ending with a
   bolded one-line `**Status:** ...` tag:

   - **`### Contract Representation and Format`** — Decide: YAML for
     human-reviewable definitions, with generated Python validation models
     (per `idea_provider_agnostic_agent_orchestration.md:428-430`'s "initial
     recommendation"). State this ADR converts that recommendation into an
     actual decision. `**Status:** Decided`

   - **`### Source Ownership`** — Decide: a new repo-root
     `agent-orchestration/` directory, functioning as a source specification
     (not a second implementation), per the source plan's proposed layout
     (`README.md`, `contract.yaml`, `agents/<role>.yaml`,
     `workflows/<workflow>.yaml`, `skills.yaml`, `monitoring-schema.yaml`,
     `hook-events.yaml`, `intentional-divergences.md`,
     `idea_..._orchestration.md:158-178`). Explicitly flag this as decided
     but subject to revisit if a future provider-runtime implementation
     ticket surfaces contradicting evidence — name the specific revisit
     condition in `## Revisit Trigger` (Step 1, item 8 below), not just in
     this subsection. Do **not** create this directory as part of this
     ticket. `**Status:** Decided`

   - **`### Versioning`** — Decide: a `version` field on `contract.yaml`,
     named consistently with the already-established `workflow_version` /
     `hook_schema_version` field-naming pattern in
     `docs/ai/monitoring_writer_decision.md` and the source plan's
     monitoring-schema table (`idea_..._orchestration.md:239-246`). State
     explicitly that no versioning *scheme* (semver vs. simple integer
     generation number) is fixed here — that is the thinnest-evidenced of
     the 5 decisions, with no direct source-plan recommendation beyond the
     field's existence. `**Status:** Proposed-pending-implementation-evidence`

   - **`### Provider-Adapter Boundary`** — Decide: `.claude/` and `.codex/`
     each translate the shared contract into provider-native configuration;
     adapters "may not silently redefine workflow phases, terminal statuses,
     gate policy, or artifact requirements" (quote/cite
     `idea_..._orchestration.md:180-202` directly — this is the
     best-specified of the 5 decisions). `**Status:** Decided`

   - **`### Conformance Mechanism`** — Decide: contract conformance tests
     must exist for both provider adapters (per source plan Workstream F,
     item 1), verifying each adapter's translated config does not diverge
     from the shared contract's phases/statuses/gate policy/artifact
     requirements. State explicitly this is the least-constrained of the 5
     decisions — the source plan gives no further detail on test shape,
     location, or invocation, and this ADR does not invent one beyond the
     stated principle. `**Status:** Proposed-pending-implementation-evidence`

6. **`### Execution Identity (Consumed Input)`** — a sixth, clearly
   separate subsection under `## Decision`, explicitly labeled as *not* one
   of the 5 decisions this ADR makes. State verbatim, citing
   `docs/ai/monitoring_writer_decision.md:91-142` (§2):
   - `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"`
     is the immutable execution key.
   - `run_id` is retained as a human-readable display field.
   - `ticket_id` is promoted to an explicit top-level join-key field.
   - One sentence: "The shared contract's monitoring schema carries these
     three fields as already-decided inputs; this ADR does not choose their
     format or ownership independently." `**Status:** Consumed-as-input`

7. **`## Rationale`** — one paragraph per decision (or grouped), explaining
   *why* each choice follows from the cited evidence — not a restatement of
   the Decision section, actual reasoning (e.g., why YAML+generated-Python
   over hand-written Python, why a source-spec directory over embedding the
   contract inside `.claude/`).

8. **`## Trade-offs`** — at minimum: YAML-first means schema drift is only
   caught at generation/validation time, not authoring time; a repo-root
   `agent-orchestration/` directory adds one more top-level path to
   `docs/architecture/world_repository_layout.md`-style discoverability
   concerns (note only — do not edit that doc); thin evidence on Versioning
   and Conformance Mechanism means those two decisions carry more
   implementation risk than the other three.

9. **`## Consequences`** — what becomes possible/required once this ADR
   lands: future provider-runtime tickets should scaffold against this
   contract shape; conformance tests become a gating requirement once
   adapters exist; no immediate code changes required by this ADR itself.

10. **`## Revisit Trigger`** — explicit conditions, matching both live
    precedents' closing-section convention:
    - Source Ownership (`agent-orchestration/` location) is revisited if a
      future provider-runtime implementation ticket's evidence contradicts
      the proposed layout.
    - Versioning scheme is revisited once a concrete `contract.yaml` schema
      is drafted and a semver-vs-integer choice becomes load-bearing.
    - Conformance Mechanism is revisited once the first provider adapter
      conformance test is actually written.

**Do NOT touch:** any file under `.claude/workflows/`, `.claude/settings.json`,
`.codex/`, `tools/agent-monitoring/*.py` (beyond the standard run/event
monitoring entries every workflow phase writes), any live ticket artifact
outside this ticket's own `tickets/`/`staging_artifacts/` paths, the shared
monitoring JSONL corpus, `docs/ai/monitoring_writer_decision.md` itself (read
and cite only — do not edit), and any `docs/architecture/*.md` file other than
the one new file. Do not create `agent-orchestration/` or any file under it.
Do not create or reference a provider-runtime implementation ticket ID.

**Verify:** `python3 tools/validate_frontmatter.py docs/architecture/agent_orchestration_contract.md` exits 0 (deferred to Step 2, run after this step). Manual review confirms: 5 separately labeled `###` decision subheadings each with a `**Status:**` tag exist; the execution-identity subsection is separately labeled and matches `monitoring_writer_decision.md`'s exact `execution_id` format string with no altered field name/shape; all 3 evidence ticket IDs appear in the body; a sentence states no final location/writer choice is made; the chosen filename/convention is stated with rationale (per test_plan.md's manual-review mapping table).

---

### Step 2 — Validate frontmatter
**Files:** none changed; verification only against `docs/architecture/agent_orchestration_contract.md`

**Change:** Run `python3 tools/validate_frontmatter.py docs/architecture/agent_orchestration_contract.md` and confirm exit code 0. If it fails, fix the frontmatter block in Step 1's file (most likely cause: a `status`/`layer`/`authority`/`audience` value not in the registered enum — re-check `python3 tools/layer_registry.py list` and `python3 tools/tag_registry.py list` before altering values).

**Do NOT touch:** any other file. Do not "fix" a validation failure by adding an `artifact_type` field or otherwise diverging from the precedent docs' frontmatter shape — re-check the enum values instead.

**Verify:** `tests/tools/test_validate_frontmatter.py` still passes unmodified (confirms the enum constants this file's frontmatter must satisfy have not drifted); manual run of the validator against the new file exits 0.

---

### Step 3 — Regenerate the docs registry
**Files:** `docs/REGISTRY.yaml` (regenerated, not hand-edited)

**Change:** Run `make knowledge-index-update` (or `make docs-registry` to preview first). Confirm the new file's `path: docs/architecture/agent_orchestration_contract.md` entry appears in the regenerated `docs/REGISTRY.yaml` with `type: doc`, the correct `layer: ai`, and the tags list.

**Do NOT touch:** any other `docs/REGISTRY.yaml` entry by hand. This file is machine-generated — do not hand-edit it; if an entry looks wrong, fix the source frontmatter (Step 1/2) and regenerate again.

**Verify:** `tests/tools/test_generate_registry.py`, `tests/tools/test_registry_query.py`, and `tests/integration/content/test_registry_projection_parity.py` all pass; grep confirms `docs/architecture/agent_orchestration_contract.md` appears in `docs/REGISTRY.yaml`.

---

### Step 4 — Link the ADR from the source plan's Related Material section
**Files:** `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`

**Change:** Add exactly one new entry to the `## Related Material` section (currently 11 entries, lines 447-459) pointing at `docs/architecture/agent_orchestration_contract.md`, in the same list-item style as the existing 11 entries (relative path + short description, matching whatever format the existing entries use — read the section first to match style exactly).

**Do NOT touch:** any other section of this plan doc (`## Proposed Architecture`, `## Open Decisions`, the discovery-epic exit-gate list, etc.) — this step is a single additive line in one section only. Do not renumber or reorder the existing 11 entries.

**Verify:** `grep -n "docs/architecture/agent_orchestration_contract.md" docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` returns the new line (per test_plan.md's link-omission guard).

---

### Step 5 — Containment and regression check
**Files:** none changed; verification only

**Change:** Run the two scoped pytest commands from `test_plan.md`:
```bash
.venv/bin/python -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v
.venv/bin/python -m pytest tests/integration/content/test_registry_projection_parity.py -v
```
Then run `git diff --stat` (or `git status`) and confirm the changed-file set is limited to: `docs/architecture/agent_orchestration_contract.md` (new), `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` (one link line), `docs/REGISTRY.yaml` (regenerated), `tickets/inprogress/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md` → later `tickets/done/`, `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/` → later `stored_artifacts/`, `tickets/working_log.csv`, and `agent-monitoring/` (run/event entries). Any diff touching `.claude/workflows/`, `.claude/settings.json`, `tools/agent-monitoring/*.py` beyond standard monitoring entries, or `.codex/` blocks Finalize.

**Do NOT touch:** anything outside the file list above. Never run `pytest tests/` (full suite) for this ticket.

**Verify:** both scoped pytest commands pass; `git diff --stat` shows only the expected file set.

## Scope Guards

- Do not create `agent-orchestration/` or any file under it (source ownership is a named decision, not an implementation, in this ticket).
- Do not create, reference, or imply a provider-runtime implementation ticket ID — Out of Scope explicitly blocks this until all 5 discovery outputs are approved.
- Do not modify production Claude/Codex workflows, hooks, monitoring writers, live ticket artifacts, or the shared monitoring JSONL corpus.
- Do not edit `tools/agent-monitoring/*.py` beyond the standard run/event entries every workflow phase writes automatically.
- Do not edit `docs/ai/agents_dir_disposition.md`, `docs/ai/codex_capability_matrix.md`, or `docs/ai/monitoring_writer_decision.md` — cite them, do not change them.
- Do not choose a different `execution_id` format, field name, or ownership than `docs/ai/monitoring_writer_decision.md` §2 already specifies — this is the sharpest scope-creep risk per the investigation's Anti-Drift Hazards.
- Do not use the numbered `ADR-[XXX]` / `adr-NNN-*.md` filename convention from `.claude/skills/architecture/trade-off-analysis.md` — explicitly rejected in favor of the two live precedents' shape.
- Do not hand-edit `docs/REGISTRY.yaml` — regenerate only.
- Do not touch any `docs/architecture/*.md` file other than the one new file.
- Do not edit any section of `idea_provider_agnostic_agent_orchestration.md` other than the single new `## Related Material` line.

## Dependency Map

- Step 1 (author ADR) has no dependencies — it is the root artifact all other steps act on.
- Step 2 (validate frontmatter) depends on Step 1 (file must exist).
- Step 3 (regenerate registry) depends on Step 1 and should run after Step 2 passes (registry generation may surface the same frontmatter issues; fixing frontmatter first avoids a wasted regeneration cycle).
- Step 4 (link from plan doc) depends on Step 1 only (needs the final chosen filename) — independent of Steps 2 and 3, can run in parallel with them.
- Step 5 (containment + regression check) depends on Steps 1-4 all being complete — it is the final gate.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| New ADR doc lands at `docs/architecture/<name>.md` with valid frontmatter (status/layer/authority/audience) passing `tools/validate_frontmatter.py`, using an already-registered layer (e.g. ai) | Step 1, Step 2 | `python3 tools/validate_frontmatter.py docs/architecture/agent_orchestration_contract.md` exit 0; `tests/tools/test_validate_frontmatter.py` |
| ADR body contains explicit, separately labeled decisions for: contract representation/format, source ownership, versioning, provider-adapter boundary, and conformance mechanism | Step 1 | Manual review: 5 `###` subheadings with `**Status:**` tags present under `## Decision` |
| ADR treats execution identity as a required, already-decided input consumed from `TCK-20260721-MONITORING-WRITER-DECISION`; no independent format/ownership choice; Scope/Out-of-Scope/AC boundary consistency preserved in the ADR body itself | Step 1 | Manual line-by-line diff of the ADR's Execution Identity subsection against `docs/ai/monitoring_writer_decision.md:91-142` |
| ADR explicitly states it makes no final location or writer-implementation choice and cites the 3 evidence-input tickets | Step 1 | Manual review: grep for `TCK-20260721-AGENTS-DIR-DISPOSITION`, `TCK-20260721-CODEX-CAPABILITY-MATRIX`, `TCK-20260721-MONITORING-WRITER-DECISION` in the ADR body; grep for the "no final location or writer-implementation choice" sentence |
| This ticket's own process picks and documents ONE explicit ADR filename/numbering convention, stating which was chosen and why | Step 1 | Manual review of the `## Context` section's stated rationale (descriptive-slug + frontmatter shape vs. rejected numbered `ADR-[XXX]` template) |
| ADR is registered via `docs/REGISTRY.yaml` regeneration (`make knowledge-index-update`) and linked from the 'Related Material' section of the main plan doc | Step 3, Step 4 | `tests/tools/test_generate_registry.py`, `tests/tools/test_registry_query.py`, `tests/integration/content/test_registry_projection_parity.py`; grep confirms both the registry entry and the Related Material link |

## Anti-Drift Notes

- **Execution identity is the single sharpest regression risk.** The ticket's Request Summary explicitly documents a prior Codex-review correction where an earlier draft contradictorily claimed to both decide and not decide execution identity. Step 1 must reproduce `monitoring_writer_decision.md` §2's exact format string (`execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"`), not paraphrase or "improve" it.
- **Discovery-output numbering ambiguity.** The source plan's own 5-output list (`idea_..._orchestration.md:129-140`) and the handoff doc's sequencing table order this ADR differently. Step 1 must read the source plan's list directly and cite its numbering — do not carry over the handoff doc's "item 4" framing into the ADR body without checking.
- **Source Ownership is "decided but revisit-flagged," not left open.** Per the investigation's synthesis, naming `agent-orchestration/` as the decided location while stating an explicit revisit trigger is itself a complete decision, not a deferral — do not soften this into "TBD" or omit the Revisit Trigger content.
- **Versioning and Conformance Mechanism are the two thinnest-evidenced decisions.** Both get `Proposed-pending-implementation-evidence` status tags rather than `Decided` — this is intentional per the investigation's evidence-weight synthesis, not an omission to fix.
- **No test file is required or expected for this ticket** — `test_plan.md` confirms the AC's prose-structure requirements have no automated-test surface; only the existing frontmatter/registry tooling tests are the regression guard. Do not invent a new pytest file for "5 labeled decisions" — the investigation and test plan both explicitly recommend against over-engineering a heading-presence test for a single doc.
- **Containment is the other major risk for a doc-only ticket:** it is easy to accidentally touch `.claude/`, `.codex/`, or `tools/agent-monitoring/*.py` while exploring evidence docs. Step 5's `git diff --stat` check is the final backstop — treat any unexpected file in that diff as a blocking finding, not a minor cleanup item.

## Deviations

- **Step 3 mechanics:** `make knowledge-index-update` only rebuilds the semantic search
  index (`tools/knowledge_search.py build --incremental`) — it does not touch
  `docs/REGISTRY.yaml` at all. The actual registry regeneration is `make docs-registry`
  (→ `python3 tools/generate_registry.py`), which the plan's Step 3 text mentions only as
  a "preview" option. Implementation ran both: `python3 tools/generate_registry.py` to
  regenerate `docs/REGISTRY.yaml` (verified the new entry lands with `layer: ai` and the 3
  tags) and `make knowledge-index-update` to keep the search index current per the
  standard "docs changed" closing rule. No behavior change from the plan's intent — the
  plan's own parenthetical already anticipated `docs-registry` might be needed.
- **Step 4 style match:** the plan's Step 4 description paraphrased the existing
  `## Related Material` entries as "relative path + short description." The actual section
  (`idea_provider_agnostic_agent_orchestration.md:449-459`) uses bare backtick-wrapped
  paths with no descriptions at all (e.g. `` - `CLAUDE.md` ``). The added line matches the
  real style (`` - `docs/architecture/agent_orchestration_contract.md` ``), not the plan's
  paraphrase, per the plan's own instruction to "match style exactly" from reading the
  section first.
