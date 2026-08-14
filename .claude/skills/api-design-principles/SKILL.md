---
name: api-design-principles
description: "Master REST and GraphQL API design principles to build intuitive, scalable, and maintainable APIs that delight developers. Use when designing new APIs, reviewing API specifications, or establishing..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# API Design Principles

Master REST and GraphQL API design principles to build intuitive, scalable, and maintainable APIs that delight developers and stand the test of time.

## Use this skill when

- Designing new REST or GraphQL APIs
- Refactoring existing APIs for better usability
- Establishing API design standards for your team
- Reviewing API specifications before implementation
- Migrating between API paradigms (REST to GraphQL, etc.)
- Creating developer-friendly API documentation
- Optimizing APIs for specific use cases (mobile, third-party integrations)

## Do not use this skill when

- You only need implementation guidance for a specific framework
- You are doing infrastructure-only work without API contracts
- You cannot change or version public interfaces

## Instructions

1. Define consumers, use cases, and constraints.
2. Choose API style and model resources or types.
3. Specify errors, versioning, pagination, and auth strategy.
4. Validate with examples and review for consistency.

Refer to `resources/implementation-playbook.md` for detailed patterns, checklists, and templates.

## In This Repo

This skill's REST/GraphQL guidance is generic and does not know about this repo's own hard,
gate-enforced boundary rule: API routes (`src/api/routes/`, `src/api/ws/`, `src/api/server.py`)
must consume `src/api/presenters/*.py` only — never a raw `AuthoritativeState`/`EntityState`
domain object (CLAUDE.md's "Do not expose raw domain models from APIs" Hard Rule, AST-enforced
unconditionally by `tests/architecture/test_api_read_model_guard.py`). When this skill's generic
principles (e.g. "return the full resource") would conflict with that rule, the repo rule wins —
route through a presenter, never the raw model.

## Resources

- `resources/implementation-playbook.md` for detailed patterns, checklists, and templates.
