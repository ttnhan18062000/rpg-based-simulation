---
ticket_id: TCK-20260612-DOMAINS-ARCH-MAP
phase: plan
---

# Plan: Domains Architecture Map

## Ordered Steps

1. Create docs/domains/domain_ownership_map.md — all 14 domains table
2. Create docs/domains/combat_engagement_contract.md
3. Create docs/domains/information_contract.md
4. Create docs/domains/campaigns_contract.md
5. Create docs/domains/optimization_contract.md
6. Run python3 tools/validate_frontmatter.py docs/domains/
7. Run make docs-registry

## Scope Guards
- Do NOT document cognition/strategy (already in docs/strategy/)
- Do NOT change source code
- Cross-link cognition_domain_ownership.md for perception/time/memory/motivation/commitment/cooperation

## Deviations
(none yet)
