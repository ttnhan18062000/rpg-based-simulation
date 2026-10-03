---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-ADR
artifact_type: test_plan
tags: [ai, workflows, process-improvement]
---

# Test Plan — TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Regression Surface

This ticket is a pure documentation deliverable (one new `docs/architecture/`
file plus a `docs/REGISTRY.yaml` regeneration and a one-line link addition to
an existing plan doc). No `src/` or `tools/agent-monitoring/` code changes are
in scope, so the regression surface is limited to the frontmatter/registry
tooling that any new or edited `docs/` file must keep passing.

- **Frontmatter validation (unit)**
  - `tests/tools/test_validate_frontmatter.py` — must keep passing unmodified;
    confirms the enum constants (`STATUS_VALUES`, `LAYER_VALUES`,
    `AUTHORITY_VALUES`, `AUDIENCE_VALUES`) this ADR's frontmatter must satisfy
    have not drifted.
- **Registry generation (unit)**
  - `tests/tools/test_generate_registry.py` — must keep passing; confirms
    `tools/generate_registry.py` still correctly walks `docs/` and emits
    well-formed entries after the new file is added.
  - `tests/tools/test_registry_query.py` — must keep passing; confirms
    registry-query filtering (by `layer`/`related_code_areas`/`tags`) still
    works with one more `type: doc` entry present.
- **Integration**
  - `tests/integration/content/test_registry_projection_parity.py` — must
    keep passing; broader parity check between `docs/REGISTRY.yaml` and the
    underlying doc set.
- **Sibling-batch precedent (not required to re-run, but same class)**
  - `tests/tools/test_codex_capability_diagnostics.py` (from
    `TCK-20260721-CODEX-CAPABILITY-MATRIX`) and
    `tests/tools/test_monitoring_writer_lockfile_candidate.py` (from
    `TCK-20260721-MONITORING-WRITER-DECISION`) are unaffected by this
    ticket's scope (no writer/hook code touched here) — listed for context
    only, not part of this ticket's regression surface.

## New Tests Required

This ticket is overwhelmingly a documentation/decision-record deliverable —
most of its 6 AC bullets are prose requirements with no natural unit-test
surface (e.g. "ADR body contains explicit, separately labeled decisions" is
verified by human/reviewer reading, not by an automated assertion on prose
content). The genuinely testable slice is the frontmatter/registry mechanics,
which existing tools already cover — so this ticket needs **zero new test
files**; it needs three verification *commands* run against the new/edited
artifacts (not new pytest functions), plus reuse of the existing tests above
to confirm no regression. Recorded here as the concrete per-AC mapping:

| AC bullet | Testable? | How verified |
|---|---|---|
| ADR lands at `docs/architecture/<name>.md` with valid frontmatter passing `tools/validate_frontmatter.py` | Yes — script check | `python3 tools/validate_frontmatter.py docs/architecture/<chosen-name>.md` (exit code 0) |
| ADR contains 5 explicit, separately-labeled decisions | No — prose-structure requirement | Manual review during Plan/Implement; not a pytest-checkable assertion. If a stricter guard is wanted, a lightweight heading-presence check could grep for 5 expected `###`/`##` decision headings, but no existing precedent doc enforces prose structure this way — recommend not over-engineering a test for section headings on a single doc. |
| ADR treats execution identity as already-decided, consumed input; no independent choice | No — prose-content requirement | Manual review; cross-check against `docs/ai/monitoring_writer_decision.md` §2's exact `execution_id` format string to confirm the ADR does not propose a different shape. |
| ADR cites all 3 evidence-input tickets and states no final location/writer choice | No — prose-content requirement | Manual review; grep for the three ticket IDs (`TCK-20260721-AGENTS-DIR-DISPOSITION`, `TCK-20260721-CODEX-CAPABILITY-MATRIX`, `TCK-20260721-MONITORING-WRITER-DECISION`) present in the ADR body as a quick sanity check, not a formal test. |
| ADR filename/numbering convention explicitly chosen and justified | No — prose-content requirement | Manual review of the ADR's own stated rationale section. |
| Registered via `docs/REGISTRY.yaml` regeneration; linked from plan doc's Related Material | Yes — script + grep check | `make knowledge-index-update` (or `make docs-registry` to preview) then confirm the new file's `path:` appears in `docs/REGISTRY.yaml`; separately confirm the new doc's relative path appears in `idea_provider_agnostic_agent_orchestration.md`'s `## Related Material` section (currently 11 entries, lines 447-459). |

No new pytest test file is required for this ticket's own deliverable. If
Implement/Verify wants a durable regression guard beyond one-time manual
verification (e.g. to prevent a future edit from silently breaking this ADR's
frontmatter or dropping the registry link), the **Anti-Drift Test Guards**
section below names the minimum viable addition and where it would live —
but adding it is optional scope, not a hard requirement of this ticket's AC.

## Scoped Pytest Commands

```bash
.venv/bin/python -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v
```

```bash
.venv/bin/python -m pytest tests/integration/content/test_registry_projection_parity.py -v
```

Never `pytest tests/` — both commands above are scoped to the
frontmatter/registry tooling domain this ticket's deliverable actually
touches.

## Anti-Drift Test Guards

- **Frontmatter drift guard (already exists, reused not created):**
  `tests/tools/test_validate_frontmatter.py`'s enum-sync tests already catch
  the case where this ADR's frontmatter uses a `layer`/`status`/`authority`/
  `audience` value that isn't in the registered enum — running it after the
  file is added is sufficient; no new test needed.
- **Registry-omission guard:** the two-step manual verification in the New
  Tests Required table above (`make knowledge-index-update` then grep the
  new `path:` in `docs/REGISTRY.yaml`) is the guard against silently landing
  the ADR without registering it — this is the single most likely omission
  for a doc-only ticket (easy to forget since it's not a code change with a
  failing test on skip).
- **Related-Material link-omission guard:** same pattern — a quick
  `grep -n "<new-adr-relative-path>" docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`
  after editing confirms the AC's explicit "linked from the main plan doc's
  Related Material section" requirement was not skipped.
- **Execution-identity re-decision guard:** the sharpest scope-creep risk in
  this ticket is the ADR silently proposing a *different* `execution_id`
  format, field name, or ownership than
  `docs/ai/monitoring_writer_decision.md` §2 already fixed. There is no
  automated test for this (it's a prose-consistency requirement across two
  docs), so the guard is procedural: before finalizing the ADR body, diff its
  execution-identity language against `monitoring_writer_decision.md:91-142`
  line by line and confirm no contradictory field name, format string, or
  ownership claim was introduced.
- **Containment guard:** confirm `git diff --stat` for this ticket's commit
  touches only `docs/architecture/<new-file>.md`,
  `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`
  (one link addition), `docs/REGISTRY.yaml`, `tickets/`, `staging_artifacts/`
  → `stored_artifacts/`, `tickets/working_log.csv`, and
  `agent-monitoring/` — any diff touching `.claude/workflows/`,
  `.claude/settings.json`, `tools/agent-monitoring/*.py` (other than the
  monitoring-run/event entries required by every workflow run), or
  `.codex/` would violate the ticket's own containment rule and should block
  Finalize.
