---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-ORACLE-MAP-REPORT
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261003-SOCIAL-ORACLE-MAP-REPORT

Measured at `origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6`, 2026-10-03.

- Ledger: 294 entries (246 verified, 44 legacy_verified, 3 divergent, 1 missing); 227 P0, of which 211 have no `test_path` (166 verified with no proof_type, 44 legacy_verified, 1 missing). The plan's figures (227 / 211) hold.
- All 23 test-file references in existing `test_path` values resolve to files that exist.
- SOC-052 (missing, P0) cites a test path that never existed in this repository, per its own `support_boundary`.
- SOC-242, SOC-263 and SOC-265 (divergent, P1) are an observability-delivery migration, a canonical-hash coverage gap, and a nemesis-versus-friend-role precedence fix; each has `test_path` entries.
- `appraisal.py` line 46 reads `source_entity.social.public_reputation`; line 64 reads `state.clans[clan_id].clan_reputation`. The "catalog-CONFLICTING (PERC-01 / KNOW-01)" label comes from the plan's G4 answer by `world-rule-catalog-design`; it is reported, not re-derived here.
- `reputation.py` has no direct importer under `tests/unit/social/`.
- CLAUDE.md's Bible table lists chapters 01 to 06; `docs/mechanics/07_social_political_dynamics.md` exists but is not listed.

Docs to update: `docs/testing/social_test_report_2026-10-03.md` (section 3).
