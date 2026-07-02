---
ticket_id: TCK-20260626-FIX-DESIGN-PATTERNS
phase: test_plan
date: 2026-06-26
---

# Test Plan — TCK-20260626-FIX-DESIGN-PATTERNS

## 1. Regression Surface

### Existing tests that must continue passing

| Test file | What it validates | Risk of regression |
|---|---|---|
| `tests/docs/test_doc_integrity.py::test_manifest_file_existence` | All mandatory docs in `docs/engine/manifest.json` exist on disk — `design_patterns.md` is not in the manifest, so this test is unaffected | Low |
| `tests/docs/test_doc_integrity.py::test_document_structural_compliance` | Required headers in each manifest-listed doc — `design_patterns.md` not in manifest | Low |
| `tests/docs/test_doc_integrity.py::test_link_integrity` | Local file links in manifest docs resolve — `design_patterns.md` not in manifest; its internal links checked by the new test only | Low |
| `tests/docs/test_contributor_guardrails.py::test_extension_templates_present` | `docs/engine/engineering_playbook_m10.md` contains extension templates | Not affected |
| `tests/architecture/test_api_read_model_guard.py::test_no_api_route_directly_imports_authoritative_state` | Enforces INFRA-210 presenter law at import level | Not affected — code unchanged |
| `tests/architecture/test_phase_domain_permissions.py` | INFRA-206/207/208 phase permission declarations | Not affected — code unchanged |
| `tests/tools/test_add_frontmatter_live.py` | Reads frontmatter from `docs/guidelines/design_patterns.md` — the frontmatter block will be retained/updated | Low: ensure frontmatter `status`, `layer`, `authority`, `audience` fields remain valid after rewrite |

### Existing doc reference requiring update

`docs/guidelines/README.md` line 14 describes `design_patterns.md` as "Architectural spines (Aspects, Systems, Presenters)." — this description is also stale. The implementation phase must update it to match the new V2-focused description. No test enforces this, but it creates a secondary drift hazard if left stale.

---

## 2. New Tests Required

### 2.1 Anti-drift guard: V1 symbols must not appear as primary extension guidance

**File:** `tests/docs/test_design_patterns_currency.py` (new file)

**Purpose:** Fail CI if `design_patterns.md` reverts to documenting V1 `GoalScorer` / `src/ai/goals/`
as the primary extension model for new code. This test is the anti-drift lock for this ticket.

```python
"""
Anti-drift guard for docs/guidelines/design_patterns.md.
Ensures the doc does not present V1 GoalScorer/src/ai/goals/ as the V2 extension point.
TCK-20260626-FIX-DESIGN-PATTERNS.
"""
import re

DOC_PATH = "docs/guidelines/design_patterns.md"
LEGACY_SECTION_HEADER = "Legacy Patterns"  # Expected header for the V1 archive section


def _load() -> str:
    with open(DOC_PATH, "r") as f:
        return f.read()


def test_v1_symbols_not_in_primary_sections():
    """
    GoalScorer, GoalEvaluator, GOAL_REGISTRY, and src/ai/goals/ must not appear
    in any primary (H2) section outside the legacy archive section.

    Strategy: split on the legacy section header; check that V1 symbols do not
    appear in the content BEFORE the legacy section header.
    """
    content = _load()
    v1_symbols = ["GoalScorer", "GoalEvaluator", "GOAL_REGISTRY", "src/ai/goals/"]

    # Find where the legacy section starts
    legacy_idx = content.find(LEGACY_SECTION_HEADER)
    assert legacy_idx != -1, (
        f"{DOC_PATH} must contain a '## {LEGACY_SECTION_HEADER}' (or similar) section "
        "to archive V1 patterns. Found no such header."
    )

    # Check that V1 symbols are NOT in the primary (pre-legacy) content
    primary_content = content[:legacy_idx]
    for symbol in v1_symbols:
        assert symbol not in primary_content, (
            f"V1 symbol '{symbol}' found in primary (non-legacy) section of {DOC_PATH}. "
            "This symbol must only appear under the Legacy Patterns archive section."
        )


def test_v2_extension_patterns_documented():
    """
    The doc must document at least 3 V2 extension patterns by name.
    """
    content = _load()
    required_patterns = [
        "Domain Phase",         # Pattern A — XPhase class with apply()/execute()
        "StateUpdate",          # Pattern B — typed update records
        "StatePresenter",       # Pattern C — presenter/read-model layer
    ]
    for pattern in required_patterns:
        assert pattern in content, (
            f"V2 pattern term '{pattern}' not found in {DOC_PATH}. "
            "The doc must document V2 extension points."
        )


def test_v2_file_paths_cited():
    """
    The doc must reference the authoritative V2 source files, not only V1 paths.
    """
    content = _load()
    required_paths = [
        "src/domains/",         # Domain phases live here
        "src/core/updates.py",  # Typed update records
        "src/api/presenters/",  # Presenter layer
    ]
    for path in required_paths:
        assert path in content, (
            f"V2 path '{path}' not cited in {DOC_PATH}. "
            "The doc must reference real V2 source locations."
        )


def test_legacy_section_clearly_marked():
    """
    The V1 archive section must be present and marked as not-for-new-code.
    """
    content = _load()
    assert LEGACY_SECTION_HEADER in content, (
        f"{DOC_PATH} must contain a section header with '{LEGACY_SECTION_HEADER}' "
        "to clearly mark V1 patterns as historical."
    )
    # The section must contain at least one of the V1 symbols (confirming it's the archive)
    legacy_idx = content.find(LEGACY_SECTION_HEADER)
    legacy_content = content[legacy_idx:]
    assert any(sym in legacy_content for sym in ["GoalScorer", "src/ai/goals/"]), (
        f"Legacy section in {DOC_PATH} does not mention V1 symbols. "
        "Expected GoalScorer or src/ai/goals/ to appear in the archive section."
    )


def test_no_broken_src_links_in_doc():
    """
    All 'src/' paths cited in the doc (as inline code) must exist on disk.
    Catches regressions where file paths are invented or have moved.
    """
    import os
    content = _load()
    # Match backtick-quoted src/ paths: `src/foo/bar.py`
    cited_paths = re.findall(r"`(src/[^`]+\.py)`", content)
    for rel_path in set(cited_paths):
        assert os.path.exists(rel_path), (
            f"{DOC_PATH} cites '{rel_path}' but the file does not exist. "
            "Update the doc to reflect the current source layout."
        )
```

### 2.2 Frontmatter validity guard (existing coverage)

`tests/tools/test_add_frontmatter_live.py` already reads `docs/guidelines/design_patterns.md`
and validates its frontmatter. The rewrite must preserve a valid frontmatter block with:
- `status: active`
- `layer: guidelines`
- `authority: P1`
- `audience: developer`

No new test needed here — existing coverage is sufficient.

---

## 3. Scoped Pytest Commands

```bash
# Run the new anti-drift guard (primary verification)
pytest tests/docs/test_design_patterns_currency.py -v

# Run the existing doc integrity suite (regression check)
pytest tests/docs/ -v

# Run the architecture guard for presenter law (unchanged by this ticket)
pytest tests/architecture/test_api_read_model_guard.py -v

# Run the frontmatter tooling test (validate frontmatter block survives rewrite)
pytest tests/tools/test_add_frontmatter_live.py -v -k "design_patterns"

# Full scoped run (all of the above, excludes slow tests)
pytest tests/docs/ tests/architecture/test_api_read_model_guard.py tests/tools/test_add_frontmatter_live.py -v -m "not slow"
```

---

## 4. Anti-Drift Test Guards

### Primary guard (new test above)

`tests/docs/test_design_patterns_currency.py` provides four assertions that together prevent
regression to V1 guidance:

| Test | What it catches |
|---|---|
| `test_v1_symbols_not_in_primary_sections` | Prevents `GoalScorer`, `GoalEvaluator`, `GOAL_REGISTRY`, `src/ai/goals/` from returning to primary sections |
| `test_v2_extension_patterns_documented` | Ensures `Domain Phase`, `StateUpdate`, `StatePresenter` are all present |
| `test_v2_file_paths_cited` | Ensures `src/domains/`, `src/core/updates.py`, `src/api/presenters/` are cited |
| `test_legacy_section_clearly_marked` | Ensures the V1 archive section exists AND contains V1 symbols (not accidentally emptied) |
| `test_no_broken_src_links_in_doc` | Prevents cited `src/*.py` paths from becoming stale if files move |

### Why the split-at-legacy-header approach

The test splits document content at the `## Legacy Patterns` header before checking for V1 symbols.
This allows V1 symbols to legally appear in the archive section (they must appear there for the
archive to be meaningful) while ensuring they do not appear in the primary guidance sections.
If someone accidentally moves GoalScorer content out of the legacy section, the test fails.

### Relationship to existing architecture tests

The existing `tests/architecture/test_api_read_model_guard.py` enforces the presenter law at
the import level (code, not docs). The new doc test enforces the same law at the documentation
level. Together they create a two-layer guard: the code boundary is enforced architecturally, and
the documentation of the boundary is enforced by the currency test.

### Parity ledger entry to add

After implementation, add `INFRA-220` to `docs/parity_ledger/infrastructure.yaml`:

```yaml
- id: INFRA-220
  text: >
    docs/guidelines/design_patterns.md documents V2 extension patterns (Domain Phase
    class, typed update records via src/core/updates.py, presenter/read-model layer
    via src/api/presenters/, feature pack registration) as the authoritative extension
    model for new code. V1 patterns (GoalScorer, src/ai/goals/) are archived in a
    clearly-marked Legacy section and not presented as active extension points.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    docs/guidelines/design_patterns.md (rewritten TCK-20260626-FIX-DESIGN-PATTERNS)
  proof_type: null
  test_path: tests/docs/test_design_patterns_currency.py
  divergence_note: null
  support_boundary: "Doc tooling only — no simulation behavior involved."
```
