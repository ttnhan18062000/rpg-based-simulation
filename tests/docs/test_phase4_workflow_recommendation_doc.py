"""Doc-structure tests for the Knowledge Gateway MCP Phase 4 workflow-integration
recommendation (TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION).

This ticket ships no code and no runtime behavior change — its entire deliverable is a
recommendation document. These tests assert doc *structure* (required section headings,
per-candidate verdict markers, citation-existence, and an anti-mandate deny-list) — never
runtime behavior — mirroring the static-assertion pattern
`tests/docs/test_redaction_retention_policy_doc.py` uses for its own documentation-only ticket.
"""
from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_RECOMMENDATION_DOC = (
    _REPO_ROOT
    / "docs"
    / "engine"
    / "contracts"
    / "knowledge_gateway_mcp"
    / "phase4_workflow_recommendation.md"
)

_REAL_CITED_PATHS = {
    "phase1_baseline_comparison.md": (
        _REPO_ROOT
        / "docs"
        / "engine"
        / "contracts"
        / "knowledge_gateway_mcp"
        / "phase1_baseline_comparison.md"
    ),
    "phase2_baseline_recomparison.md": (
        _REPO_ROOT
        / "docs"
        / "engine"
        / "contracts"
        / "knowledge_gateway_mcp"
        / "phase2_baseline_recomparison.md"
    ),
    "phase3_pilot_acceptance_measurement.md": (
        _REPO_ROOT
        / "docs"
        / "engine"
        / "contracts"
        / "knowledge_gateway_mcp"
        / "phase3_pilot_acceptance_measurement.md"
    ),
    "RETRO-2026-W33.md": (
        _REPO_ROOT / "agent-monitoring" / "retro" / "RETRO-2026-W33.md"
    ),
}

_VERDICT_MARKERS = (
    "**Recommend against.**",
    "**Insufficient evidence to recommend for.**",
    "**Recommend against enabling it today. Flag as the correct landing spot for a future ticket**",
)

_NUMERIC_LATENCY_TOKEN_CLAIM_RE = re.compile(
    r"\d+(?:\.\d+)?\s*ms\b" r"|\d+(?:\.\d+)?\s*tokens?\b" r"|\d+(?:\.\d+)?x\b",
    re.IGNORECASE,
)

_ALLOWLISTED_NEGATION = "creates no mandatory phase, gate, or ticket step"

_MANDATE_DENY_PATTERNS = (
    re.compile(r"must call", re.IGNORECASE),
    re.compile(r"is required to call", re.IGNORECASE),
    re.compile(r"shall invoke", re.IGNORECASE),
    re.compile(r"mandatory[\s\w,]{0,40}gateway", re.IGNORECASE),
)


def _read_doc() -> str:
    return _RECOMMENDATION_DOC.read_text()


# ---------------------------------------------------------------------------
# AC1 / AC2 (structure): required sections present
# ---------------------------------------------------------------------------


def test_phase4_workflow_recommendation_doc_exists_and_has_required_sections():
    assert _RECOMMENDATION_DOC.exists(), f"missing required doc: {_RECOMMENDATION_DOC}"
    text = _read_doc()

    required_headings = [
        "## Headline: This document creates no mandatory phase, gate, or ticket step",
        "## Candidate 1 — Scope and Investigate phases",
        "## Candidate 2 — Document-Update / doc-updater phase",
        "## Candidate 3 — Architecture Review",
        "## Candidate 4 — Dormant shadow-packet hook",
        "## Evidence honesty note",
        "## Open question not settled by this document",
    ]
    for heading in required_headings:
        assert heading in text, f"missing required section heading: {heading}"

    assert _ALLOWLISTED_NEGATION in text


# ---------------------------------------------------------------------------
# AC2: every candidate point gets an explicit verdict, none left unaddressed
# ---------------------------------------------------------------------------


def test_every_candidate_point_has_an_explicit_recommendation_verdict():
    text = _read_doc()

    # Split on "## Candidate " to isolate each candidate section from the rest of the
    # document (headline preamble, evidence-honesty note, open-question section) so a
    # verdict marker appearing in the wrong section is caught rather than silently
    # satisfying the assertion via document-wide presence.
    sections = text.split("## Candidate ")
    assert len(sections) == 5, (
        f"expected exactly 4 '## Candidate ' sections, found {len(sections) - 1}"
    )
    candidate_sections = sections[1:]

    for index, section in enumerate(candidate_sections, start=1):
        found = [marker for marker in _VERDICT_MARKERS if marker in section]
        assert found, (
            f"Candidate {index} section contains no explicit verdict marker "
            f"(expected one of {_VERDICT_MARKERS!r})"
        )


def test_document_update_candidate_uses_insufficient_evidence_not_recommend_against():
    """The Document-Update/doc-updater candidate reflects a genuine capability mismatch,
    not a measured performance regression like the other three candidates — the plan's own
    Anti-Drift Notes forbid flattening it into "recommend against" for consistency."""
    text = _read_doc()
    sections = text.split("## Candidate ")
    candidate_2_section = sections[2]
    assert "**Insufficient evidence to recommend for.**" in candidate_2_section
    assert "**Recommend against.**" not in candidate_2_section


# ---------------------------------------------------------------------------
# AC2: no recommendation is asserted without citing real retro/measurement data
# ---------------------------------------------------------------------------


def test_recommendation_doc_cites_real_evidence_paths_not_fabricated():
    text = _read_doc()

    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    numeric_paragraphs = [
        p for p in paragraphs if _NUMERIC_LATENCY_TOKEN_CLAIM_RE.search(p)
    ]
    assert numeric_paragraphs, "expected at least one paragraph with a numeric latency/token claim"

    for paragraph in numeric_paragraphs:
        cited = [name for name in _REAL_CITED_PATHS if name in paragraph]
        assert cited, (
            "numeric latency/token claim has no adjacent citation to a real measurement "
            f"doc; paragraph: {paragraph!r}"
        )

    cited_anywhere = [name for name, path in _REAL_CITED_PATHS.items() if name in text]
    assert cited_anywhere, "document cites none of the four real evidence paths at all"
    for name in cited_anywhere:
        path = _REAL_CITED_PATHS[name]
        assert path.exists(), f"cited evidence path does not exist on disk: {path}"


# ---------------------------------------------------------------------------
# AC1: the survey's per-candidate call-site citations resolve to real, still-current
# locations (not merely citation-shaped text) — distinct from
# test_recommendation_doc_cites_real_evidence_paths_not_fabricated above, which only checks
# the four *measurement-doc* paths behind numeric claims. That test's shallowness (existence,
# not numeric accuracy) is a disclosed, deliberate limitation per plan.md/test_plan.md's own
# Anti-Drift Notes, deferred to Architecture-Verify's spot-check obligation. This test covers a
# different, previously-uncovered surface: the `<path>:<start>-<end>` code-citation style used
# throughout the Candidate sections (e.g. `.claude/workflows/implement-ticket.js:131-134`) was
# not checked by any existing test for path existence or line-range validity.
# ---------------------------------------------------------------------------


_EXPLICIT_FILE_LINE_CITATION_RE = re.compile(
    r"`(?P<path>\.claude/[A-Za-z0-9_./-]+\.(?:js|md)|[A-Za-z0-9_-]+\.(?:js|md)):"
    r"(?P<start>\d+)(?:-(?P<end>\d+))?`"
)


def test_call_site_file_line_citations_resolve_to_real_locations():
    text = _read_doc()

    explicit_matches = list(_EXPLICIT_FILE_LINE_CITATION_RE.finditer(text))
    assert explicit_matches, "expected at least one explicit `path:start-end` code citation"

    known_paths = {m.group("path") for m in explicit_matches if "/" in m.group("path")}

    checked = 0
    for match in explicit_matches:
        path_str = match.group("path")
        start = int(match.group("start"))
        end = int(match.group("end") or start)

        if path_str.startswith(".claude/"):
            full_path = _REPO_ROOT / path_str
        else:
            # Bare filename shorthand (e.g. "implement-ticket.js:840-902") — resolve against
            # a full path already cited elsewhere in the same document.
            candidates = [p for p in known_paths if p.endswith("/" + path_str)]
            assert candidates, (
                f"bare filename citation {path_str!r} has no matching full path elsewhere "
                "in the document to resolve it against"
            )
            full_path = _REPO_ROOT / candidates[0]

        assert full_path.exists(), (
            f"cited file does not exist: {full_path} (from {match.group(0)!r})"
        )
        line_count = len(full_path.read_text().splitlines())
        assert 1 <= start <= end <= line_count, (
            f"citation {match.group(0)!r} line range {start}-{end} is out of bounds for "
            f"{full_path} ({line_count} lines) — citation is stale or fabricated"
        )
        checked += 1

    assert checked >= 5, f"expected several resolvable file:line citations, found {checked}"


# ---------------------------------------------------------------------------
# AC3: document never states a mandatory requirement
# ---------------------------------------------------------------------------


def test_recommendation_doc_never_states_a_mandatory_requirement():
    text = _read_doc()
    text_without_allowlisted_negation = text.replace(_ALLOWLISTED_NEGATION, "")

    for pattern in _MANDATE_DENY_PATTERNS:
        match = pattern.search(text_without_allowlisted_negation)
        assert match is None, (
            f"document contains mandate-shaped language: {match.group(0)!r} "
            f"(pattern: {pattern.pattern!r})"
        )
