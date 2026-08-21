import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent

# Ticket-scoped directories only (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT) — not all of docs/**.
SCOPE_DIRS = ("docs/engine", "docs/architecture", "docs/performance")

# Backtick-quoted or bare tokens matching a file-extension-bearing path under one of the
# four known top-level source/doc roots. The negative lookbehind stops a match starting
# mid-path (e.g. "dashboard-frontend/src/lib/x.ts" must not match as "src/lib/x.ts").
PATH_PATTERN = re.compile(r"(?<![\w/-])(?:src|tests|tools|docs)/[\w./-]+\.\w+")

# src/legacy/ is the canonical, structural marker for a completed V1-to-V2 replacement
# (docs/engine/legacy_replacement_ledger.md: "the old path is no longer reachable in
# production" — by definition, not drift). Excluded the same way docs/archive/ is: by
# path prefix, not by hand-exempting individual doc files.
LEGACY_PATH_PREFIX = "src/legacy/"


def _iter_scoped_docs():
    for scope in SCOPE_DIRS:
        yield from sorted((ROOT / scope).rglob("*.md"))


def _frontmatter_status(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    data = yaml.safe_load(text[3:end]) or {}
    return data.get("status")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "12 pre-existing dead path citations remain across docs/engine/ (3, top-level "
        "authoritative_*.md contract docs), docs/engine/contracts/regression_and_verification.md "
        "(5), docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md "
        "(2, citing a src file+test confirmed deleted by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE "
        "per git log), and docs/performance/optimization_invariants.md (2). Zero-candidate searches "
        "(no renamed file found under any path) suggest most of the remaining citations point to "
        "tests that were never implemented, not simply moved — resolving each needs per-doc "
        "investigation at the depth TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT's own plan explicitly "
        "deferred to the recommended follow-up ticket (see docs/audits/D25_engine_docs_drift.md's "
        "'Recommended Follow-Up' section for the itemized list). 22 other dead citations found by "
        "this same test during Implement were fixed directly (real renames/relocations, confirmed by "
        "unique-match search) — this xfail covers only the residual, unresolvable-with-confidence set. "
        "strict=True: once the follow-up ticket resolves or formally re-scopes all 12, this marker "
        "must be removed by whoever closes that ticket, the same self-enforcing pattern already used "
        "by test_kernel_phase_names_consistent.py's xfail."
    ),
)
def test_doc_path_citations_exist():
    """Every src/tests/tools/docs path cited in a scoped, active doc must resolve on disk.

    This is what would have caught docs/guides/simulation.md's former citation of the
    nonexistent src/engine/authoritative_pipeline.py (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT).
    Note docs/guides/ itself is outside this test's scope (docs/engine, docs/architecture,
    docs/performance only) — that fix was applied directly, this test guards the three
    directories this ticket is scoped to.
    """
    failures = []
    for doc_path in _iter_scoped_docs():
        text = doc_path.read_text()
        status = _frontmatter_status(text)
        if status is not None and status != "active":
            continue
        for cited in sorted(set(PATH_PATTERN.findall(text))):
            if cited.startswith("docs/archive/") or cited.startswith(LEGACY_PATH_PREFIX):
                continue
            if not (ROOT / cited).exists():
                failures.append(f"{doc_path.relative_to(ROOT)}: cites {cited!r} which does not exist")

    assert not failures, "Dead path citation(s) found:\n" + "\n".join(failures)
