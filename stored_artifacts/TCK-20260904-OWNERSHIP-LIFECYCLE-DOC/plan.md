---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260904-OWNERSHIP-LIFECYCLE-DOC
artifact_type: plan
tags: [ai, documentation, governance]
---

# Implementation Plan — TCK-20260904-OWNERSHIP-LIFECYCLE-DOC

## Summary

This is a pure documentation ticket: create one new canonical doc,
`docs/guidelines/subsystem_ownership_lifecycle.md`, with a 5-column ownership/lifecycle table
(Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition), a role
vocabulary section resolving the dangling "roadmap's shared role vocabulary" citation, 7 table
rows (2 already-drafted + 3 batch subsystems + 2 self-referential meta-rows) and 2 explicit
exclusion notes (bash secret-scan hook, AST import-boundary enforcement) for the 2 batch
subsystems that do not get a row. Then update 3 existing docs to point at it instead of
duplicating or leaving a dangling citation: `telemetry_retention_epic.md` (mark its M3 draft table
historical, fix the citation), `governance_capability_policy_epic.md` and
`workflow_reliability_epic.md` (one-line cross-references). All content below is drafted verbatim
from real, cited evidence in `investigation.md` — no placeholder text. Layer/tag choices reuse
already-registered values (`layer: guidelines`, tags `ai`/`documentation`/`governance`) — no new
registry entries needed.

**Plan resolves investigation.md's one open interpretive question up front** (see Anti-Drift Notes):
every "Removal condition" cell below answers "when is the underlying mechanism itself
retired/superseded," not "when is this row deleted from the table" — applied consistently across
all 7 rows.

## Steps

### Step 1 — Create the canonical doc with frontmatter, role vocabulary, table, and exclusions
**Files:** `docs/guidelines/subsystem_ownership_lifecycle.md` (new)
**Change:** Create the file with exactly this content:

```markdown
---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [ai, documentation, governance]
---

# Subsystem Ownership & Lifecycle

This doc is the canonical table recording, for every governance-relevant subsystem the AI-First
Hardening epics touch, an accountable role (never a person), an update trigger, a staleness
signal, and a removal condition. It is the M3 deliverable of
`docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`, shipped by
`TCK-20260904-OWNERSHIP-LIFECYCLE-DOC`. It supersedes that doc's own planning-time M3 draft table
(now marked historical there) and resolves the draft's dangling "roadmap's shared role vocabulary"
citation by defining the vocabulary here instead.

## Accountable Role Vocabulary

- **Agent Configuration Maintainer** — owns `.claude/agents/*.md` frontmatter scoping and the
  capability-envelope baseline/diff script.
- **Workflow Runtime Maintainer** — owns `.claude/workflows/*.js` pipeline logic, done-checker gate
  wiring, and pipeline-adjacent hooks.
- **Documentation Governance Maintainer** — owns this table itself and the artifact-retention-
  classification table.

## Ownership & Lifecycle Table

| Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition |
|---|---|---|---|---|
| Capability-envelope baseline (`docs/ai/capability_envelope_baseline.md` + diff script — `governance_capability_policy_epic.md` M2) | Agent Configuration Maintainer | Any new legitimate permission need | Baseline diverges from a working local file | Superseded by a genuine runtime-enforced approved-envelope check that closes the mechanism's own disclosed limitation (no confirmed mechanism today enforces the envelope relationship automatically at runtime); migration ticket recorded here |
| Ticket-claim detection log (Bucket-B experiment — `workflow_reliability_epic.md` M2) | Workflow Runtime Maintainer | Continuous | Zero incidents after 30 days | Zero double-claim incidents surface after a full quarter of operation (the epic's own kill criteria) — downgraded from "build a lock" to "keep as documented convention"; if the Experiment Specification is later killed outright rather than downgraded, record the closing ticket here |
| Tools frontmatter rollout (`.claude/agents/*.md` `tools:` scoping — `governance_capability_policy_epic.md` M3; Wave 1 shipped by `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`, Waves 2-3 pending) | Agent Configuration Maintainer | The prior wave's observation window clears with no unresolved permission regression, unblocking the next wave's ticket | A wave's ticket sits open past its gating window with no observation-window evidence recorded, or a permission-related failure surfaces that is not identifiable by agent/tool/workflow-phase | All 3 waves ship and the epic's Horizon-0 exit signal confirms zero critical workflow breakage over the stated observation window; this row is then folded into a single "shipped" note rather than tracked wave-by-wave |
| Doc-coverage reverse-check (`check_docs_to_update_coverage`'s reverse direction, `tools/gate_checks/done_checker_static.py` — shipped by `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`) | Workflow Runtime Maintainer | A new doc-touching pipeline phase/agent is added, or the Files Changed/Related Docs section-parsing contract changes | A real recurrence of a docs/ path touched-but-undeclared incident (the ITEM-INSTANCE-HISTORY/RACE-RELATIONS-MATRIX/READINESS-SPEED-FORMULA pattern) slips through Verify despite the check being wired in | A different, more general reverse-coverage mechanism (covering all touched paths, not just `docs/`) supersedes this check, closing its disclosed `docs/`-only scope limitation; migration ticket recorded here |
| Test-scoper hang guard (`SubagentStop` hook, `tools/agent-monitoring/subagent_stop_background_guard.py` — shipped by `TCK-20260904-TEST-SCOPER-HANG-GUARD`) | Workflow Runtime Maintainer | The harness's `SubagentStop` payload schema changes (e.g. `background_tasks` field renamed/reshaped), or a new hook event key is added that could supersede this mechanism | A real subagent background-hang recurrence is observed despite the hook being wired in `.claude/settings.json`, or the hook's one-time self-referential retry rate is observed to compound rather than resolve | `test-scoper.md`'s prose Background Commands section and this hook are both superseded by a first-party Claude Code feature that makes turn-end background-task blocking a harness default; migration ticket recorded here |
| Artifact-retention classification table (`docs/guidelines/artifact_retention_classification.md`, M2 deliverable of this same epic) | Documentation Governance Maintainer | A new persistent artifact class is introduced anywhere in the repo (new top-level dir/file family) | A merged ticket introduces such a class and it is not reflected in the 8-row table within the same PR | The classification table is folded into a different repo-wide artifact index; migration ticket recorded here |
| Subsystem ownership & lifecycle table (this doc) | Documentation Governance Maintainer | Any future ticket creates, materially changes, or retires a subsystem this table covers | A merged ticket changes a covered subsystem's shape/lifecycle without a corresponding row edit in the same PR (no automated check exists for this yet — accepted gap, named here rather than silently left) | This table is superseded by a different tracking mechanism (e.g. folded into `docs/REGISTRY.yaml` metadata); migration ticket recorded here |

## Excluded Subsystems

The following in-batch subsystems are deliberately **not** given a table row, with the reasoning
stated explicitly rather than left implicit:

- **Bash secret-exposure advisory hook** — excluded — subsystem is BLOCKED
  (`TCK-20260904-BASH-SECRET-SCAN-HOOK`), no code exists yet; add a row when it ships and is
  unblocked.
- **AST import-boundary enforcement** — excluded — ownership is a matter for whoever maintains the
  already-shipped `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`'s code, not re-assigned here;
  this subsystem predates the AI-First Hardening batch entirely and was only discovered
  already-shipped during this batch's own investigation pass, mirroring the `agent-monitoring/data/`
  weekly-shard layout's own exclusion precedent in `telemetry_retention_epic.md`'s M3 section.

## Related Docs (disambiguation, cross-link only)

This table answers "who is accountable for noticing this subsystem has gone stale, and when
should it be removed." It does not overlap with these structurally distinct ownership docs, which
answer "which code/test suite owns this behavior":

- `docs/testing/content_migration_test_ownership.md` — maps `tests/` suites to the behavior they
  cover (columns: Suite path | Marker/tier | Owns | Preserves).
- `docs/simulation/domains/domain_ownership_map.md` — maps `src/domains/` packages to their
  contract docs.
- `docs/architecture/cognition_domain_ownership.md` — maps cognition sub-models to their owning
  packages, plus code-removal history.
```

Every behavioral/schema claim embedded in this table cell text is cited to its source at the point
of use (`governance_capability_policy_epic.md:75-78` for the capability-envelope limitation,
`:123-124` for the wave-gating rule, `:174-177` for the M5 exit signal; `workflow_reliability_epic.md:81-84`
for the kill criteria; the 3 batch tickets' own Status/Files-Changed sections for what shipped) —
see `investigation.md`'s Current Behavior section for the full citations this cell text is drawn
from verbatim.
**Do NOT touch:** the 3 existing differently-shaped ownership docs listed under Related Docs above
(cross-link only, per ticket Out of Scope); `docs/guidelines/artifact_retention_classification.md`'s
own table content (only referenced by path in the meta-row, never restated).
**Verify:** `test_subsystem_ownership_lifecycle_doc_exists_and_has_five_columns`,
`test_subsystem_ownership_lifecycle_doc_covers_both_drafted_rows`,
`test_subsystem_ownership_lifecycle_doc_documents_each_batch_subsystem_or_justified_exclusion`,
`test_subsystem_ownership_lifecycle_doc_defines_role_vocabulary`,
`test_accountable_role_column_never_names_a_person`,
`test_bash_secret_scan_hook_not_given_shipped_style_row`.

### Step 2 — Mark `telemetry_retention_epic.md`'s M3 draft table historical, fix the dangling citation
**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`
(lines 93-109, read directly — cited in `investigation.md`'s Current Behavior section)
**Change:** Two edits, both outside the table itself:

1. Line 96's sentence — currently `an accountable role (not a person — see the roadmap's shared
   role vocabulary), an update trigger, a staleness signal, and a` — change only the parenthetical
   to `(not a person — see docs/guidelines/subsystem_ownership_lifecycle.md's Accountable Role
   Vocabulary section)`. Do not change anything else on that line.
2. Insert one new paragraph immediately before the table (after the sentence ending "...and a
   removal condition:" and before the `| Subsystem | ...` header line), mirroring M2's own
   historical-marker pattern at lines 70-74 of the same file:

   ```
   **M3 is shipped — see `docs/guidelines/subsystem_ownership_lifecycle.md`.** The table below
   reflects this milestone's original planning-time draft. The committed, evidence-verified
   version — with the Accountable Role Vocabulary section and explicit row-or-exclusion decisions
   for every other in-batch subsystem — now lives at
   `docs/guidelines/subsystem_ownership_lifecycle.md`, shipped by
   `TCK-20260904-OWNERSHIP-LIFECYCLE-DOC`. Treat that doc as authoritative; this table is retained
   here for historical context only.
   ```

**Do NOT touch:** the table header (`| Subsystem | Accountable role | Update trigger | Staleness
signal |`, still 4 columns) or its 2 data rows (lines ~101-102) — leave every character of the
table itself untouched, per the Anti-Drift Hazard in `investigation.md` ("do not silently fix the
draft M3 table's own columns in place"). Do not touch the closing paragraph after the table
("This milestone documents ownership for this epic's own remaining subsystems...") or the
weekly-shard exclusion sentence above the table — both are pre-existing, unrelated text.
**Other writers to this file:** `telemetry_retention_epic.md` is also touched by
`TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION` (already shipped — added the M2 historical marker
at lines 70-74 this step mirrors) and, per `investigation.md`'s Prior Work, no other ticket is
currently open against this file's M3 section. No concurrent-write risk identified beyond the
general shared-worktree caution CLAUDE.md already states; this step only edits prose immediately
around the (untouched) M3 table, at a location no other in-flight ticket's diff touches per
`investigation.md`'s Prior Work section.
**Verify:** `test_telemetry_retention_epic_no_longer_cites_roadmap_role_vocabulary`,
`test_draft_m3_table_marked_historical_not_edited_in_place`.

### Step 3 — Add one-line cross-references from the 2 sibling epic docs
**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md`
**Change:**
- In `governance_capability_policy_epic.md`, immediately after the M2 section's existing bullet
  list (after line 81, "What requires review: any local entry the diff flags as outside it."),
  add: `**Ownership/lifecycle row:** see docs/guidelines/subsystem_ownership_lifecycle.md for this
  subsystem's accountable role, update trigger, staleness signal, and removal condition — not
  restated here.` Additionally, immediately after the M3 section's wave-based-rollout list (after
  line 134's Wave 3 bullet, before the "Observability requirement" paragraph), add the same
  cross-reference sentence for the tools-frontmatter-rollout row, since that subsystem's row also
  lives in the new canonical doc: `**Ownership/lifecycle row:** see
  docs/guidelines/subsystem_ownership_lifecycle.md for this subsystem's accountable role, update
  trigger, staleness signal, and removal condition — not restated here.`
- In `workflow_reliability_epic.md`, immediately after the M2 section's existing paragraph (after
  line 88, "...see the freeze verdict's Bucket-B handoff boundary."), add the same sentence:
  `**Ownership/lifecycle row:** see docs/guidelines/subsystem_ownership_lifecycle.md for this
  subsystem's accountable role, update trigger, staleness signal, and removal condition — not
  restated here.`
**Do NOT touch:** any other section of either file (M1/M3 in `workflow_reliability_epic.md`, M1/M4/M5
in `governance_capability_policy_epic.md`) — this ticket only adds these 3 one-line
cross-references, nothing else in either doc.
**Other writers to these files:** per `investigation.md`'s Prior Work and the files' own recent
edit history (both list `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`,
`TCK-20260904-CAPABILITY-ENVELOPE-BASELINE`, `TCK-20260904-AGENT-TOOL-USAGE-BASELINE` as recent
writers to `governance_capability_policy_epic.md`'s M1/M3 sections), none of those tickets are
still open — all are DONE per the ticket files read during Investigation. No other ticket is
currently in-flight against these 2 files' M2 section text. This step's inserts are single
sentences appended after existing paragraphs, at line offsets that will shift if a concurrent
session edits earlier lines first — re-read each file immediately before editing to confirm the
anchor text is still where expected, same practice the shipped
`TCK-20260904-TEST-SCOPER-HANG-GUARD` ticket used before its own `settings.json` edit.
**Verify:** `test_sibling_epic_docs_link_to_canonical_ownership_doc`.

### Step 4 — Add the new test file
**Files:** `tests/docs/test_subsystem_ownership_lifecycle_doc.py` (new)
**Change:** Create the file with exactly this content (static text assertions only — never
import/execute the doc, mirroring `tests/docs/test_artifact_retention_classification_doc.py`):

```python
"""Doc-structure tests for the subsystem ownership & lifecycle doc
(TCK-20260904-OWNERSHIP-LIFECYCLE-DOC).

This is the M3 deliverable of `telemetry_retention_epic.md`: the canonical table recording an
accountable role, update trigger, staleness signal, and removal condition for every
governance-relevant subsystem the AI-First Hardening epics touch. These tests assert doc
*structure* (required headings, required table columns, required phrases present as distinct,
individually matchable text) — never runtime behavior — mirroring the static-assertion pattern
`tests/docs/test_artifact_retention_classification_doc.py` uses.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_DOC = _REPO_ROOT / "docs" / "guidelines" / "subsystem_ownership_lifecycle.md"
_TELEMETRY_EPIC = (
    _REPO_ROOT / "docs" / "plans" / "agent_infrastructure" / "ai_first_hardening_epics"
    / "telemetry_retention_epic.md"
)
_GOVERNANCE_EPIC = (
    _REPO_ROOT / "docs" / "plans" / "agent_infrastructure" / "ai_first_hardening_epics"
    / "governance_capability_policy_epic.md"
)
_WORKFLOW_EPIC = (
    _REPO_ROOT / "docs" / "plans" / "agent_infrastructure" / "ai_first_hardening_epics"
    / "workflow_reliability_epic.md"
)
_ARTIFACT_RETENTION_DOC = (
    _REPO_ROOT / "docs" / "guidelines" / "artifact_retention_classification.md"
)

_REQUIRED_COLUMNS = [
    "Subsystem",
    "Accountable role",
    "Update trigger",
    "Staleness signal",
    "Removal condition",
]

_ROLE_VOCABULARY = [
    "Agent Configuration Maintainer",
    "Workflow Runtime Maintainer",
    "Documentation Governance Maintainer",
]

_BATCH_SUBSYSTEM_EVIDENCE = {
    "bash secret-scan hook": "TCK-20260904-BASH-SECRET-SCAN-HOOK",
    "tools frontmatter rollout": "TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE",
    "AST import-boundary enforcement": "TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC",
    "doc-coverage reverse-check": "TCK-20260904-DOC-COVERAGE-REVERSE-CHECK",
    "test-scoper hang guard": "TCK-20260904-TEST-SCOPER-HANG-GUARD",
}

_ARTIFACT_CLASS_STRINGS = [
    "agent-monitoring/data/",
    "stored_artifacts/",
    "tickets/done/",
    "retro/RETRO-*.md",
    "working_log.csv",
    "graphify-out/",
    "knowledge-index/",
    ".claude/current_run",
]


def _read(path: Path) -> str:
    return path.read_text()


def _table_rows(text: str) -> list[str]:
    """Return every markdown table-row line (starts with '| ') in the Ownership & Lifecycle Table."""
    start = text.index("## Ownership & Lifecycle Table")
    end = text.index("## Excluded Subsystems")
    section = text[start:end]
    return [line for line in section.splitlines() if line.strip().startswith("|")]


def test_subsystem_ownership_lifecycle_doc_exists_and_has_five_columns():
    assert _DOC.exists(), f"missing required doc: {_DOC}"
    text = _read(_DOC)
    rows = _table_rows(text)
    header = rows[0]
    for column in _REQUIRED_COLUMNS:
        assert column in header, f"table header missing column: {column}"


def test_subsystem_ownership_lifecycle_doc_covers_both_drafted_rows():
    text = _read(_DOC)
    rows = _table_rows(text)
    data_rows = rows[2:]  # skip header + separator

    capability_row = next(
        (r for r in data_rows if "Capability-envelope baseline" in r), None
    )
    assert capability_row is not None, "missing Capability-envelope baseline row"
    assert "Agent Configuration Maintainer" in capability_row
    cells = [c.strip() for c in capability_row.strip().strip("|").split("|")]
    assert len(cells) == 5 and all(cells), "capability-envelope row must have 5 non-empty cells"

    ticket_row = next(
        (r for r in data_rows if "Ticket-claim detection log" in r), None
    )
    assert ticket_row is not None, "missing Ticket-claim detection log row"
    assert "Workflow Runtime Maintainer" in ticket_row
    cells = [c.strip() for c in ticket_row.strip().strip("|").split("|")]
    assert len(cells) == 5 and all(cells), "ticket-claim row must have 5 non-empty cells"


def test_subsystem_ownership_lifecycle_doc_documents_each_batch_subsystem_or_justified_exclusion():
    text = _read(_DOC)
    for _label, ticket_id in _BATCH_SUBSYSTEM_EVIDENCE.items():
        assert ticket_id in text, f"missing evidence token for batch subsystem: {ticket_id}"


def test_subsystem_ownership_lifecycle_doc_defines_role_vocabulary():
    text = _read(_DOC)
    assert "## Accountable Role Vocabulary" in text
    vocab_start = text.index("## Accountable Role Vocabulary")
    vocab_end = text.index("## Ownership & Lifecycle Table")
    vocab_section = text[vocab_start:vocab_end]

    rows = _table_rows(text)
    data_rows = rows[2:]
    used_roles = set()
    for row in data_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) == 5:
            used_roles.add(cells[1])

    for role in used_roles:
        assert role in vocab_section, f"role used in table but not defined in vocabulary: {role}"


def test_accountable_role_column_never_names_a_person():
    text = _read(_DOC)
    rows = _table_rows(text)
    data_rows = rows[2:]
    for row in data_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) == 5:
            assert cells[1] in _ROLE_VOCABULARY, (
                f"Accountable role cell is not a declared vocabulary role: {cells[1]!r}"
            )


def test_bash_secret_scan_hook_not_given_shipped_style_row():
    text = _read(_DOC)
    rows = _table_rows(text)
    matching_rows = [r for r in rows if re.search(r"secret[- ]scan|secret-exposure", r, re.I)]
    if matching_rows:
        for row in matching_rows:
            assert "BLOCKED" in row or "not yet built" in row, (
                "bash secret-scan hook row must be visibly marked speculative/pre-ship"
            )
    exclusions_start = text.index("## Excluded Subsystems")
    exclusions_end = text.index("## Related Docs")
    exclusions_section = text[exclusions_start:exclusions_end]
    assert "TCK-20260904-BASH-SECRET-SCAN-HOOK" in exclusions_section
    assert "BLOCKED" in exclusions_section


def test_telemetry_retention_epic_no_longer_cites_roadmap_role_vocabulary():
    text = _read(_TELEMETRY_EPIC)
    assert "roadmap's shared role vocabulary" not in text.lower()
    m3_start = text.index("### M3")
    assert "docs/guidelines/subsystem_ownership_lifecycle.md" in text[m3_start:]


def test_draft_m3_table_marked_historical_not_edited_in_place():
    text = _read(_TELEMETRY_EPIC)
    assert (
        "| Subsystem | Accountable role | Update trigger | Staleness signal |" in text
    ), "original 4-column M3 draft table header must remain textually intact"
    assert (
        "Capability-envelope baseline (from `governance_capability_policy_epic.md`) | "
        "Agent Configuration Maintainer | Any new legitimate permission need | "
        "Baseline diverges from a working local file |" in text
    ), "original capability-envelope draft row must remain textually intact"
    assert (
        "Ticket-claim detection log (from `workflow_reliability_epic.md`) | "
        "Workflow Runtime Maintainer | Continuous | Zero incidents after 30 days |" in text
    ), "original ticket-claim draft row must remain textually intact"
    assert "M3 is shipped" in text, "must add a shipped/historical marker note"


def test_sibling_epic_docs_link_to_canonical_ownership_doc():
    for path in (_GOVERNANCE_EPIC, _WORKFLOW_EPIC):
        text = _read(path)
        assert "docs/guidelines/subsystem_ownership_lifecycle.md" in text, (
            f"{path} does not link to the canonical ownership doc"
        )


def test_three_existing_ownership_docs_unmodified():
    for rel_path in (
        "docs/testing/content_migration_test_ownership.md",
        "docs/simulation/domains/domain_ownership_map.md",
        "docs/architecture/cognition_domain_ownership.md",
    ):
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", rel_path],
            cwd=_REPO_ROOT,
            capture_output=True,
        )
        assert result.returncode == 0, f"{rel_path} was modified by this ticket but must not be"


def test_artifact_retention_classification_row_count_unchanged():
    text = _read(_ARTIFACT_RETENTION_DOC)
    for artifact_class in _ARTIFACT_CLASS_STRINGS:
        assert artifact_class in text, f"missing pre-existing artifact class: {artifact_class}"
    start = text.index("## Retention Classification Table")
    body = text[start:]
    row_lines = [
        line for line in body.splitlines()
        if line.strip().startswith("|") and "---" not in line
    ]
    data_rows = row_lines[1:]  # drop header
    assert len(data_rows) == 8, (
        f"expected exactly 8 artifact-class rows, found {len(data_rows)} — "
        "this ticket must not add/remove rows in this file"
    )
```

**Do NOT touch:** `tests/docs/test_artifact_retention_classification_doc.py` or
`tests/docs/test_redaction_retention_policy_doc.py` — both stay untouched regression guards.
**Verify:** running `pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py -v` — all tests
pass.

### Step 5 — Run the full scoped verification suite
**Files:** none (verification only)
**Change:** Run, in order:
1. `python3 tools/validate_frontmatter.py docs/guidelines/subsystem_ownership_lifecycle.md`
2. `pytest tests/docs/ tests/tools/test_validate_frontmatter.py tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v`
   (the exact scoped command from `test_plan.md`)
3. `make docs-registry` (or equivalent) to preview `docs/REGISTRY.yaml` regeneration mid-session,
   then confirm the new doc's path/tags/layer appear correctly. (Per CLAUDE.md's After Work step,
   the authoritative regeneration happens automatically at Finalize's post-migration self-check —
   this run is a preview/confirmation, not a substitute.)
**Do NOT touch:** `docs/REGISTRY.yaml` by hand — it is generated, never hand-edited.
**Verify:** all commands above exit 0 / all tests pass; `docs/REGISTRY.yaml` (after Finalize's
regeneration) lists `docs/guidelines/subsystem_ownership_lifecycle.md` with `layer: guidelines` and
tags `ai`, `documentation`, `governance`.

## Scope Guards

- Do not merge, rewrite, or edit `docs/testing/content_migration_test_ownership.md`,
  `docs/simulation/domains/domain_ownership_map.md`, or
  `docs/architecture/cognition_domain_ownership.md` — cross-link from the new doc only (ticket Out
  of Scope, enforced by `test_three_existing_ownership_docs_unmodified`).
- Do not build or populate `docs/guidelines/artifact_retention_classification.md`'s own 8-row table
  content — only reference it by path in one meta-row (ticket Out of Scope bullet 3, enforced by
  `test_artifact_retention_classification_row_count_unchanged`).
- Do not edit `telemetry_retention_epic.md`'s M3 draft table's header or its 2 data rows in place —
  mark historical with surrounding prose only (Anti-Drift Hazard, enforced by
  `test_draft_m3_table_marked_historical_not_edited_in_place`).
- Do not reassign ownership of the `agent-monitoring/data/` weekly-shard layout — already
  explicitly excluded in `telemetry_retention_epic.md`'s existing text; leave that sentence
  untouched.
- Do not touch `guardrail_enforcement_epic.md`, `roadmap.md`, `docs/ai/README.md`, or
  `docs/guidelines/artifact_retention_classification.md` beyond what Step 1's meta-row references
  by path — `investigation.md`'s Docs Requiring Update section explicitly excludes edits to all
  four of these.
- Do not add a preemptive table row for the bash secret-scan hook — it stays an exclusion note
  naming the BLOCKED ticket, per the ticket's own recommendation; if a row is ever added instead,
  it must be visibly marked speculative/pre-ship, never presented as equivalent-confidence to the
  shipped/drafted rows.
- Do not reuse the `lifecycle` tag for this doc's frontmatter — it is registry-scoped to
  `src/systems/lifecycle_systems/` (reproduction/birth/death), a different subsystem meaning
  entirely, despite the word appearing in this ticket's own title.

## Dependency Map

All 5 steps are independently completable and verifiable — no step blocks another:
- Step 1 (new doc) does not depend on Steps 2-3 (edits to other docs) — the new doc's content is
  self-contained and does not require those edits to exist first.
- Step 2 (telemetry_retention_epic.md) and Step 3 (governance/workflow epic docs) both reference
  the new doc's path by string only — they can be done before or after Step 1 exists on disk,
  though doing Step 1 first lets Step 4's tests validate cross-references against a real file.
- Step 4 (new test file) should run last among the content steps, since its assertions read all of
  Steps 1-3's output — but writing the test file's text does not require Steps 1-3 to be complete
  first (this plan specifies the test content precisely enough that it can be written in parallel).
- Step 5 (verification) depends on Steps 1-4 all being complete.

Recommended execution order: Step 1 → Step 2 → Step 3 → Step 4 → Step 5.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Single committed doc with columns Subsystem \| Accountable role \| Update trigger \| Staleness signal \| Removal condition, covering at minimum the 2 drafted rows plus an explicit row-or-justified-exclusion decision for each other new/changed subsystem in this batch | Step 1 | `test_subsystem_ownership_lifecycle_doc_exists_and_has_five_columns`, `test_subsystem_ownership_lifecycle_doc_covers_both_drafted_rows`, `test_subsystem_ownership_lifecycle_doc_documents_each_batch_subsystem_or_justified_exclusion` |
| Sibling epic docs link to the canonical table doc rather than restating rows | Step 3 | `test_sibling_epic_docs_link_to_canonical_ownership_doc` |
| The dangling "roadmap's shared role vocabulary" citation is resolved — either a real section is added and referenced correctly, or the citation is corrected to point at wherever roles are actually defined | Step 1 (adds the section), Step 2 (fixes the citation) | `test_subsystem_ownership_lifecycle_doc_defines_role_vocabulary`, `test_telemetry_retention_epic_no_longer_cites_roadmap_role_vocabulary` |
| New doc passes `tools/validate_frontmatter.py` and appears in `docs/REGISTRY.yaml` after regeneration | Step 1 (frontmatter), Step 5 (validation + registry regeneration) | direct `validate_frontmatter.py` run; `docs/REGISTRY.yaml` inspection after Finalize |

## Anti-Drift Notes

- **Removal-condition semantics, resolved by this plan:** every "Removal condition" cell above
  answers "when is the underlying mechanism itself retired/superseded," never "when is this row
  deleted from the table" — consistent with the M2-drafted rows' own language ("Baseline diverges
  from a working local file" describes mechanism staleness, not row deletion). This was flagged in
  `investigation.md` as requiring an explicit Plan-time decision rather than silent assumption;
  this plan makes that decision explicit here so Implement does not need to re-decide it.
- **Do not silently fix the draft M3 table's own columns in place** — Step 2 is prose-only around
  the untouched table; see Scope Guards.
- **Do not let the Accountable Role column drift into naming actual people** — enforced by
  `test_accountable_role_column_never_names_a_person`'s closed-vocabulary check against exactly the
  3 roles Step 1 defines.
- **Do not treat "5+ other new subsystems" as a closed, exact-5 list** — if Implement discovers a
  6th in-batch subsystem this Investigation missed, add a row or exclusion for it too rather than
  silently omitting it; if none is found, the 5 named in the ticket's own Scope bullet are
  sufficient and no further search is required.
- **Do not resolve the bash-secret-scan-hook exclusion by inventing forward-looking staleness
  metadata for code that doesn't exist** — Step 1's exclusion note deliberately contains no
  Update-trigger/Staleness-signal/Removal-condition language for that subsystem; if Implement
  decides to add a preemptive row instead (a legitimate alternate call the ticket allows), it must
  be explicitly labeled speculative/pre-ship per `test_bash_secret_scan_hook_not_given_shipped_style_row`.
- **`layer: observability` (used by the ticket/investigation/test_plan files themselves) is
  deliberately different from `layer: guidelines` (used by the new deliverable doc)** — the ticket
  classifies the *work* as cross-subsystem observability concern; the *deliverable* matches the
  directory convention of every other doc actually inside `docs/guidelines/`. Do not "fix" this
  apparent mismatch by making them match — it is intentional, per `investigation.md`'s Risks and
  Open Questions section and the `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION` precedent.
