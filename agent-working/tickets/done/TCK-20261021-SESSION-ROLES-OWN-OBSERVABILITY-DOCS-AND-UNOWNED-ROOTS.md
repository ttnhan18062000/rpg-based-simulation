---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-SESSION-ROLES-OWN-OBSERVABILITY-DOCS-AND-UNOWNED-ROOTS
phase: done
date: 2026-10-21
tags: [ai, governance]
---

# TCK-20261021-SESSION-ROLES-OWN-OBSERVABILITY-DOCS-AND-UNOWNED-ROOTS

## Title
Eleven paths that route as unowned get an owner in session_roles.yaml: the 8 docs/observability files, README.md, docs/guides/feature_flags.md and tools/release/**

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner decisions of 2026-10-21, relayed by lead-planner. The rule is that each doc belongs to whoever owns the code or data it describes:
- The 8 `docs/observability/*.md` files: platform-planner raised `loki_label_policy.md`, then `route.py` showed that all 8 are unowned. lead-planner routed them.
- `README.md`, `docs/guides/feature_flags.md`, `tools/release/**`: from #704 (owner decision comment 2026-10-21 10:03Z). #704 is reopened to track these three.

Lead also told us to file and dispatch now, not after 2026-10-25. Once this lands, each new owner fixes its own text: lead fixes README, rpg fixes feature_flags.md, testing fixes the release tools.

All 11 paths route `status: unowned` on origin/main 4099c0889 (checked with `python3 -m tools.sessions.route <path>`).

## Scope
1. `registries/session_roles.yaml` (a governing file). Add to each domain's `owns`:
   | Domain | Add |
   |---|---|
   | platform | `docs/observability/loki_label_policy.md` |
   | rpg | `docs/observability/prometheus_metrics.md`, `docs/observability/hard_law_monitor.md`, `docs/observability/decision_trace_contract.md`, `docs/observability/read_model_service_contract.md`, `docs/observability/how_to_run_simulation.md`, `docs/guides/feature_flags.md` |
   | agent-working | `docs/observability/retrieval_retention_redaction_policy.md`, `docs/observability/agent_ops_dashboard_contract.md`, with a comment: "contract for the agent-monitoring data the dashboard reads; the code under src/api/agent_ops_dashboard stays rpg (src/** route)" |
   | testing | `tools/release/**` (generate_release_proof.py, release_gate.py) |
   | lead | `README.md` |
   Use explicit file entries, not a `docs/observability/**` glob. A future doc there must not get an owner silently.
   The registry has no co-owner field (`owns`/`owns_not`/`routes` only). The existing `src/** -> rpg-planner` routes already cover the dashboard code.
2. Routes. Several domains route `"tools/**": agent-working-designer` (codebase, testing, lead, platform). Make sure `route.py --from <domain> tools/release/release_gate.py` gives testing-planner for every domain. Where a `tools/**` route would win, add `"tools/release/**": testing-planner` to that domain's routes, the same way codebase's `tools/test_architecture/**` route works. Check the same for the other 10 paths against every domain's routes.
3. Regenerate the role cards (`python3 -m tools.sessions.generate_agents`). The card budget is 415 tokens (`tools/sessions/card.py`). Decision of the owner (2026-10-21, via lead-planner and agent-working-planner): the budget is raised from 415 to 440 for this batch, because explicit file entries for 11 paths cannot fold (precedent 400->415 on 2026-10-20). The follow-up TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT is filed to bring it back down.
4. Update any test that pins the owns lists, the routes or the card text.

## Out of Scope
- Fixing the text of any of the 11 paths. Each new owner fixes its own.
- Any other ownership change. `docs/REGISTRY.yaml`, `.claude/handover/drafts/**` and `agent-working/tickets/todos/**` stay unowned. `test_unowned_paths_are_not_an_event` uses them.
- `.claude/settings.json`, CLAUDE.md.

## Acceptance Criteria
1. `python3 -m tools.sessions.route <path>` names the domain in the Scope table for all 11 paths (tools/release: check both files). Record the output in Test Summary.
2. `route.py --from <d>` for every domain d resolves each of the 11 paths to the new owner's seat, not to a stale `tools/**` route. Record the matrix, or a one-line "all N combinations resolve" with the command.
3. No other path changes owner. Diff `route.py` over all tracked paths before and after. Only the 11 paths, and other files under `tools/release/` if any, may move.
4. `python3 -m tools.sessions.validate`: 0 findings. If a new entry overlaps another domain's glob, it needs an `ownership_splits` entry or a narrower glob; report it rather than silencing it.
5. `python3 -m tools.sessions.generate_agents --check`: no drift. Every card is within 415 tokens. Record the worst card.
6. Tests: `tests/tools/test_agent_working_paths_guard*.py` and `pytest tests/tools -k "session or route or roster or card or boundary" -p no:randomly` pass. Grep `tests/` and `tools/` for anything that counts or lists unowned paths. At filing, nothing counts them; the only fixtures are `test_session_route.py` (a synthetic path) and `test_session_boundary.py` (paths that stay unowned). Re-check, and record the result.
7. The PR body carries the literal `session_roles.yaml` hunk for the owner to confirm. lead-planner reviews the batch SHA before any push.

## Related Tickets
- TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (same shape; it raised the budget from 400 to 415)
- TCK-20261013-SEARCH-MCP-FILES-OWNED (brace folding in card.py)
- TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING (platform; may edit loki_label_policy.md)
- #704 (README / feature_flags / tools/release), #634 (cross-host claim)

## Related Docs
- `docs/guidelines/session_roles/`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `registries/session_roles.yaml`
- `tools/sessions/{route,validate,generate_agents,card}.py`
- `.claude/agents/session-*.md` (generated)
- `tests/tools/test_session_*.py`

## Assumptions / Open Questions
- Checked at filing: no u24 branch touches `registries/session_roles.yaml` or `.claude/agents/`. Re-check `git ls-remote origin` and #634 before pushing.
- If the edit to `registries/session_roles.yaml` triggers the role-capability permission prompt, retry in your own window and the owner approves there. Never work around it.

## Implementation Notes
- `registries/session_roles.yaml`: 11 explicit `owns` entries (rpg 6, agent-working 2, platform 1, lead 1, testing `tools/release/**`) and a `"tools/release/**": testing-planner` route in codebase, lead and platform (the three domains with a `tools/**` route that do not claim the path; testing claims it itself).
- Over budget after the edit: 9 of 25 cards (worst 437). Fold and trim options were put to agent-working-planner; the owner chose to raise the limit to 440. `card.py`, `test_session_platform_domain.py` and `host_suffixed_twins.md` updated. Worst card now 437 (rpg-implementer).
- Cherry-picked 8dcec1a20 (files the follow-up ticket only; not implemented here).

## Test Summary
- Route matrix over all 18080 tracked files x (no domain + 8 domains): 18 paths change (the 10 files plus 8 under tools/release/), every view gives the new owner's seat. Command: iterate `tools.sessions.route.route(path, roster, domain)`.
- `python3 -m tools.sessions.validate`: 0 findings. `generate_agents --check`: no drift.
- `pytest tests/tools -k "session or route or roster or card or boundary or paths_guard" -p no:randomly`: 855 passed, 1 skipped.
- Grep for unowned-path counts: only test_session_route / test_session_boundary / test_session_status fixtures, unchanged and passing.

## Files Changed
- registries/session_roles.yaml, .claude/agents/session-*.md (25, generated), tools/sessions/card.py, tests/tools/test_session_platform_domain.py, docs/guidelines/session_roles/host_suffixed_twins.md

## Completion Summary
11 paths now route to their owners (rpg 6, agent-working 2, platform 1, lead 1, testing `tools/release/**`) with `tools/release/**` routes in codebase, lead and platform. Card budget raised 415 -> 440 by owner decision; worst card 437. No other path changed owner.
