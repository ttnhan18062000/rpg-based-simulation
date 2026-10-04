---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M3A-ROUTE-OWNER-LOOKUP
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M3A-ROUTE-OWNER-LOOKUP

## Title
Session-layer M3a: `route.py` owner lookup by path and by route key

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add `tools/sessions/route.py <path>` and `--route-key <key>`: answer "who owns this" from the manifest, with no free-text topic lookup (plan 9.1).

Child of `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY`. Hold rule met: M1 merged.

## Scope
- `tools/sessions/route.py`: importable `route(path) -> RouteResult` plus CLI. Resolution: the domains' `owns` globs, the longest matching glob wins; `owns_not` and `routes` carry the content-versus-tooling splits; a path matched by an `ownership_splits` entry returns both domains and the split reason; a path nothing owns returns `unowned` (never a guess).
- Result names the **seat** to contact (the domain planner for dispatch, the named semantic owner for a question, per plan 9.0) and states that liveness is a model-side `ListAgents` call, not computed here.
- ~~`--route-key <key>`~~ WITHDRAWN by the owner 2026-10-05 (see Implementation Notes): a named entry for a recurring subject paths cannot express. The manifest has no such section yet; add a `route_keys:` map to `registries/session_roles.yaml` (empty or with at most the entries evidence supports) and extend loader and validator (unknown role target is an error). The key set is closed: an unknown key is an error, not a fuzzy match.
- Reads only through the typed loader; read-only.

## Out of Scope
- Free-text or semantic topic routing, liveness checks, message-class rules (M3b), any hook or `settings.json` change.

## Acceptance Criteria
1. Test cases from the manifest: `registries/mechanisms.yaml` routes content to the rpg planner and `tools/mechanism_registry/**` to agent-working; `tests/architecture/**` returns the split between rpg and testing; `tools/sessions/**` returns agent-working; `src/**` from the agent-working side routes to `rpg-planner`; an unowned path returns `unowned`.
2. Longest-match wins over a shorter overlapping glob (fixture).
3. ~~`--route-key`~~ withdrawn (owner decision 2026-10-05); `--from <domain>` applies the asking domain's routes instead.
4. Output names a seat and never a session or a liveness claim; a test proves route.py imports nothing that lists sessions.
5. Read-only: a test proves it writes no file. Loader types only; scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (parent), M1a (done; loader and validator)
- M3b (shares the card and templates, not the code)

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding)
- `docs/guidelines/session_roles/functions/*.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Related Code Areas
- `tools/sessions/route.py` (new; reuses `roster.py`), `registries/session_roles.yaml` (`route_keys:`), `tools/sessions/validate.py`, `tests/tools/`.

## Assumptions / Open Questions
- Adding a `route_keys:` section changes the manifest schema; it is registry-backed and append-only in spirit, and M1a's loader and validator are extended in the same ticket. If the owner prefers path-only routing in v1, drop the `--route-key` flag and this section; nothing else changes.

## Implementation Notes
`tools/sessions/route.py`: `route(path, roster, from_domain)` plus CLI (`<path> [--from <domain>]`). Splits first (both domains + reason), else the longest `owns` glob across domains (a domain whose `owns_not` matches is excluded), else `unowned`. `--from` applies the asking domain's `routes` to a path it does not own. Seat = the owning domain's planner. Output states liveness is not computed. Globs: `**` crosses directories, `*` stays in one segment.

**Owner decisions 2026-10-05 (literal diff confirmed in the terminal):** (1) `--route-key` and a `route_keys:` section are dropped for v1 (no evidence of a recurring subject paths cannot express); plan 9.1 records this. (2) `registries/session_roles.yaml` gains `- tools/mechanism_registry/**` under `domains.agent-working.owns`, so AC1's mechanism-registry case resolves to agent-working (before, that path was unowned). The generated `.claude/agents/session-agent-working-*.md` were regenerated for that line.

## Test Summary
`tests/tools/test_session_route.py` (22): manifest cases (mechanisms.yaml -> rpg-planner, tools/mechanism_registry -> agent-working, tests/architecture split, tools/sessions, src, unowned), longest-glob fixture, owns_not, split, `*` vs `**`, `--from`, no-liveness/no-sessions-import, read-only snapshot. Roster/cards/validator/generator suites green (76).

## Files Changed
`tools/sessions/route.py`, `tests/tools/test_session_route.py`, `registries/session_roles.yaml` (one owns line), `.claude/agents/session-agent-working-{designer,planner,implementer}.md` (regenerated), `docs/plans/agent_infrastructure/session_layer_working_process.md` (9.1), `docs/guides/delivery_process.md`.

## Completion Summary
Delivered path-based owner lookup; AC3 (`--route-key`) withdrawn by the owner, so no `route_keys:` schema change. All other acceptance criteria met.

