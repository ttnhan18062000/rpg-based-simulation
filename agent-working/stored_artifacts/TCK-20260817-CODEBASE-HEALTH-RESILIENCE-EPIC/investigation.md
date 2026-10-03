---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC
artifact_type: investigation
tags: [architecture, engine, observability]
---

# Investigation — TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC

## Source material

Two audit documents were provided by the user directly (not produced by this session's own
investigation), authored in the gitignored `tmp/` directory:

- `tmp/architecture_resilience_audit.md` → preserved as `docs/audits/D23_architecture_resilience.md`
- `tmp/codebase_health_observatory_audit.md` → preserved as `docs/audits/D24_codebase_health_observatory.md`

Both state their own method (direct source/doc inspection plus multiple independent
investigation passes, cross-verified against implementation) and both explicitly tag every claim
as Confirmed / Inferred / Unable-to-verify, with file:line citations for Confirmed claims. This
investigation treats both as trustworthy source material rather than re-deriving their findings
from scratch — the work here is triage and grouping, not re-auditing.

## What was verified in this investigation pass

- **`tmp/` is gitignored** (`grep -n "^tmp" .gitignore` → `tmp/*`; confirmed via
  `git check-ignore -v` on both files) — without copying their content into the repo, both
  audits' evidence would be lost the moment the `tmp/` directory is cleaned. This is why
  preservation under `docs/audits/` is part of this ticket's own scope rather than deferred.
- **`docs/audits/` naming convention**: existing files follow a `D<NN>_<topic>.md` pattern
  (`D01` through `D22`, confirmed via `ls docs/audits/`), each with a frontmatter block
  (`status`/`layer`/`authority`/`audience`/`tags`) and, in sampled files (`D17`), a "Dimension
  Profile" table with `Group`/`Impact`/`Interest`/`Priority` numeric scores tied to a specific
  scoring rubric this session doesn't have applied data for. **Decision**: use the `D23`/`D24`
  numbering and directory placement (genuinely fits — these are audit reports, same as D01-D22),
  but use a lighter "Audit Profile" table (Method/Scope/Posture/Date, matching what the source
  audits themselves already state) rather than fabricate Impact/Interest/Priority scores from a
  rubric never applied to this material — inventing those numbers would imply false precision.
- **Overlap with existing work**: `TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC`'s child ticket
  `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION` already targets the `architecture.md` (6-phase) vs.
  `kernel.md`/`simulation_kernel_contract.md` (7-phase) contradiction. Both new audits
  independently re-discovered this same contradiction (D23 §B, D24 §G) and added two pieces of
  evidence the existing ticket doesn't have: `docs/guides/simulation.md`'s citation of a
  nonexistent `src/engine/authoritative_pipeline.py`, and root `CLAUDE.md`'s own "32-phase" claim.
  Confirmed by reading `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION`'s existing scope — it does
  not currently mention either of these two additional sources. **Decision**: this new evidence
  should amend that existing ticket's scope when it's implemented, not spawn a duplicate ticket.
- **Registered tags**: `documentation`, `architecture`, `engine`, `performance`, `observability`,
  `testing`, `determinism` are all already registered (`python3 tools/tag_registry.py list`,
  checked earlier this session when registering `architecture`) — no new tag registration needed
  for this ticket or its staging artifacts.
- **Registered layer**: `architecture` (registered 2026-07-18: "ADRs and structural/architectural
  decisions") fits this ticket's cross-cutting scope better than any single-subsystem layer
  (`engine`, `observability`, etc.), since the roadmap spans engine, API, observability, and
  testing concerns simultaneously.

## Risks / open items carried forward from the source audits

- Two coverage questions the audits themselves flag as needing a closer look before acting:
  whether `pipeline.py`/`tactical.py` have real dedicated unit coverage or only indirect coverage
  via integration suites, and whether `src/observability/mining/`'s three similarly-named
  orchestration classes are legitimately distinct. Neither was independently re-verified in this
  investigation pass — carried forward as open questions in the epic ticket and roadmap.
- Whether hardware-class (A/B/C) performance budgets are runtime-enforced or configuration-only
  was explicitly flagged by D23 as not fully traced — same treatment, carried forward rather than
  re-investigated here.

## Conclusion

No blocking conflicts, no duplicate epic-level ticket already exists for this scope. The one real
overlap found (Epic C / `AUDIT-ENGINE-DOCS-DRIFT`) is documented as an amendment, not a
duplication. Proceed to scope the epic ticket and roadmap as investigation/prioritization-only,
per the user's explicit instruction not to create detailed tickets for all candidate epics yet.
