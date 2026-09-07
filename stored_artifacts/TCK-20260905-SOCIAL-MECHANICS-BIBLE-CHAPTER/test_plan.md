---
status: active
layer: mechanics
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER
date: 2026-09-07
---

# Test Plan: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER

## Scope
Docs-only ticket — no `src/`/`tests/` code authored. "Testing" here means: (a) direct code
verification of every formula cited in the new chapter (done during Investigate, re-confirmed here
via targeted grep/read commands, not a pytest run), and (b) the real regression suite that validates
doc structure/frontmatter/registry consistency.

## Formula Verification Commands (already run during Investigate; re-listed for traceability)
- `grep -n "def process_witnessed_event" -A 15 src/domains/commitment/reputation.py`
- `grep -n "def combine_public_reputation" -A 10 src/systems/social_systems/reputation.py`
- `sed -n '1,80p' src/systems/social_systems/appraisal.py` (trust pipeline + CLAN_INFLUENCE_WEIGHT)
- `cat src/systems/social_systems/memory.py` (place attachment + nemesis promotion)
- `cat src/systems/social_systems/relationships.py` (clamp ranges)
- `grep -rln "GuildMembership\|guild_dues\|GuildRank" src/` (expect 0 hits)
- `grep -rln "PartyRecord" src/` (expect 0 hits)
- `grep -n "class ContractKind" -A 20 src/core/strategic.py` (expect no ESCORT member)
- `cat src/systems/social_systems/party_composition.py` (scoring weights)
- `sed -n '1,45p' src/systems/social_systems/party_lifecycle.py` (defection threshold formula)

## Scoped Pytest Commands
```
pytest tests/tools/test_generate_registry.py tests/tools/test_doc_staleness_check.py \
       tests/tools/test_add_frontmatter_live.py -q
```
Rationale: these are the real tests that validate `docs/REGISTRY.yaml` stays in sync with the real
docs/ tree (the check this ticket's new/edited files must not drift from) and that frontmatter
tooling handles the new chapter's frontmatter block correctly.

## Regression Surface
- `tools/validate_frontmatter.py <path> --content-type doc` on every touched/created file.
- `python3 tools/generate_registry.py` (regenerate, confirm no drift afterward).
- `make knowledge-index-update` (docs/ changed — CLAUDE.md's After Work rule).

## New Tests Required
None — no new src/ behavior to test. The formula-verification commands above are this ticket's own
equivalent of new test coverage (each formula's real source is independently re-confirmed, not
assumed).

## Anti-Drift Test Guards
- Re-running the registry-drift test (`test_check_flag_detects_no_drift_against_real_registry`)
  after `docs/REGISTRY.yaml` regeneration must pass clean — a stale registry after a docs-only
  ticket is itself a real regression this ticket must not introduce.
