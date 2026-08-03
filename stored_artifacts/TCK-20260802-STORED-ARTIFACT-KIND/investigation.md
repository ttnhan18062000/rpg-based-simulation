---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-STORED-ARTIFACT-KIND
artifact_type: investigation
tags: [ai, documentation, registry, frontmatter]
---

# Investigation — TCK-20260802-STORED-ARTIFACT-KIND

## Current Behavior

**`docs/REGISTRY.yaml` never indexes `stored_artifacts/*.md` as its own entity.** Confirmed by
reading `tools/generate_registry.py` in full:

- `collect_docs()` (`tools/generate_registry.py:186-238`) walks `root / "docs"` only
  (`docs_dir = root / "docs"`, line 192; `docs_dir.rglob("*.md")`, line 199). `stored_artifacts/`
  and `staging_artifacts/` sit at repo root, siblings of `docs/`, not under it — neither directory
  is reachable by this walk at all, regardless of `_SKIP_DOC_SUBDIRS` (line 42, which only
  filters `docs/`-relative subdirectory names: `{"archive", "parity_ledger", "scenarios",
  "entity"}`).
- `collect_tickets()` (`tools/generate_registry.py:246-311`) walks `tickets/done/*.md` (flat, line
  258) and for each ticket calls `join_artifact_files(root, ticket_id)` (line 295).
  `join_artifact_files()` (`tools/generate_registry.py:105-112`) does `root / "stored_artifacts" /
  ticket_id`, globs `*.md` non-recursively, and returns a **flat sorted list of path strings** —
  no frontmatter is read from those files, no `status`/`authority`/`artifact_type` value from any
  artifact file is copied anywhere into the registry entry. The ticket entry's own `artifact_files`
  field (line 306) is that list of strings, nothing more.
- Confirmed via `grep -rn "staging_artifacts" tools/generate_registry.py` → zero matches. The
  string `staging_artifacts` does not appear anywhere in this file — not scanned, not skipped, not
  referenced in a comment. Its total absence from `docs/REGISTRY.yaml`'s generation is structural
  (the walk never reaches repo-root-level `staging_artifacts/`), not an explicit exclusion list
  entry like `_SKIP_DOC_SUBDIRS`.

**`tools/validate_frontmatter.py`'s content-type detection treats the two artifact directories
asymmetrically.** `detect_content_type()` (lines 116-130): checks `"tickets" in parts` → `ticket`,
then `"stored_artifacts" in parts` → `artifact`, then falls through `docs/` handling, and
**defaults to `"doc"` for everything else** (line 130) — `staging_artifacts` is never named in
this function at all, so a `staging_artifacts/*.md` file silently content-type-detects as `doc`
unless a caller passes an explicit override. `tools/gate_checks/done_checker_static.py:279-282`
already documents this asymmetry in its own comment: *"staging_artifacts/ paths do not auto-detect
as `artifact` content type (only stored_artifacts/ does) — must pass content_type_override
explicitly or this silently falls through to `doc`'s looser required-field set."* — confirming
this is known, existing behavior this ticket did not discover fresh.

`_validate_artifact()` (`tools/validate_frontmatter.py:214-225`) requires exactly six fields for
content-type `artifact`: `status`, `layer`, `authority`, `audience`, `ticket_id`, `artifact_type`.
`ARTIFACT_TYPE_VALUES = {"investigation", "plan", "test_plan"}` (line 57). There is **no
`last_verified` field anywhere in `_validate_artifact`** — that field only appears in
`_validate_doc` (line 193-196), conditionally required when `status == "authoritative"`. Confirmed
directly against real files, not just the schema definition:

| File | status | layer | authority | audience | artifact_type |
|---|---|---|---|---|---|
| `stored_artifacts/TCK-20260728-CONTEXT-PACKET-SCHEMA/investigation.md` | historical | ai | P2 | agent | investigation |
| `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/plan.md` | historical | ai | P2 | agent | plan |
| `stored_artifacts/TCK-20260610-CATALOG-SCENARIO-BUILDER/investigation.md` | historical | misc | P2 | agent | investigation |
| `stored_artifacts/TCK-20260802-CONTEXT-KIND-PRIORITY/investigation.md` | historical | ai | P2 | agent | investigation |

No `last_verified` key present in any of the four. This matches the ticket's own stated premise
exactly.

**The real corpus is more heterogeneous than the ticket's own scoping example implies — this
matters for the decision.** Corpus-wide scan of `stored_artifacts/*/*.md` (2,941 files, 875
directories):

- `authority:` values: `P0` (4), `P1` (258), `P2` (1698), plus a handful of unrendered template
  placeholders (`{authority}`). Real variance exists — it is not a fixed constant.
- `status:` values: `historical` (1733), `active` (265), `authoritative` (5), `archive` (1),
  `verified` (5), plus assorted one-off non-canonical strings (`draft`, `complete`, `ready`, and
  several unrendered template/placeholder artifacts from malformed docs). The bulk cleanly matches
  `STATUS_VALUES`; a small tail does not.
  Real variance exists — it is not a fixed constant.
- `artifact_type:` values: `investigation` (639), `plan` (620), `test_plan` (582) — the canonical
  triplet this ticket scopes to — but also `index` (412) and `notice` (1), **neither of which is
  in `ARTIFACT_TYPE_VALUES`**. The `index` files (e.g.
  `stored_artifacts/9b6a9dff-f4cd-4620-8356-52f0a34dafbc/index.md`) are auto-generated landing
  pages with a **structurally different frontmatter shape** — `title`/`description`/
  `artifact_type: index`/`layer`/`tags` only, no `status`/`authority`/`audience`/`ticket_id` at
  all. Traced to `make docs-artifacts` → `python3 tools/generate_artifact_pages.py` (Makefile line
  246-247), a deliberate, separate tool feeding the Docusaurus website build
  (`docs-serve`/`docs-build` depend on `docs-artifacts`), unrelated to `generate_registry.py`. This
  is intentional tooling, not corruption — but it means "`stored_artifacts/*.md` frontmatter" is
  not one uniform shape across the whole directory tree; only the `investigation.md`/`plan.md`/
  `test_plan.md` triplet the ticket scopes to matches the clean 6-field `artifact` schema.
- Directory naming: 855 of 875 directories (~97.7%) match `TCK-YYYYMMDD-*`; 20 do not (UUID-named
  directories, `epic_17`/`epic-17-multi-hero`/`epic-17-phase-2`, `PHASE4_RECONSTRUCTION`,
  `D145C3D0-MILESTONE-*`, a bare `README.md`, `TCK-20260328` without a scope suffix, etc.) — a
  legacy pre-ticket-ID-convention tail. Consistent with the existing project memory note that
  legacy/old-format data should not be a target for new-check compliance, only a source future
  scanners must not crash on.
- Within `TCK-*` directories, filenames beyond the canonical triplet also occur: `walkthrough.md`
  (46), `task.md` (22), `implementation_plan.md` (14), `parity.md` (5), `security_review.md` (3),
  and dozens of further one-off names. `join_artifact_files()`'s non-recursive `*.md` glob (line
  111) already picks these up into the existing flat `artifact_files` list today — this is
  pre-existing behavior, unchanged by this ticket, but relevant context for any future
  `stored_artifact`-kind scanner's filtering logic.

**`staging_artifacts/` is currently WIP-only in practice, empirically.** As of this investigation,
exactly two `staging_artifacts/{ticket_id}/` directories exist on disk
(`TCK-20260730-CODEX-CONTROLLED-PILOT`, `TCK-20260802-STORED-ARTIFACT-KIND` — this ticket's own),
and both correspond 1:1 to a `tickets/inprogress/{ticket_id}.md` file. None correspond to a
`tickets/done/` ticket — the project workflow (CLAUDE.md "After Work": *"Move staging artifacts to
`stored_artifacts/`"*) treats the migration as a move, not a copy, so a `staging_artifacts/`
directory's lifetime is bounded to exactly the ticket's open window.

## Mechanics / Engine Constraints

Not applicable. This ticket touches `docs/engine/contracts/context_packet_contract.md`, an
agent-orchestration/retrieval-tooling contract, not a simulation-mechanics document. No
`docs/mechanics/*` chapter or `src/` simulation code is read, cited, or constrained by this work
— consistent with the contract's own §4 Verification Path, which states this contract "governs
agent-orchestration/retrieval tooling, not simulation logic."

## Docs Requiring Update

- `docs/engine/contracts/context_packet_contract.md`: append a new `## 6. Open Decision 8
  Resolution` section after the existing `## 5. Open Decision 7 Resolution` (added by sibling
  ticket `TCK-20260802-CONTEXT-KIND-PRIORITY`), resolving whether `stored_artifacts/*.md` becomes
  a registry-indexed `kind` and confirming `staging_artifacts/`'s exclusion is intentional. §1-§5
  are not edited.

No other `docs/` path requires a change. `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`'s Open Decision 8 entry (lines 341-350) is
the question being answered, not a document this ticket edits — the epic ticket
(`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`, a ticket file, not a
`docs/` path) is the tracking location the sibling ticket updated for Decision 7's RESOLVED
status; the Plan phase should decide whether to mirror that same update for Decision 8's entry,
but that file is outside this section's `docs/` scope by definition.

## Parity Ledger Overlap

None. No `docs/parity_ledger/*.yaml` entry exists or is needed for this work, matching the
established precedent already recorded in `context_packet_contract.md` §4: *"That future ticket
will not need a `docs/parity_ledger/` entry: this contract governs agent-orchestration/retrieval
tooling, not simulation logic, the same posture already recorded for agent-monitoring tooling
under `docs/parity_ledger/infrastructure.yaml`'s INFRA-281 through INFRA-292 entries
(`support_boundary` field)."* Confirmed directly: `docs/parity_ledger/infrastructure.yaml`'s
INFRA-281 through INFRA-292 entries are tagged `proof_type: feature` covering agent-monitoring
dashboard/orchestration tooling (not simulation mechanics), the same support-boundary category
this ticket's subject matter falls into. No `P0` entries are implicated.

## Prior Work

- `tickets/done/TCK-20260802-CONTEXT-KIND-PRIORITY.md` (sibling, same batch) — the structural
  precedent for *how* to add a new numbered section: appended `## 5. Open Decision 7 Resolution`
  immediately after `## 4. Verification Path`, opened with a verbatim quote of the open-decision
  question (matching §3's own quote-only convention), left §1-§4 byte-for-byte untouched (verified
  by a dedicated static test file), and closed with an explicit "human sign-off required" statement
  for the one residual genuine value judgment rather than inventing an answer. §6 of this ticket's
  work should follow the identical shape: append after §5, quote Open Decision 8 verbatim, leave
  §1-§5 untouched.
- `stored_artifacts/TCK-20260728-CONTEXT-PACKET-SCHEMA/investigation.md` and
  `docs/engine/contracts/context_packet_contract.md` §3 — the original Decision 3 resolution this
  ticket must follow the pattern of (three branches: REGISTRY-backed direct mapping, `unrated`
  sentinel for non-registry-backed kinds, differently-shaped-primitive mapping for
  `parity_ledger_entry`).
- `docs/ai/default_packet_scenarios_decision.md` and `docs/ai/code_test_index_boundaries_decision.md`
  — shape/rigor precedent for a "decides and evidences, implements nothing" decision document
  (explicit non-implementation framing in their opening paragraphs, verified-fact sections with
  real citations, no code changes).
- `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/plan.md` — precedent for a decision-record
  ticket that resolves multiple open architecture questions (ownership, discovery/IDs, schema
  shape) without shipping an index or scanner, directly analogous to what this ticket must do for
  `stored_artifacts` retrieval treatment.

## Risks and Open Questions

- **Which of Decision 3's three branches applies is a genuine judgment call, not pre-resolved by
  this investigation** (per the ticket's own Assumptions/Open Questions). See the Plan-phase
  framing in the closing summary below; investigation surfaces evidence but does not adjudicate.
- **The real `stored_artifacts/` corpus is not uniform** (see Current Behavior above: `index`/
  `notice` artifact_types, non-`TCK-*` legacy directories, dozens of non-canonical filenames). Any
  future `stored_artifact`-kind scanner (explicitly out of scope for *this* ticket) would need to
  either filter to the canonical triplet or define separate handling for `index`-type files — this
  ticket's decision doc should flag that filtering complexity exists without attempting to resolve
  it, since Scope explicitly excludes "implementation of a stored_artifact kind scanner."
- **The epic ticket's Open Decision 8 tracking entry update is ambiguous scope.** The sibling
  ticket updated `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Decision 7
  entry from UNRESOLVED to RESOLVED as part of its Implementation Notes. This ticket's own Scope
  section does not explicitly list that file under Related Code Areas, though Related Tickets
  names the epic. The Plan phase should decide explicitly whether to mirror that update (Files
  Changed would then include a `tickets/` path, not only `docs/`) — flagging this rather than
  silently assuming either way.
- **`content_type_override` asymmetry between `stored_artifacts/` and `staging_artifacts/` is
  pre-existing, documented behavior**, not a bug this ticket should fix (out of scope: no code
  changes to `tools/validate_frontmatter.py`). It is, however, directly relevant evidence for the
  staging-exclusion-is-intentional argument (see decision doc §6).

## Anti-Drift Hazards

- Do not edit `docs/engine/contracts/context_packet_contract.md` §1-§5 in place — append §6 only,
  exactly mirroring the sibling ticket's additive pattern (verified via the existing
  `tests/tools/test_context_kind_priority_decision.py`'s own byte-preservation test style, which
  the new test file for this ticket should follow for §1-§5 this time).
- Do not touch `tools/generate_registry.py`, `tools/context_packet_assembler.py`, or
  `tools/hybrid_retrieval.py` — this ticket is decision-document-only, per its own Out of Scope.
- Do not invent a fourth branch beyond Decision 3's three (REGISTRY-backed direct mapping /
  `unrated` sentinel / differently-shaped-primitive mapping) — pick one of the three with explicit
  reasoning tied to the real fields, per the ticket's own Acceptance Criteria.
- Do not absorb Open Decision 7 (cross-kind ranking, already resolved by the sibling ticket) or
  Open Decision 9 (exact-vs-fuzzy lookup convention, still pending, separate ticket) into this
  ticket's §6 — stay scoped to Decision 8 only.
- Do not re-litigate whether `staging_artifacts/`'s exclusion is *correct* — the idea doc's own
  Open Decision 8 text already asserts it is "correct today, since it holds in-progress/scratch
  content for open tickets"; this ticket's job is to record that as an explicit, reasoned, durable
  decision (or identify it as an accidental gap if the evidence actually pointed the other way,
  which it does not — see Current Behavior's empirical staging_artifacts lifecycle check).
