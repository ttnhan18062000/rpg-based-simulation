---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX
phase: done
date: 2026-11-14
tags: [ai, governance, process-improvement]
---

# Test plan

All in `tests/tools/test_session_card_citations.py`, tmp-path fixtures with a miniature repo root (roster, two card sources, three docs).
- **AC1 (real tree):** for every file in domains/ and functions/, every vocabulary name or alias found in `## Card` is listed in `## Cites`; every cited path (and its `#section` heading slug) exists.
- **AC2 positive:** card cites C, active doc D has `amends: [C]`, card lacks D: one finding naming card, C, D and the seat ids from the roster.
- **AC2 negative:** nothing amends C: no findings.
- **AC2 both-cited:** card cites C and D: no findings.
- Section covering: target `path#a` versus cite `path#b` gives no finding; versus cite `path` (no section) gives a finding.
- A superseded or historical D (status not active/authoritative) is ignored.
- D with `amends:` but absent from the vocabulary: reported as such.
- Malformed `amends:` (not a list): reported, never raised; exit stays 0.
- **AC3:** `generate_agents --check` prints the advisory line only with findings (fixture with and without); exit code unchanged. Docs tests: delivery_process.md carries the rule and the PR-body list, the reset-boundary guide carries step (c).
- `validate_frontmatter` accepts a doc with an `amends:` key.
- **AC4 (one-off, recorded in the ticket):** `python3 -m tools.sessions.card_citation_check` on the branch after the backfill prints no findings.
- Also before push: paths-guard, test_ci_workflow_test_coverage, test_no_duplicate_content_blocks, ruff, `generate_agents --check` = 0 drift, `generate_registry --check`. No heavy run needed.
