---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# investigation — TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

Source: brief section 3 B4 and the planner's notes. `git ls-files` top level after B1 to B3 has 40 entries (20 directories, 20 files). Sibling layout test `tests/codebase/test_domain_root_layout.py` shows the style. Single source of truth: the test parses the guideline, so the list cannot diverge from the doc.
