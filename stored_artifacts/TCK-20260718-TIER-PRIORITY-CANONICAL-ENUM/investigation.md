---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
date: 2026-07-18
tags: [frontmatter, data-quality]
---

# Investigation — TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM

## Current Behavior (file:line refs)

- `tools/validate_frontmatter.py:44-47` defines `LAYER_VALUES` (19 values) as
  a module-level `set`. `_check_enum()` (`tools/validate_frontmatter.py:132-136`)
  checks a frontmatter dict value against a given `valid` set. `validate_file()`
  (`tools/validate_frontmatter.py:244+`) calls `_check_enum` for
  `status`/`layer`/`authority`/`audience`/`phase` — **frontmatter fields
  only**, extracted via `extract_frontmatter()`.
- `tools/gate_checks/done_checker_static.py:236-262`'s `check_frontmatter_valid`
  calls `validate_file(ticket_path)` — confirms the existing hard gate only
  ever validates frontmatter, never body sections.
- `run_static_precheck` (`done_checker_static.py:266-282`) aggregates 5 Part
  A conditions: `staging_artifacts_complete`, `data_runs_clean`,
  `ticket_location`, `working_log_no_row_yet`, `frontmatter_valid`. No
  existing condition touches `## Tier`/`## Priority`.
- `tools/generate_registry.py:54-66`'s `parse_body_section(body, section)`
  extracts body-section text (everything from `## <section>` to the next
  `## ` heading or EOF) — this is the function that must be used for
  `## Tier`/`## Priority`, exactly as `status_drift_check.py` already uses
  it for `## Status`.
- `src/api/agent_ops_dashboard/ingest.py:375` defines
  `WORKFLOW_STATUS_VALUES: list[str] = sorted({"OPEN", "INPROGRESS",
  "BLOCKED", "DONE", "EPIC_SCOPED"})` — added earlier today by
  TCK-20260718-STATUS-FACET-CANONICAL, dashboard-module-local, not a shared
  `tools/` location.
- `ingest.py:28-35` already puts `tools/` on `sys.path` and imports
  `from validate_frontmatter import extract_frontmatter` and
  `from generate_registry import parse_body_section, _strip_frontmatter` —
  confirms a new `tools/ticket_field_values.py` module is importable from
  `ingest.py` with the exact same one-line import pattern already in use.
- `tools/gate_checks/status_drift_check.py:44-46` puts
  `Path(__file__).parent.parent` (i.e. `tools/`) on `sys.path` — same
  pattern, confirms `gate_checks/*.py` can import a new top-level
  `tools/ticket_field_values.py` cleanly too.
- Corpus scan (direct, via `parse_body_section`, executed live during this
  investigation): `## Tier` — 932 `standard` / 103 `hotfix` / 40 `epic`,
  zero drift. `## Priority` — 794 `P1` / 240 `P2` / 25 `P0` / 24 `P3` / **2
  `"P1: High"`**.
- `CLAUDE.md`'s Ticket Format section (`## Priority (P0 | P1 | P2)`) is
  missing `P3`, confirmed by direct read — a real doc/reality mismatch
  independent of any code change.

## Mechanics/Engine Constraints

None — this is agent-tooling/ticket-schema infrastructure, not simulation
gameplay code. No `docs/mechanics/` or `docs/engine/` chapter applies.

## Parity Ledger Overlap (IDs + status)

None found for this specific concern. `INFRA-277` (status_drift_check.py,
`docs/parity_ledger/infrastructure.yaml`) is the closest precedent but
covers a different check function; this ticket's new check function is a
distinct capability and likely needs its own new parity entry if this
ticket's `behavior_changed` requires one (a pure detection/validation
addition with no `src/` mutation may not need one — Parity phase will
determine via `implementation.files_changed`/`behavior_changed`, following
the same skip-eligibility logic every prior ticket this session has used).

## Prior Work

- TCK-20260718-STATUS-FACET-CANONICAL (this session) — established the
  `WORKFLOW_STATUS_VALUES` pattern this ticket generalizes to Tier/Priority
  and consolidates.
- TCK-20260718-STATUS-DRIFT-REPAIR / -SUFFIX-TRIM / -MULTILINE-FIX (this
  session) — established the drift-detection-and-fix discipline the sibling
  corpus-cleanup ticket will follow; `status_drift_check.py`'s docstring
  itself documents the exact lesson (first-token-only regex missed real
  drift twice) this ticket's design must not repeat — hence using
  `parse_body_section` directly from the start, not a bespoke regex.

## Risks and Open Questions

- Where exactly to put the new body-section enum-check *function* (as
  opposed to the enum *values*, which clearly belong in the new
  `tools/ticket_field_values.py`): co-locating it in the same new module
  keeps enum-definition and enum-checking together (mirrors
  `validate_frontmatter.py`'s own shape, where `LAYER_VALUES` and
  `_check_enum` live in the same file) — chosen over splitting it into
  `gate_checks/`, since the check function itself has no dependency on
  anything `gate_checks/`-specific and `done_checker_static.py` already
  imports across package boundaries freely (e.g. it already imports
  `tag_registry`, `validate_frontmatter` — both top-level `tools/` modules).
- `WORKFLOW_STATUS_VALUES`'s existing importers: only
  `src/api/agent_ops_dashboard/ingest.py` (grep confirms — no other file
  references it). Safe to move without a re-export shim; `ingest.py`'s own
  import line changes from a local definition to `from ticket_field_values
  import WORKFLOW_STATUS_VALUES`.
- `status_drift_check.py`'s own `EPIC_TIER_VALUES = {"EPIC_SCOPED"}` — a
  narrower, drift-detection-specific set (Status-only, includes the
  epic-terminal exemption) — is conceptually different from
  `WORKFLOW_STATUS_VALUES` (the dashboard's full canonical Status set,
  which also includes `EPIC_SCOPED` as a normal member, not an exemption).
  Leave `status_drift_check.py`'s own `EPIC_TIER_VALUES` as-is; it is a
  drift-check-specific concept, not the same thing as the canonical
  facet/validation source of truth this ticket builds.

## Anti-Drift Hazards

- Do not duplicate `LAYER_VALUES`'s literal value set in the new module —
  import and re-export it from `validate_frontmatter.py`, so there is
  exactly one physical definition, avoiding the exact "duplicated enum goes
  stale" failure mode `status_drift_check.py`'s own docstring warns about.
- The new body-section check function must use `parse_body_section` +
  `_strip_frontmatter` (the real dashboard-equivalent extraction), never a
  bespoke regex — this is the single most important lesson from this
  session's Status-drift tickets.
