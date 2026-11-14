---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX
phase: done
date: 2026-11-14
tags: [ai, governance, process-improvement]
---

# TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX

## Title
Link each decision doc to the role cards that cite it, so an amended decision flags its cards

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
lead-planner's finding of 2026-11-14 (the owner asked for a fix): role cards are generated correctly (`generate_agents.py --check` catches format drift) but nothing links a decision to the cards that cite it, so card content goes stale silently, and a running seat sees a change only at relaunch. TCK-20261114-ROLE-CARDS-CITE-AMENDED-DECISIONS fixes the two stale cards found; this ticket stops the next one.

## Scope
Design reviewed by agent-working-designer 2026-11-14 (approved with 4 changes, folded in below).
(a) Delivery rule (docs/guides/delivery_process.md, PR Lifecycle): a PR that accepts or amends an ADR or recorded decision lists the affected role cards in its body, taken from the check's output, and updates them in the same change. One line in the session_roles guide points to it.
(b) Vocabulary + index:
  - `registries/session_decisions.yaml`: entries `short_name -> path[#section]` with the aliases cards use (e.g. "the devops ADR", "system_overview", "PERF-D1/D2").
  - Each card source file gets a `## Cites` section OUTSIDE `## Card` (not injected) listing the vocabulary names it uses.
  - Detection of amendment: optional frontmatter key `amends: [path#section, ...]` on the accepting doc (2a). Prose parsing of "It amends `x`" is rejected. Backfill distributed_workers_adr with `amends: [docs/architecture/system_overview.md#what-is-deliberately-not-distributed, docs/architecture/devops_plan_amendment_proposal.md#what-stays-from-the-adr]` (paths as the plan settles). First confirm validate_frontmatter does not reject unknown keys; the frontmatter_schema.md / validate_frontmatter before/after goes to that doc's owner as a separate fyi/request, not blocking this ticket.
  - `tools/sessions/card_citation_check.py`, report-only, exit 0: a card citing C where an active doc D has `amends:` naming C and the card does not also cite D is a finding "card X cites C, amended by D", naming the seat ids for that card from the roster.
  - `generate_agents --check` prints one advisory line only when there are findings (no output = no findings).
(c) agent_session_reset_boundaries.md: after a card-changing merge, lead relaunches or clears the seats the check named.
Card scope: domains/ cards; the test is generic over domains/ and functions/ (functions cite no decision doc today).

## Out of Scope
- Rewriting card content (TCK-20261114-ROLE-CARDS-CITE-AMENDED-DECISIONS does the two known cases).
- Auto-relaunching seats.
- A blocking CI gate.
- Making `amends:` a required/validated schema key (schema owner's call).

## Acceptance Criteria
1. Test: every vocabulary name found in a `## Card` is listed in that card's `## Cites`, and every cited path exists (over domains/ and functions/).
2. Check tests on fixtures: positive (card cites C, D amends C, card lacks D -> finding with seat ids), negative (nothing amended -> none), and both-cited (card cites C and D -> none).
3. delivery_process.md states rule (a) including the PR-body list; the reset-boundary guide states step (c); the --check advisory line appears only with findings.
4. Run against origin/main after TCK-20261114-ROLE-CARDS-CITE-AMENDED-DECISIONS merged and the backfill: no findings. (Sequence: start after the hotfix merges, or rebase onto it before the AC4 run.)

## Related Tickets
- TCK-20261114-ROLE-CARDS-CITE-AMENDED-DECISIONS
- TCK-20261004-SESSION-LAYER-M1C-GENERATED-SESSION-AGENT-FILES

## Related Docs
- docs/guidelines/session_roles/
- docs/guides/delivery_process.md
- docs/guides/agent_session_reset_boundaries.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/sessions/generate_agents.py, tools/sessions/card.py, registries/session_roles.yaml, tests/tools/

## Assumptions / Open Questions
- How "amended" is detected (frontmatter field vs an "amends:" line in the accepting ADR) is for the plan; the distributed_workers ADR states its amendments in its header, which is the likely source.
- agent-working-designer reviews the design.

## Implementation Notes
- Plan, investigation and test plan: `agent-working/stored_artifacts/TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX/`. Design approved by agent-working-designer (3 gaps folded in: unlisted-reference and reverse checks in the blocking test, superseded/historical amender fixture, seat-list cut in the advisory) and agent-working-planner (split: Cites-vs-Card test blocks, amendment check report-only).
- Owner-of-doc OK for the `amends:` line in `docs/architecture/distributed_workers_adr.md`: lead-planner (owner of docs/architecture/**), cross-session message of 2026-11-14, on the condition that `amends` is defined once in `docs/guidelines/frontmatter_schema.md` in the same PR (done: a new optional row in the `doc` table). architecture-planner declined to approve (not its path) and had no content objection.
- `validate_frontmatter` accepts unknown keys; pinned by `test_validate_frontmatter_accepts_an_amends_key`.
- The `Cites` section sits after `Card` in the 9 domain and 3 function sources, so it is not injected: `generate_agents --check` shows 0 drift and no card changed.
- Detection: a card uses a name when the name or an alias appears as a whole token. Doc paths ending `.md` and `*_adr` / `*_decision(s)` tokens in a card must resolve to a vocabulary entry.

## Test Summary
- `tests/tools/test_session_card_citations.py`: 28 pass (12 per-card Cites/vocabulary tests over domains/ and functions/, vocabulary target and heading existence, real-tree no-findings, fixture positive/negative/both-cited, section covering, superseded and historical amender, unlisted amender, malformed `amends:`, CLI report-only, seat-list cut, advisory only with findings, docs state the rule).
- Positive controls: dropping `perf_decisions` from architecture's Cites fails the per-card test; dropping `distributed_workers_adr` from architecture's Cites makes `card_citation_check` print the finding naming the four architecture seats.
- Wider scoped run: `pytest tests/tools -k "session or frontmatter or agent_working_paths or ci_workflow_test_coverage or generate_registry"`: 1605 passed, 1 skipped. `tests/integrity/test_no_duplicate_content_blocks.py` passes.
- AC4: `python3 -m tools.sessions.card_citation_check` on this branch after the backfill: `0 citation finding(s)`. `generate_agents --check`: OK, 0 drift, no advisory line.

## Files Changed
- New: `registries/session_decisions.yaml`, `tools/sessions/decisions.py`, `tools/sessions/card_citation_check.py`, `tests/tools/test_session_card_citations.py`.
- Changed: `tools/sessions/generate_agents.py` (advisory line), a Cites section in the 12 files under `docs/guidelines/session_roles/{domains,functions}/`, `docs/architecture/distributed_workers_adr.md` (`amends:`), `docs/guidelines/frontmatter_schema.md`, `docs/guides/delivery_process.md`, `docs/guides/agent_session_reset_boundaries.md`, `docs/plans/agent_infrastructure/session_layer_working_process.md` (pointer).

## Completion Summary
Role card sources now carry a Cites list, `registries/session_decisions.yaml` is the vocabulary, a doc that amends another says so in an optional `amends:` frontmatter key, and `python3 -m tools.sessions.card_citation_check` (report-only, exit 0) names the cards and seat ids that cite an amended decision without the amending doc. `generate_agents --check` prints one advisory line only on findings. The delivery rule and the reset-boundary step are written down.

Known gap: owner-of-doc follow-ups, no new ticket: `next_generation_engine_adr` (calls itself a companion, not an amendment) and the devops amendment have no `amends:` key, and `distributed_workers_adr` is the only doc that has one; the owners of those docs decide if more are needed.
Known gap: the amendment check is report-only and nothing runs it automatically except the `generate_agents --check` advisory line; a seat sees a changed card only at relaunch or `/clear`.
