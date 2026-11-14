---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX
phase: done
date: 2026-11-14
tags: [ai, governance, process-improvement]
---

# Plan

Files (all inside agent-working's ownership except the two noted):
1. `registries/session_decisions.yaml` (new): `decisions: {short_name: {path: ..., aliases: [...]}}`, path may end in `#section`. Seeded with the names the two cards use.
2. `tools/sessions/decisions.py` (new, no side effects): load the vocabulary; `cites_in_card(text, vocab)`; parse a `## Cites` section; `amending_docs(root)`; `resolve` and the covers rule.
3. `tools/sessions/card_citation_check.py` (new): `find_findings(root) -> list[Finding]`, CLI prints one line per finding naming the card, the cited name, the amending doc and the seat ids; always exit 0.
4. `tools/sessions/generate_agents.py`: `--check` prints one `ADVISORY` line when `find_findings` is non-empty; no output otherwise; exit code unchanged. Module-top import.
5. `docs/guidelines/session_roles/domains/*.md` and `functions/*.md`: add `## Cites` after `## Card` (a bullet list, empty marker "none" for cards that cite nothing). Card text untouched.
6. `docs/architecture/distributed_workers_adr.md` (architecture-owned): add `amends:` frontmatter. Needs the architecture owner's OK; sent as a request with the exact diff, and the change is one frontmatter line.
7. Docs: `docs/guides/delivery_process.md` PR Lifecycle gets rule (a); `docs/guidelines/session_roles` guide line pointing to it; `docs/guides/agent_session_reset_boundaries.md` gets step (c). `delivery_process.md` is a governing guide: owner approval is checked at the #715 comment before I edit it (the dispatch approval 6873240715 covers this ticket; I will verify the comment text first).
8. `tests/tools/test_session_card_citations.py` (new, under a CI-covered directory). Frontmatter note: pinned there as a test that `validate_frontmatter` accepts `amends:`.

Order: vocabulary and loader, check and tests (fixtures), Cites sections, backfill, docs, AC4 run recorded in the ticket, registry regen, monitoring closure.

Out of scope as ticketed: rewriting cards, auto-relaunch, a blocking CI gate, making `amends` a schema key.
