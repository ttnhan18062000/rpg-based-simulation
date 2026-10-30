# Implementation Sequence: ai-first-sdlc-evolution

Epic `TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION`, filed by agent-working-planner on dispatch from agent-working-designer, 2026-10-31. Plan: `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, section 38 for dependencies. Owner decisions: #715 6529263880.

## Order

1. TCK-20261031-SDLC-PLAN-DOCUMENTS-LAND: first PR, docs only. Everything below cites these files.
2. TCK-20261031-SDLC-E6B-THROWAWAY-REPO-GITHUB-BEHAVIOURS: needs the owner's ask for the repo. First among the authority work, because OD-3's M1 depends on it.
3. Parallel after 1:
   - TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN (Phase 0)
   - TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY (read-only)
   - TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS (tag push has its own ask)
   - TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
   - TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY (Phase 5, independent)
4. BLOCKED, each with its own owner ask:
   - TCK-20261031-SDLC-MACHINE-USER-AND-OWNER-CREDENTIAL-REMOVAL
   - TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION

## Not cut yet

Phases 2, 3, 4 and R1: see the epic's table for the decisions each waits on. They are cut after those decisions are recorded.

## Rules

- No credential or ruleset change runs without its own owner ask, by ticket.
- Credential details stay out of committed files, tickets and public comments (#715 6528807751).
- Pushes, tags and merges are the owner's yes, through lead-planner.
