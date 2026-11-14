---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX
phase: done
date: 2026-11-14
tags: [ai, governance, process-improvement]
---

# Investigation: link decision docs to the role cards that cite them

Measured on origin/main db918c517 (after #908).

## Findings
1. **Card text comes from two files per seat.** `tools/sessions/card.py::compose_card` injects only the `## Card` section (regex `^## Card ... (?=^## |\Z)`) of `functions/<f>.md` and `domains/<d>.md`. Anything after another `## ` heading is not injected, so a `## Cites` section placed after `## Card` changes no generated card: `generate_agents --check` stays at 0 drift, and the 456-token card budget is untouched.
2. **Which cards cite a decision doc today.** Over the nine domain files, only two `## Card` sections name one: `architecture.md` (system_overview, distributed_workers_adr, next_generation_engine_adr, PERF-D1/D2, plus the devops ADR and kernel_concurrency_design_philosophy by prose name) and `platform.md` (`docs/architecture/distributed_workers_adr.md`). The three function files cite none.
3. **`amends` is not used as a key anywhere.** No doc has a frontmatter `amends:`. The word appears in prose in `distributed_workers_adr`, `next_generation_engine_adr`, `devops_plan_amendment_proposal`, `performance_optimization_decisions` and others, which is why the design rejects prose parsing.
4. **`validate_frontmatter` accepts unknown keys.** `_validate_doc` checks the four required fields, enums, tags and evidence fields only; nothing rejects an extra key. A test will pin that, so a later schema change that rejects `amends` fails loudly rather than silently breaking the check.
5. **Anchors the backfill needs exist.** `docs/architecture/system_overview.md` has `## What is deliberately not distributed`. The devops amendment section "What stays from the ADR" is to be confirmed at implementation.
6. **Seat ids.** `Roster.roles` carries `role`, `domain`, `function`; a domain card maps to every role whose `domain` matches (e.g. architecture: planner, implementer, both hosts), a function card to every role with that `function`.

## Design points the plan fixes
- A card "uses" a vocabulary name when its name or one of its aliases appears in the `## Card` text (word-boundary match).
- The amendment finding compares paths and sections: an `amends:` target `path#section` covers a cite `path[#section]` when the paths are equal and either side has no section or the sections are equal.
- The check scans `docs/**/*.md` frontmatter (first 40 lines, status active or authoritative) for `amends:`. It cannot scan only the vocabulary, because a newly accepted ADR is not in it yet; that is the case the check exists for.
- A doc that has `amends:` and is not in the vocabulary is reported too ("D amends C but has no entry in session_decisions.yaml"), otherwise the both-cited rule could never be satisfied.

## Open questions
1. AC1 is a blocking test over `## Card` versus `## Cites` (both live in the same file, so it only fails when a card author skips the Cites step). The amendment check itself stays report-only. Confirm that split.
2. Whether `next_generation_engine_adr` and `devops_plan_amendment_proposal` should get `amends:` too. Proposal: backfill only what AC4 needs (distributed_workers_adr); file the rest as owner-of-doc requests.
