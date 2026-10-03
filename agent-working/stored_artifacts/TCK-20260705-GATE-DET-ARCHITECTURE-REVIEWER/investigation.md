---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
artifact_type: investigation
tags: [ai, workflows, determinism, architecture-reviewer]
---

# Investigation — TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER

## Current Behavior

### `.claude/workflows/implement-ticket.js` — Review phase (lines 359-420)

The `agent()` call at line 374 (`agentType: 'architecture-reviewer'`) instructs the agent to read
**only**:
- `staging_artifacts/${tid}/plan.md`
- `staging_artifacts/${tid}/investigation.md`
- `${ticketInfo.ticket_path}` (the ticket file)

`REVIEW_SCHEMA` (line 361) requires `verdict`/`violations`/`parity_entries_affected`/
`mechanics_chapters_to_read`/`summary`/`ts` — no `files_changed`/diff field exists on this schema.
`docs/ai/agents.md:100` independently confirms the same fact in the doc layer: **"Inputs:
`staging_artifacts/{ticket_id}/plan.md` + ticket."**

The Implement phase (`IMPL_SCHEMA`, line 432) — the first point at which `files_changed` exists —
is defined *after* Review returns (line 428, `phase('Implement')`), and only runs if
`review.verdict === 'APPROVED'` (line 404's early-return gate). **Architecture-reviewer today has
zero code to parse.** `plan.md` is markdown prose describing intended files/approach; it is not
Python source and cannot be fed to `ast.parse()`. This is a stronger version of the causality
problem `GATE-DET-PARITY-UPDATER` hit — that ticket at least had a *ledger file* to check (just
not yet edited); here there is no *code* of any kind yet, at any phase, until Implement returns.

### `src/core/state.py` — durable state shape (read in full for dataclass discipline)

Every durable component/state class is `@dataclass(frozen=True, slots=True)` (confirmed at lines
56, 89, 104, 115, 142, and throughout — `AuthoritativeState` L1080, `EntityState` L664, etc.). This
means **direct top-level attribute rebinding (`entity.combat.hp = 5`) already raises
`dataclasses.FrozenInstanceError` at runtime, everywhere in the codebase, not just outside some
designated authoritative path.** A naive AST rule for "attribute assignment on a known state
object" would find this pattern almost nowhere in real code, because it would already have crashed
in any test run that exercised it. Its value is narrow: catching the mistake at review time instead
of at test-run time — real but modest.

### The sanctioned bypass: `object.__setattr__`, and why it's not confined to one file

`src/engine/apply.py`'s own `replace()` helper (lines 7-25, the fast dataclass-copy utility used
throughout the apply path) uses `object.__setattr__` directly to construct replacement objects, and
explicitly resets any field whose name ends in `_cache` to `None` on every replace (lines 19-24) —
confirming `_cache`-suffixed fields are a first-class, deliberately-recognized category of
mutable-via-setattr, non-durable data in this codebase's own convention.

Grepping `object\.__setattr__` across `src/` (excluding tests) turns up 12 files, **not confined to
a single "authoritative pipeline" module**:
`src/core/state.py`, `src/core/models/inventory.py`, `src/simulation_quality/weights.py`,
`src/engine/kernel.py`, `src/engine/spatial_query.py`, `src/engine/apply.py`,
`src/engine/world_index.py`, `src/engine/pipeline.py`, `src/engine/pipeline_phases/actions.py`,
`src/engine/pipeline_phases/movement.py`, `src/world/environment.py`,
`src/engine/domain/view.py`, `src/systems/strategic_systems/intelligence.py`.

Inspecting each call site's target field name shows nearly all of them are cache/derived/transient
fields, not durable simulation truth: `_strongholds_cache`, `_has_hostiles_or_dead_cache`,
`_spatial_grid_cache`, `_occupancy_map_cache`, `_region_list_cache`, `_index_hits`,
`_index_misses`, `world_indexes`, `transient_claims`, `occupancy_snapshot`, `_opt_profile`,
`_force_full_scan`. Two of these call sites (`src/world/environment.py:87`,
`src/systems/strategic_systems/intelligence.py:240`) are **legitimately outside `src/engine/`
entirely** — both populate a cache field on the shared `AuthoritativeState` object from a
non-engine module, which is normal in this codebase's design. A thirteenth file,
`src/simulation_quality/weights.py`, uses the identical `object.__setattr__` idiom on an entirely
unrelated frozen class (`ScoringWeights`, a config/rules object — not durable simulation state at
all).

**Critical finding: `src/engine/authoritative_pipeline*` (the path pattern named in both the idea
doc's table and this ticket's own Scope text) does not exist as a source module.**
`find src/engine -iname "authoritative_pipeline*"` returns nothing. Only
`docs/engine/authoritative_pipeline.md` exists — a conceptual contract document, not a code
boundary. The actual authoritative mutation logic is spread across `src/engine/apply.py`,
`src/engine/pipeline.py`, `src/engine/kernel.py`, `src/engine/pipeline_phases/*.py`,
`src/engine/domain/view.py`, `src/engine/spatial_query.py`, `src/engine/world_index.py` — and, per
the two non-`src/engine/` call sites above, the real boundary is not even a single directory.

**Consequence for the AST scan's design:** there is no clean "inside vs. outside path X" test to
write. A check that flags every `object.__setattr__` call on a state-shaped object outside some
assumed single directory would be almost entirely false positives (most instances are the
sanctioned cache idiom, scattered legitimately across and beyond `src/engine/`), while a check that
allowlists every current legitimate call site would only catch violations in genuinely new
locations — an ongoing allowlist-maintenance burden that must be disclosed, not hidden.

### The higher-value, harder-to-catch real violation surface: mutating nested mutable containers

Frozen dataclasses only block *rebinding* their own top-level fields — they do **not** protect the
contents of a mutable attribute. `InventoryComponent.items: List[ItemStack]` (confirmed
`src/core/models/inventory.py:42`) is a plain mutable `list`; nothing stops
`entity.inventory.items.append(x)` from outside the authoritative path, and it would not crash.
Some `Dict`-typed fields (e.g. via `_readonly_mapping`/`ReadOnlyDict`, `src/core/state.py:36-40`)
raise `ReadOnlyError` on `__setitem__`/`__delitem__` at runtime — a real backstop for *those*
fields — but `AuthoritativeState.global_resources: Dict[str, float]` (line 1124) is stored as a
plain dict by default and only frozen via `shallow_freeze`/`ReadOnlyDict` wrapping at specific
points (line 1233) — not universally guaranteed at every call site. **This is the actual highest-
value target for a static check** (a real gap with no runtime backstop in the general case), but it
is also the hardest to detect via plain `ast` module inspection: without type inference, the AST
cannot know that `x.items.append(...)` refers to `InventoryComponent.items` versus an unrelated
list attribute on some other object. A workable first pass can only match by **attribute-name
heuristic** against a small, explicitly-maintained list of known mutable state-bearing field names
mined from `src/core/state.py`/`src/core/models/inventory.py` (e.g. `.items`, `.global_resources`,
`.trust_history`) — necessarily incomplete (any renamed or newly-added mutable field is invisible
until the list is updated) and subject to name collisions with unrelated objects.

### `src/api/` — presenter/read-model convention (confirmed to exist and be consistent)

- `src/api/presenters/*.py` (`state_presenter.py`, `campaigns.py`, `chronicle.py`, `decisions.py`,
  `economy.py`, `scenarios.py`): every class is named `*Presenter`; every method is
  `@staticmethod present_*(state: AuthoritativeState/EntityState/RegionState) -> Dict[str, Any]`.
  The **input** parameter is typed as the raw domain object; the **return** annotation is always
  `Dict[str, Any]` — confirmed by reading `state_presenter.py` in full (`StatePresenter.present_full`,
  `.present_entity`, `.present_region`, all `-> Dict[str, Any]`). `state_presenter.py`'s own
  docstring states the law explicitly: `"M12 Law: API presenters MUST NOT mutate authoritative
  state."`
- `src/api/schemas.py`: `TypedDict` response classes named `*Response`
  (`WorldStateResponse`, `EntityPageResponse`, `EntityDetailResponse`) used as
  `response_model=` targets for the four highest-risk inline routes in `src/api/server.py`. The
  module's own docstring discloses a known, already-tracked gap: `Dict[str, Any]` is used as a
  "typed placeholder" for the remaining actionable inline routes pending full Pydantic
  contract-testing (`open_audit_findings_backlog §1G`) — an existing, disclosed limitation this
  ticket should not re-litigate.
- `src/api/routes/*.py`: most files are real route modules with handlers returning `Dict[str, Any]`
  or a `*Response` type (e.g. `economy.py:28` `-> Dict[str, Any]`, `campaigns.py:96`
  `-> CampaignHistoryResponse`). Three files are 0-byte stubs (`control.py`, `health.py`,
  `state.py`) — actual inline routes for `/api/v1/state` etc. live directly in `server.py` (per
  `schemas.py`'s own docstring: "Response schemas for `src/api/server.py` inline routes"). One
  private helper, `decisions.py:40` `_get_index(run_id: str) -> DecisionTraceIndex`, returns a
  non-`Response`/non-`Dict` type — but it is a leading-underscore internal helper, not a registered
  route handler, and must be excluded from the check's scope (it is never returned to an API
  caller directly).

**Confirmed: a real, consistent, mechanically-checkable naming convention exists** —
`*Presenter`/`*Response`/`Dict[str, Any]` on one side, raw domain classes defined in
`src/core/state.py`/`src/core/strategic.py`/`src/core/self_model.py`/`src/core/models/*.py` on the
other. Zero route/presenter function anywhere in `src/api/` was found returning a raw domain class
type directly. **Caveat:** many handlers have **no return-type annotation at all** (plain
`async def get_x(...):` with no `-> ...`) — a type-annotation-based static check is blind to those;
it can only flag an annotation that is *present and wrong*, not the (more common) case of an
unannotated handler that happens to return a raw model at runtime. That residual gap needs a
runtime/dynamic check to close and is out of scope for a static `ast` pass.

## Mechanics / Engine Constraints

None from `docs/mechanics/` — this ticket is agent-workflow tooling (`.claude/`, `tools/`), not
simulation formula logic. The relevant constraints are architectural, from CLAUDE.md's Durable
State Rule and Architecture Rule, and from `docs/engine/authoritative_pipeline.md` /
`docs/engine/authoritative_mutation_pipeline_contract.md` (both read; both describe the mutation
*sequence* conceptually — neither names a single `src/` module boundary the way the idea doc's
table assumed).

## Parity Ledger Overlap

- **`INFRA-204`** (`docs/parity_ledger/infrastructure.yaml:2312`, status `verified`, priority `P1`):
  "AuthoritativeState (src/core/state.py) does not import from `src/engine/` at module or instance
  level... `support_boundary: "src/core/ — no upward imports to src/engine/ permitted."`" — the
  closest existing parity entry to this ticket's concern: it encodes an *import-direction* boundary
  (state must not depend upward on engine), which is adjacent to but distinct from "engine code must
  not mutate state from outside the authoritative path" (a *mutation-direction* boundary). No
  existing entry covers the mutation-direction rule itself. Recommend Plan flag whether a new
  parity entry should be added once the static check exists, or whether this stays purely an
  agent-workflow-tooling concern outside the ledger's scope (the ledger tracks legacy-vs-V2
  behavioral parity, not agent-tooling coverage — leaning toward the latter, but not asserting it
  here).
- No P0 entries directly implicated by this ticket's own scope (it builds review tooling, not
  simulation behavior).

## Prior Work

- **`stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/`** — established shared module shape:
  `tools/gate_checks/done_checker_static.py`, plain functions returning `(status, evidence)`
  tuples, aggregated by `run_*()` returning `list[dict]`; a Part A / Part B split for pre- vs.
  post-Finalize checks, invoked via `bash()` calls from two different `implement-ticket.js` call
  sites (not one). `DONE_SCHEMA` gained `verified_by`.
- **`stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/`** — hit the **same class of
  causality problem** this ticket faces (its investigation.md Risk 4, "Causality/timing issue").
  Resolution adopted: split the check into a pre-step (`expected_subsystems_for_files`, runs before
  the `parity-updater` `agent()` call, using only the diff that already exists — `files_changed`)
  and a post-step (`cross_reference_touched`, runs after the agent call returns, via `bash()`,
  mirroring `run_finalize_selfcheck`'s pattern). **Directly transferable precedent**, though this
  ticket's version is more extreme: Parity's pre-step could run early because a diff already
  existed by then (Parity is a post-Implement phase); Review's pre-step has **no diff at all**
  because Review itself is pre-Implement — so unlike Parity, there is no meaningful "part that
  genuinely can run first" for architecture-reviewer's static checks. See Risks below.
- **`tools/gate_checks/mechanics_auditor_static.py`** — third sibling, confirms the same
  conventions (plain functions, `(status, evidence)` tuples, no CLI/argparse, imports the parity
  path-mapping module rather than re-deriving one).
- **`tests/tools/test_parity_updater_static.py`** (and the done-checker/mechanics-auditor
  equivalents) — establish the test-file location (`tests/tools/test_<module>.py`) and the
  coverage-honesty pattern (one positive-control fixture per check function, imports directly from
  `tools.gate_checks.<module>`, no pytest marker).

## Risks and Open Questions

1. **[BLOCKS PLAN — surfaced per ticket's own Assumptions] Where does the AST/grep static check
   actually run, given architecture-reviewer's Review phase runs before Implement and has no code
   to parse?** Recommend (not decided here — this changes pipeline ordering, matching the
   ticket's own flagged concern) mirroring `GATE-DET-PARITY-UPDATER`'s resolution: add a **new,
   separate post-Implement call site** (via `bash()`, using `implementation.files_changed`) rather
   than modifying the existing pre-Implement `agent()` call's prompt. The AC wording "instructs
   architecture-reviewer to run these checks first" cannot be satisfied literally at the *original*
   Review call site — there is nothing to check yet. Two candidate designs for Plan to choose
   between, neither decided here:
   (a) invoke `architecture-reviewer` a **second time**, post-Implement, against the real diff, with
   the static checks as its own "Step 0" (mirrors how `done-checker`'s prompt runs its static
   pre-check as Step 0 before judging by hand) — this doubles the LLM cost per ticket but keeps one
   agent owning the concern end-to-end; or
   (b) fold the static-check output into the **existing Security-Review phase** (already runs
   post-Implement, per `implement-ticket.js:668`) as additional context, with a FAIL still
   downgrading to `NEEDS_CHANGES`/`BLOCKED`. Recommend Plan read the Security-Review phase's own
   prompt/schema before deciding between (a) and (b) — not read in this investigation pass, out of
   this ticket's stated Related Code Areas, but relevant to resolving this open question.
2. **No single "outside the authoritative pipeline" path exists to check against** —
   `src/engine/authoritative_pipeline*` does not exist as a source module (confirmed above); the
   real boundary is a set of ~9 files across and slightly beyond `src/engine/`. The check's `FAIL`
   condition must therefore be built from an explicit, disclosed allowlist of known-legitimate call
   sites/field-name patterns (the `_cache` suffix convention, plus a short named-exception list),
   not a directory-prefix test. This allowlist will need updating as new legitimate cache-population
   sites are added — a real, ongoing maintenance cost that must be stated as a limitation, not
   silently absorbed.
3. **The highest-value violation (nested mutable-container mutation bypassing frozen dataclasses)
   is also the hardest to detect precisely.** A name-based heuristic (matching `.items`,
   `.global_resources`, and similar known field names) is the only workable `ast`-only approach;
   it will miss any violation on a differently-named or newly-added mutable field, and can
   false-positive on an unrelated object that happens to share an attribute name. This must be
   disclosed explicitly in the check's own docstring, per the ticket's own preference for "a first
   version that catches only the clearest violations... over an over-ambitious one that's
   unreliable."
4. **Zero real historical precedent for the reason/metadata-smuggling pattern.** Searched
   `git log --all --grep`, `tickets/done/`, `docs/archive/`, and all 31 recorded
   `NEEDS_CHANGES`/`BLOCKED` architecture-review verdicts in `agent-monitoring/events.jsonl` (the
   actual historical corpus of confirmed findings). Every "smuggl*" hit found (7 total, in
   `tickets/done/TCK-20260420-RESOURCE-PHASE4-HIGH-LEVEL.md` and 5 files under `docs/archive/`) uses
   "smuggle" in the sense of **scope creep** ("don't smuggle a whole economy into this narrow
   milestone") — a different meaning entirely from CLAUDE.md's Durable State Rule concern (durable
   *meaning* encoded in a `reason`/`metadata` *string* instead of a typed field). None of the 31
   real Review-phase failures cite a reason/metadata-string violation; the closest adjacent real
   finding is `TCK-20260619-E53Aa-FACTION-STATE`'s "`to_readonly()` must wrap factions with
   ReadOnlyDict" — an unwrapped-mutability finding, not a string-smuggling one. One older,
   thematically-related but not pattern-identical concern exists
   (`docs/archive/thinking_high_level_implementation.md:16`, flagging ad hoc intent smuggled through
   `goal_scores`/`last_goal`/mood fields — which did motivate the real `src/core/strategic.py`
   typed-state layer now in place) but it is about ad hoc *fields*, not `reason`/`metadata`
   *string parsing*. **This check has zero empirical grounding in this repo's history** — it must
   be built from CLAUDE.md's/`architecture-reviewer.md`'s own rule prose, and disclosed plainly as
   speculative/preventive rather than evidence-derived. This is the weakest-evidenced of the three
   checks and should carry the strongest precision/recall caveat.

## Anti-Drift Hazards

- Do not assume `src/engine/authoritative_pipeline*` is a real path and write a check against a
  glob that matches nothing — confirmed it does not exist; any "inside/outside path" framing must
  use an explicit file list, not a glob.
- Do not treat every `object.__setattr__` call as a violation — most are the sanctioned
  `_cache`-suffix idiom; a naive version of this check would fail on the codebase's own existing,
  correct code (a hostile false-positive rate), which the ticket explicitly says to avoid.
- Do not re-decide `status: verified`/`divergent` semantics or Mechanics Bible compliance judgment —
  stays LLM-judged per ticket Out of Scope.
- Do not fold this module into `lane-architecture`'s pytest marker (SEQUENCE.md decision 1) — new
  sibling module `tools/gate_checks/architecture_reviewer_static.py`, same shape as the three DONE
  siblings.
- Do not invent a corpus of confirmed reason/metadata violations that doesn't exist — state plainly
  in the module docstring that this check's patterns are rule-derived, not incident-derived.
- Do not scope the API-boundary check to *every* function in `src/api/` — must exclude
  leading-underscore private helpers (confirmed real example: `decisions.py:_get_index`), or it
  will false-positive on internal-only code that never reaches an API caller.
- The two `object.__setattr__` call sites legitimately outside `src/engine/`
  (`src/world/environment.py:87`, `src/systems/strategic_systems/intelligence.py:240`) are real,
  correct code populating a cache field on `AuthoritativeState` — do not let a directory-prefix
  check flag them.
