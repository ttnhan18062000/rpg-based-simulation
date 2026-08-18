---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION

## Architecture Review Corrections

**This section records a Review-mandated correction, not an implementer-discovered deviation.**
Architecture Review returned `NEEDS_CHANGES` on the first pass of this plan, on exactly one point:
Step 5 / New Test 11 (`test_no_junction_table_or_new_sqlite_table_introduced_by_this_ticket`)
asserted `source.count("CREATE TABLE") == 5` as "the real, currently-confirmed count." Review
independently re-ran the grep against the live `tools/retrieval_cache.py` and found the plan's
enumeration undercounted the real DDL statements (missed `retrieval_cache_generation` at line 265,
a genuine `CREATE TABLE` inside `migration_001_add_level2_tables()`) and that a plain substring
count also picks up 3 more hits inside docstrings/comments (lines 257, 312, 668 — prose mentioning
"CREATE TABLE," not SQL). As written, the assertion would have failed immediately against the
current, unmodified file, before this ticket's own diff even lands.

This session re-verified both of Review's numbers by direct execution against the live file (not by
trusting Review's citation) — confirmed: **6** real `CREATE TABLE IF NOT EXISTS` DDL statements
(the three legacy marker-only tables at `:207`/`:221`/`:237`, `retrieval_cache_generation` at
`:265`, the Level 1 table at `:273`, the Level 2 table at `:326`), and **9** for the plain
`source.count("CREATE TABLE")` substring count (the 6 real statements plus 3 comment/docstring
occurrences at `:257`, `:312`, `:668`).

Going further than Review's own literal suggestion required: this session also directly executed
Review's proposed regex, `re.findall(r'CREATE TABLE IF NOT EXISTS \w+', source)`, against the live
file rather than assuming it would return 6. **It does not — it returns 8.** Two of the three
comment/docstring occurrences (`:257`, `:312`) are phrased as the literal string `"CREATE TABLE IF
NOT EXISTS only — additive, never..."` inside migration_001's and migration_002's own docstrings —
"only" is itself a `\w+` token, so Review's suggested pattern matches those two false positives
too, alongside the 6 real statements (8 total), not the 6 Review's own framing implied. Only the
third comment occurrence (`:668`, `"...CREATE TABLE) — the caller's..."`, no `IF NOT EXISTS`
following) is excluded by that pattern.

**Corrected mechanism adopted (Option (a), strengthened):** match DDL statements only, requiring an
opening `(` after the table name to exclude the docstring landmines that share the literal `CREATE
TABLE IF NOT EXISTS <word>` shape:

```python
import re
matches = re.findall(r"CREATE TABLE IF NOT EXISTS \w+\s*\(", source)
assert len(matches) == 6
```

Verified directly against the live file this session: this exact pattern returns exactly 6 matches,
none of them the two docstring landmines. This is the more robust of Review's two offered options
(matching real DDL, not comment-text-coupled substring counting) and is additionally hardened
against the specific landmine Review's own literal regex suggestion did not account for. `test_plan.md`
was checked for a restated assertion of this test; it states the qualitative requirement only ("no
new `CREATE TABLE` statement beyond `migration_002_add_level2_tables()`'s existing single table")
with no hardcoded number, so it required no correction and is left unchanged.

DD1 and DD4 were both independently confirmed correct by Architecture Review and are **not**
re-derived, re-litigated, or modified anywhere below. Steps 1-4 and Step 6 are unchanged from the
prior version of this plan.

## Summary

This ticket adds two new, additive pieces of pure logic on top of two already-real modules, and
wires neither into a live call path (that is explicitly the next ticket's job):

1. **`PacketAssembly.evidence_dependencies: list[str]`** — a new field on the dataclass
   `tools/knowledge_gateway_packet_assembly.py::PacketAssembly` (`:617-633`), computed by a new
   helper `_evidence_dependencies()` and wired into `assemble_packet()`'s return (`:646-745`).
2. **`revalidate_context_packet_row()`** — a new sibling orchestrator function in
   `tools/knowledge_gateway_cache.py`, placed alongside the existing `revalidate_cache_row()`
   (`:204-219`), reusing `is_branch_compatible()` (`:191-193`) and
   `working_tree_overlap_forces_revalidation()` (`:196-201`) by direct, unmodified call — plus one
   small new adapter helper, `_level2_repo_branch_scope()`, to reconstruct the combined
   `repository_id::branch` string `is_branch_compatible()` expects from Level 2's split columns
   (investigation.md Risk 3).

Both pieces are independently unit-testable without a live Level 2 storage/lookup path, because
neither this ticket's Scope nor its Out of Scope asks for one (that path does not exist yet —
confirmed by direct read of `tools/retrieval_cache.py`: `LEVEL2_CACHE_COLUMNS`/
`migration_002_add_level2_tables()` exist, but no `check_*_cache()`/`write_*_cache()` function
against `retrieval_context_packet_cache_rows` exists anywhere in the module, and this ticket's own
Out of Scope forbids adding one).

This plan makes one deliberate, cited **correction to investigation.md's stated implementation
approach** (DD1 below: the aggregation source is `final_context`, not `final_evidence` as
investigation.md suggested) and one **new design decision investigation.md did not examine** (DD4
below: how the revalidation function behaves when `select_validation_basis()` returns `"FINER"` at
Level 2, where no fingerprint column exists to support that branch). Both are flagged explicitly for
Architecture Review scrutiny in "Flagged for Architecture Review" below, with two Plan-derived tests
added beyond `test_plan.md`'s enumerated 12 to cover the behavior each one controls.

No schema/table change (`tools/retrieval_cache.py` stays byte-unchanged). No `check_*_cache()`/
`write_*_cache()` function added. No `_run_knowledge_context()` wiring. No junction table. No
semantic/fuzzy matching. `tools/knowledge_gateway_router.py` stays byte-unchanged.

## Design Decisions

### DD1 — Aggregation source: `final_context`, not `final_evidence` (correction to investigation.md, cited)

**investigation.md's claim** (Current Behavior, "Direct answer to Investigate Question 3, part A"):
`{e.path for e in final_evidence if e.path}` — over `PacketAssembly.evidence` — "already IS the
'aggregated from the dependencies of every provider result the packet assembled' set the ticket's
own Scope asks for; nothing upstream of it needs to change."

**Read directly, not inferred — this claim is incomplete.** `assemble_packet()`
(`tools/knowledge_gateway_packet_assembly.py:646-745`) computes `final_context`/`final_evidence` in
two branches, verified by direct trace of both (`:697-707`):

- **Ordinary branch** (`else`, `:704-708`, `budget_assembly_failed` is `False`):
  `final_context = [c for c in context_entries if c.source_id in included_evidence_ids]` and
  `final_evidence = [e for e in evidence_entries if e.evidence_id in included_evidence_ids]`. Since
  `render_candidates()` (`:245-333`) builds `ContextEntry`/`EvidenceEntry` in the same loop
  iteration with `c.source_id == e.evidence_id` and `c.path == e.path` for every result (confirmed:
  `path=source_path` on both at `:282`/`:291` for `context_search`, `path=None` on both at
  `:319`/`:328` for `graphify`), `final_context` and `final_evidence` select the **identical**
  subset and yield the identical `{...path...}` set in this branch. This is why
  `test_plan.md`'s test 2 (budget-truncation exclusion) passes identically regardless of which of
  the two this plan aggregates over — that test never reaches the branch below.
- **§16 budget-assembly-failure branch** (`if budget_assembly_failed:`, `:698-702`):
  `final_context: list[ContextEntry] = []` (explicitly emptied) but
  **`final_evidence = evidence_entries`** — the full, *unfiltered* list every provider result
  produced, deliberately left un-narrowed by the sibling DEDUP-BUDGET ticket's own design (its own
  plan.md DD3 branch trace documents this as intentional — full evidence visibility even when no
  statement survived budget assembly). In this one branch, `final_context` and `final_evidence`
  **diverge**: `final_context` is empty (consistent with `final_statements = []`,
  `answer = ""`), `final_evidence` is not.

**Why this matters for this ticket specifically.** AC1's own wording requires the aggregated set to
be "not merely a superset copy of every source ever consulted." If `evidence_dependencies` were
computed from `final_evidence` per investigation.md's suggestion, then in the §16 branch — where the
packet's own `answer`/`statements`/`context` are all empty — `evidence_dependencies` would still be
the full, unfiltered path set of every provider result ever returned for that request: literally the
superset AC1 forbids, for that one code path. No test in `test_plan.md`'s enumerated 12 exercises
this branch, so this would have shipped unnoticed.

**Decision:** compute `evidence_dependencies` from **`final_context`**, not `final_evidence`. This
is a one-line change of which already-computed list to read (`final_context` is already computed at
the exact same point `final_evidence` is, in both branches) and is correct in both branches by the
same construction the sibling ticket already established for `final_context`/`final_statements`/
`answer`: empty when the packet's answer is empty, filtered to the real included set otherwise. It
is also the more literal reading of the ticket's own Scope wording ("the packet's answer **and
context items** actually depend on") and a closer structural mirror of Level 1's own precedent
(`tools/knowledge_gateway_cache.py:311-312`: `source_paths` is derived from `response.get("context",
[])`, i.e., context entries — not from an "evidence" field, which Level 1's response shape does not
even have).

**New helper**, placed immediately above `assemble_packet()`:

```python
def _evidence_dependencies(context_entries: list[ContextEntry]) -> list[str]:
    """Aggregates the packet's real dependency-path set for the Level 2 evidence_dependencies
    column, from the packet's own final `context` items (post-dedup, post-budget-truncation) --
    NOT from `evidence` (`final_evidence`). The two carry identical .path values for every
    context_search-sourced result in the ordinary/truncated branches (same source_id/evidence_id
    filter -- verified by direct trace of render_candidates()/assemble_packet()), but diverge in
    the section-16 budget-assembly-failure branch, where final_context is correctly emptied
    (matching the packet's own empty answer/statements) while final_evidence is deliberately left
    as the full, unfiltered evidence_entries list. Reading final_context keeps
    evidence_dependencies consistent with what the packet actually claims, in every branch,
    without any branch-specific special-casing here. graphify-sourced entries carry path=None
    (symbol-kind evidence is not path-tracked by this module at all, matching Level 1's own
    identical limitation) and contribute nothing -- not a crash, not a literal "None" string.
    """
    return sorted({c.path for c in context_entries if c.path})
```

Called in `assemble_packet()`, after `final_context` is computed (both branches), alongside the
existing `provenance_providers` computation (`:721-725`):

```python
evidence_dependencies = _evidence_dependencies(final_context)
```

**`PacketAssembly` field insertion** — one new required (non-defaulted) field, placed after
`evidence`, before `conflicts` (keeps every defaulted field, i.e. only `negative_claim_support`,
trailing — Python dataclass field-ordering rule):

```python
@dataclass(frozen=True)
class PacketAssembly:
    status: str
    freshness: str
    verification: str
    provenance_providers: list[str]
    providers_consulted_this_call: list[str]
    answer: str
    statements: list[Statement]
    context: list[ContextEntry]
    evidence: list[EvidenceEntry]
    evidence_dependencies: list[str]
    conflicts: list[Conflict]
    budget_requested: int
    budget_returned: int
    budget_truncated: bool
    omitted_statement_count: int
    provider_failures: list[str]
    negative_claim_support: Optional[NegativeClaimSupport] = None
```

**Other constructors of `PacketAssembly` (enumerated, per fact-verification requirement, re-checked
this session, not trusted from the sibling ticket's own prior claim):** `grep -n "PacketAssembly("
tools/knowledge_gateway_packet_assembly.py` returns exactly one hit — the `return PacketAssembly(...)`
statement inside `assemble_packet()` (`:727-744`). `grep -n "PacketAssembly("
tests/tools/test_knowledge_gateway_packet_assembly.py` returns **zero** hits — every one of the 38
existing tests reaches `PacketAssembly` only via `assemble_packet()`. Adding one new required field
therefore breaks no existing construction site. `test_packet_never_carries_raw_provider_results_
verbatim_beyond_rendered_statements` (`:176-186`) iterates `dataclasses.fields(packet)` but only
asserts specific forbidden names (`"raw_provider_results"`, `"raw"`) are absent — it is not an
exact-set/count assertion, so it does not need updating.

### DD2 — `working_tree_fingerprint`: not populated by this ticket (Risk 1, resolved)

**Read directly, not inferred.** `tools/retrieval_cache.py:326-355` (`migration_002_add_level2_
tables()`'s real DDL) declares `working_tree_fingerprint TEXT` — **nullable, no `NOT NULL`**
(confirmed by direct read; contrast `evidence_dependencies TEXT NOT NULL` at the same DDL block,
line 336, and `provider_generations TEXT NOT NULL`, line 343). Leaving this column `NULL` is
therefore schema-legal, not a constraint violation this ticket must work around.

**Decision: this ticket does not populate or read `working_tree_fingerprint`, in either of its two
new functions.** Reasoning:
1. No cited doc (`evidence_cache_identity_contract.md`, `cache_migration_plan.md`, the schema
   ticket's own artifacts, the proposal) defines what value this column should hold or how it would
   differ from the `changed_paths`-intersection mechanism `evidence_dependencies` already provides —
   confirmed by investigation.md's own citation search and re-confirmed here (no new hit from this
   session's `search_docs`/`graphify` re-verification either).
2. §5 rule 3's own text (`evidence_cache_identity_contract.md:159-171`, read in full this session)
   frames `changed_paths` intersection as the *replacement for*, not a supplement to, whole-tree
   fingerprinting: "Rather than hashing the entire working tree on every request, the gateway
   intersects the caller-supplied `changed_paths` set against the set of file paths a cached
   packet's evidence actually depends on." `evidence_dependencies` (this ticket's new field) plus
   `working_tree_overlap_forces_revalidation()` (already reused, unmodified) is the complete,
   sufficient mechanism §5 describes — nothing about it depends on a separate stored fingerprint
   value.
3. This ticket ships **no write function** for the table at all (Out of Scope, confirmed:
   `tests/tools/test_retrieval_cache.py::TestLevel2Migrations::test_no_actual_read_write_functions_
   added_for_the_new_level2_table` must keep passing per `test_plan.md`'s Regression Surface) — so
   there is no `INSERT` statement in this ticket's own diff that could populate the column either
   way. The question is genuinely moot at the *mechanism* level for this ticket: neither new
   function this ticket adds needs to write or read `working_tree_fingerprint`.
4. `revalidate_context_packet_row()` (DD3 below) therefore never references `row["working_tree_
   fingerprint"]` at all, mirroring `revalidate_cache_row()`'s own precedent of never reading
   `head_commit` (test 8, `test_revalidate_context_packet_row_survives_new_commit_alone_unchanged_
   generations`, asserts this directly for the new function).

**Handoff note for the read-write-wiring ticket** (not this ticket's obligation, recorded so it is
not silently forgotten): if a future ticket decides this column needs a real producer, that is a new
decision requiring its own citation — this ticket does not pre-empt it either way.

### DD3 — `revalidate_context_packet_row()`: signature, composition, and the branch-check-first ordering constraint

**Load-bearing structural difference from Level 1.** In the real Level 1 code,
`is_branch_compatible()` is called by the **orchestrator** (`perform_cache_lookup()`,
`tools/knowledge_gateway_cache.py:237`), *before* `revalidate_cache_row()` is even invoked —
`revalidate_cache_row()` itself (`:204-219`) never calls `is_branch_compatible()` internally. Level 2
has no equivalent lookup orchestrator yet (Out of Scope — that is the wiring ticket's job), so this
ticket's single new function must perform **both** the branch check and the working-tree/generation
checks itself, in the §5-rule-2-mandated order (branch check strictly first, "before any fingerprint
comparison is even consulted") — this is exactly what `test_plan.md` test 7
(`test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies`) requires
via its "call-order mechanism ... branch check runs before any fingerprint/generation comparison is
even consulted" wording.

**New adapter helper** (investigation.md Risk 3 — the reconstruction the caller needs to bridge
Level 2's split `repository_id`/`branch` columns into `is_branch_compatible()`'s single
combined-string shape), placed immediately above `revalidate_context_packet_row()`:

```python
def _level2_repo_branch_scope(repository_id: str, branch: str) -> str:
    """Single named helper for the repository_id/branch -> combined-scope-string reconstruction
    is_branch_compatible() expects (investigation.md Risk 3) -- same "::" join format
    _current_repo_branch_scope() already uses for Level 1 (f"{repo_root}::{branch}"), so a Level 2
    row written under one format and compared under a differently-shaped reconstruction can never
    silently fail to match. Not the same function as _current_repo_branch_scope() -- that one
    performs a live `git branch --show-current` subprocess read; this one is a pure string join
    over caller-supplied values, since Level 2's row/current identity is supplied by the caller
    (DD3), never queried internally by this module.
    """
    return f"{repository_id}::{branch}"
```

**New orchestrator function**, placed immediately after `revalidate_cache_row()` (`:204-219`), as a
new "Step 9" section (matching this module's existing convention of a numbered section comment per
plan-step addition, e.g. `# --- Step 5 ---`, `# --- Step 7 ---`):

```python
def revalidate_context_packet_row(
    row: dict, *, capability_descriptor: dict,
    current_provider_generations: dict[str, str],
    current_repository_id: str, current_branch: str,
    changed_paths: list[str],
) -> bool:
    """True = still valid (packet may be served as a genuine HIT). False = stale (treat as MISS).
    Level 2 sibling to revalidate_cache_row() (§5) -- consumes only a stored row dict (never a live
    PacketAssembly; tools/knowledge_gateway_packet_assembly.py is not imported here, guarded by
    test_module_does_not_import_knowledge_gateway_router_or_packet_assembly). Unlike Level 1, this
    function performs the branch-compatibility check itself (DD3) -- no Level 2 lookup
    orchestrator exists yet to do it first.
    """
    row_scope = _level2_repo_branch_scope(row["repository_id"], row["branch"])
    current_scope = _level2_repo_branch_scope(current_repository_id, current_branch)
    if not is_branch_compatible(row_scope, current_scope):
        return False  # §5 rule 2 -- hard partition, checked before any other comparison.

    if working_tree_overlap_forces_revalidation(row["evidence_dependencies"], changed_paths):
        return False  # §5 rule 3.

    basis = select_validation_basis(capability_descriptor)
    if basis != "PROVIDER_GENERATION":
        # DD4 -- Level 2's schema carries no evidence_fingerprints-equivalent column to support
        # §4's finer-grained comparison. Fail closed (force revalidation) rather than assume
        # validity without the data to prove it. Unreachable with both real providers today (both
        # report fine_grained_fingerprints: False -- see Risk 4 / test_provider_generation_
        # fallback_used_for_both_real_providers_today).
        return False

    row_generations: dict[str, str] = json.loads(row["provider_generations"])
    for provider_id, stored_generation in row_generations.items():
        if current_provider_generations.get(provider_id) != stored_generation:
            return False  # §5 rule 1, per-provider (Investigate Question 2's dict-shaped finding).
    return True
```

**Other readers/writers of `row["evidence_dependencies"]`/`row["provider_generations"]`/
`row["repository_id"]`/`row["branch"]` (enumerated, per fact-verification requirement):** none exist
yet, anywhere in the repo — confirmed by `grep -rn "repository_id\"\]\|provider_generations\"\]"
tools/ tests/` returning no hits outside this plan's own new code. No live producer of a Level 2
`row` dict exists (the read-write-wiring ticket's job); this ticket's own new tests are the first and
only callers, constructing the row dict directly (per `test_plan.md` tests 5-10's own stated
approach). `row["evidence_dependencies"]` is a JSON-encoded string (the `evidence_dependencies TEXT
NOT NULL` column), passed to `working_tree_overlap_forces_revalidation()` exactly as-is — that
function's own `json.loads()` call handles the decode, mirroring how `revalidate_cache_row()` passes
`row["working_tree_overlap"]` through unchanged (`:210`). `row["provider_generations"]` is likewise a
JSON-encoded string (the `provider_generations TEXT NOT NULL` column, dict-shaped per §10.3) —
`revalidate_context_packet_row()` is the one place in this ticket's diff that calls `json.loads()` on
it.

**Return-type discipline (§3 Non-collapse rule):** bare `bool`, exactly like `revalidate_cache_row()`
— never a `freshness`/`verification` field, satisfied by construction (every `return` statement in
the function body returns a literal `bool`).

### DD4 — Flagged for Architecture Review: fail-closed default when `select_validation_basis()` returns `"FINER"` at Level 2

Not examined by investigation.md (a genuinely new finding surfaced by this session's own direct
trace of `revalidate_cache_row()`'s `"FINER"` branch, `:219`: `return row["evidence_fingerprints"] ==
current_evidence_fingerprint`). Level 1 can answer this comparison because its row has an
`evidence_fingerprints` column; **Level 2's `LEVEL2_CACHE_COLUMNS` has no equivalent column at all**
(confirmed by direct read, `tools/retrieval_cache.py:154-185`) — there is no schema-legal way for
`revalidate_context_packet_row()` to perform the literal comparison Level 1 performs in this branch.

Three alternatives were considered:
- **(a) Fail closed — adopted.** Treat `"FINER"` as "cannot verify with the data this schema
  provides" and return `False` (force revalidation). Safe default: never silently serves a packet as
  valid without the data to prove it. Costs nothing today (unreachable with both real providers,
  confirmed by direct read of `provider_capabilities_context_search.json`/
  `provider_capabilities_graphify.json`, both `fine_grained_fingerprints: false`).
- **(b) Fail open (assume `True`).** Rejected — this would silently serve a packet as valid in
  exactly the case §4 exists to guard against once a future provider does advertise
  `fine_grained_fingerprints: True`, defeating the rule's own purpose rather than merely leaving it
  unimplemented.
- **(c) Raise `NotImplementedError`.** Rejected as disproportionate — a future provider onboarding
  should not crash the caller's request; failing closed (miss, refresh) is the same practical outcome
  with graceful degradation instead of an unhandled exception.

**This is flagged for Architecture Review, not silently decided** — it is a genuinely new
safety-relevant branch with no existing test in `test_plan.md`'s enumerated 12 covering it. A new
test is added in Step 5 to cover it (see below), and the Implementer must not remove or weaken this
branch's fail-closed behavior without an explicit Architecture Review sign-off, since it directly
governs a §4 hard-rule branch this repo's own `evidence_cache_identity_contract.md` treats as
binding.

## Steps

### Step 1 — Add `evidence_dependencies` field + `_evidence_dependencies()` helper; wire into `assemble_packet()`

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Per DD1. Add the new module-level helper `_evidence_dependencies(context_entries:
list[ContextEntry]) -> list[str]` (exact body in DD1 above) immediately above `assemble_packet()`
(before `:646`). Add `evidence_dependencies: list[str]` as a new field on `PacketAssembly`
(`:617-633`), placed after `evidence`, before `conflicts` (exact field list in DD1 above). In
`assemble_packet()`, after `final_context`/`final_evidence` are computed in both branches of the
`if budget_assembly_failed:` block (`:697-708`), add `evidence_dependencies =
_evidence_dependencies(final_context)` — placed alongside the existing `provenance_providers = ...`
computation (`:721-725`), after both are in scope. Add `evidence_dependencies=evidence_dependencies,`
to the final `return PacketAssembly(...)` statement (`:727-744`), positioned to match the field's
dataclass position (between `evidence=final_evidence,` and `conflicts=conflicts,`).

**Do NOT touch:** `EvidenceEntry`/`ContextEntry`'s own field definitions (`:216-232`) — unchanged.
Do not compute `evidence_dependencies` from `evidence_entries`/`final_evidence` (DD1's explicit
correction). Do not change `render_candidates()`, `deduplicate_statements()`,
`_conflict_signal_index_pairs()`, `assemble_within_budget()`, or `build_conflicts()` — none of this
ticket's logic depends on or alters dedup/conflict/budget behavior, only reads their
already-computed `final_context` output.

**Verify:** `test_evidence_dependencies_aggregated_from_packet_evidence_paths`,
`test_evidence_dependencies_excludes_paths_from_omitted_budget_truncated_statements`,
`test_evidence_dependencies_omits_graphify_symbol_evidence_with_no_path` (all `test_plan.md`, New
Tests 1-3); plus **new, Plan-derived**
`test_evidence_dependencies_empty_in_section16_budget_assembly_failure_not_full_unfiltered_evidence`
(not in `test_plan.md`'s enumerated 12 — added per DD1's correction; asserts a budget too small to
admit even the single lowest-cost statement produces `packet.evidence_dependencies == []`, not the
full unfiltered path set `final_evidence` would give); plus full regression:
`tests/tools/test_knowledge_gateway_packet_assembly.py` (all 38 existing tests, including
`test_packet_never_carries_raw_provider_results_verbatim_beyond_rendered_statements`, which does not
need updating per DD1's field-enumeration check).

### Step 2 — Add `_level2_repo_branch_scope()` adapter helper

**Files:** `tools/knowledge_gateway_cache.py`

**Change:** Per DD3 (investigation.md Risk 3). Add the new module-level helper
`_level2_repo_branch_scope(repository_id: str, branch: str) -> str` (exact body in DD3 above),
placed immediately above `revalidate_context_packet_row()` (Step 3). Pure string join, no I/O, no
`git` subprocess call (distinct from `_current_repo_branch_scope()`, `:121-129`, which does perform a
live `git branch --show-current` read — this new helper never does, since Level 2's identity is
always caller-supplied per DD3).

**Do NOT touch:** `_current_repo_branch_scope()` itself (`:121-129`) — unchanged, still Level 1's own
live-git-read helper, never called by this ticket's new Level 2 code.

**Verify:** exercised indirectly by every Step 3/Step 5 test that constructs a row/current-scope
pair (`test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies` is
the most direct proof of its correctness, since it depends on the reconstructed strings actually
differing when `repository_id`/`branch` differ).

### Step 3 — Add `revalidate_context_packet_row()` orchestrator

**Files:** `tools/knowledge_gateway_cache.py`

**Change:** Per DD3/DD4. Add `revalidate_context_packet_row()` (exact body in DD3 above) immediately
after `revalidate_cache_row()` (`:204-219`), under a new `# --- Step 9 ---` section comment matching
this module's existing per-addition section-comment convention (`# --- Step 5 ---` at `:152-155`,
`# --- Step 7 ---` at `:222-224`, etc.). The function performs, strictly in this order: (1) branch
check via `is_branch_compatible()` + `_level2_repo_branch_scope()` (Step 2) — returns `False`
immediately on incompatibility, before any other line executes; (2) `working_tree_overlap_forces_
revalidation()` against `row["evidence_dependencies"]`; (3) `select_validation_basis()` — DD4's
fail-closed `False` on any non-`"PROVIDER_GENERATION"` basis; (4) a per-provider dict comparison of
`json.loads(row["provider_generations"])` against the caller-supplied `current_provider_generations`
dict (Investigate Question 2's finding — genuinely dict-shaped, not a single-string reuse).

**Do NOT touch:** `revalidate_cache_row()` itself (`:204-219`) — byte-unchanged, this is a new
sibling function, not a modification. Do not call, import, or reference
`tools.knowledge_gateway_packet_assembly` anywhere in this function or this module (the guarded
architecture boundary, investigation.md's central finding) — the function's only inputs are a plain
`row: dict` and caller-supplied scalars/dicts. Do not add a `check_context_packet_cache()`/
`write_context_packet_cache()` pair — this function is a pure decision function, never wired to a
live lookup. Do not read `row["working_tree_fingerprint"]` or `row["head_commit"]` (DD2 — neither is
part of this ticket's mechanism).

**Verify:** `test_revalidate_context_packet_row_rejects_on_changed_paths_intersection`,
`test_revalidate_context_packet_row_survives_unrelated_changed_path`,
`test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies`,
`test_revalidate_context_packet_row_survives_new_commit_alone_unchanged_generations`,
`test_revalidate_context_packet_row_multi_provider_generations_dict_all_checked`,
`test_revalidate_context_packet_row_never_returns_freshness_or_verification_field` (all
`test_plan.md`, New Tests 5-10); plus **new, Plan-derived**
`test_revalidate_context_packet_row_fails_closed_when_finer_basis_selected_but_no_level2_
fingerprint_column_exists` (not in `test_plan.md`'s enumerated 12 — added per DD4; constructs a
`capability_descriptor` fixture with `fine_grained_fingerprints: True` so `select_validation_basis()`
returns `"FINER"`, and asserts the function returns `False` rather than raising or assuming valid);
plus regression: `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`
(`test_plan.md` New Test 12 / existing guard), `test_no_raw_insert_statement_bypasses_redaction_
anywhere_in_cache_module`, and the full existing 20-test suite in
`tests/tools/test_knowledge_gateway_cache.py`.

### Step 4 — Add the direct-reuse proof test for `working_tree_overlap_forces_revalidation()`

**Files:** `tests/tools/test_knowledge_gateway_cache.py`

**Change:** Add `test_working_tree_overlap_forces_revalidation_called_unmodified_against_evidence_
dependencies_shape` (`test_plan.md` New Test 4) — imports `knowledge_gateway_packet_assembly` only
to construct a fixture packet (never the reverse import direction; this test file, unlike the
production module, has no architecture guard against importing packet assembly), asserts
`working_tree_overlap_forces_revalidation()` is called with the exact JSON string
`json.dumps(sorted(packet.evidence_dependencies))` with no intermediate transformation, proving Step
1's aggregation output is consumed by Step 3's orchestrator with no reimplementation of the
intersection logic in between.

**Do NOT touch:** the import-direction guard test itself
(`test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`) — this new test lives in
the *test file*, not the production module, so it is exempt from that guard by design (the guard
only inspects `tools/knowledge_gateway_cache.py`'s own source, not the test file's).

**Verify:** `test_working_tree_overlap_forces_revalidation_called_unmodified_against_evidence_
dependencies_shape` itself; regression: the full existing test-file suite.

### Step 5 — Add the anti-scope-creep guard test (no new SQLite table)

**Files:** `tests/tools/test_knowledge_gateway_cache.py` (or a new dedicated architecture-guard test
file — Plan decision: place it in `tests/tools/test_knowledge_gateway_cache.py`, alongside the other
architecture-guard tests for this same module, rather than a new file, since this ticket's diff is
entirely within `tools/knowledge_gateway_cache.py`/`tools/knowledge_gateway_packet_assembly.py` and a
single-purpose new file would be disproportionate)

**Change:** Add `test_no_junction_table_or_new_sqlite_table_introduced_by_this_ticket`
(`test_plan.md` New Test 11). Concrete mechanism (Architecture-Review-corrected — see "Architecture
Review Corrections" at the top of this plan): read `tools/retrieval_cache.py`'s full source and
assert `len(re.findall(r"CREATE TABLE IF NOT EXISTS \w+\s*\(", source)) == 6` — matching actual DDL
statements only (three legacy marker-only tables at `:207`/`:221`/`:237`, `retrieval_cache_generation`
at `:265`, the Level 1 table at `:273`, the Level 2 table at `:326`), not a raw substring count. The
trailing `\s*\(` is load-bearing: it excludes two docstring occurrences at `:257`/`:312` that are
phrased as the literal text `"CREATE TABLE IF NOT EXISTS only — additive, never..."` inside
migration_001's/migration_002's own docstrings — without the trailing `\(` requirement, "only" reads
as a matching `\w+` token and the pattern false-positives to 8, not 6 (confirmed by direct execution
against the live file this session). A number that must not silently grow. This does not merely
assert "byte-unchanged" (which would be over-broad and fragile against unrelated future edits to
this file) and does not use a plain `source.count("CREATE TABLE")` substring count (comment-text-
coupled — 9 today, per the correction note above, and would break again if an unrelated docstring
elsewhere in the file changes) — it asserts the one specific invariant this ticket's Anti-Drift
Hazards actually care about: no new DDL table statement.

**Do NOT touch:** `tools/retrieval_cache.py` itself — this ticket's own diff must leave it
byte-unchanged; this test is a guard against a *future* regression, not a description of a change
this ticket makes.

**Verify:** `test_no_junction_table_or_new_sqlite_table_introduced_by_this_ticket` itself; regression:
`tests/tools/test_retrieval_cache.py::TestLevel2Migrations` (all 13 tests, including
`test_no_actual_read_write_functions_added_for_the_new_level2_table`).

### Step 6 — Document-Update: parity ledger `INFRA-348`, proposal §20 annotation, module docstring/comment honesty

**Files:** `tools/knowledge_gateway_packet_assembly.py` (comments/docstrings only),
`tools/knowledge_gateway_cache.py` (comments/docstrings only), `docs/plans/knowledge-gateway-mcp-
proposal.md`, `docs/parity_ledger/infrastructure.yaml`

**Change:**
1. **Module docstrings/comments** (no behavior change): `tools/knowledge_gateway_packet_assembly.py`'s
   top-level docstring bullet list gains one line noting `evidence_dependencies` is a real, aggregated
   field (mirroring the sibling ticket's own Step 9 convention of updating the module's "honesty
   notes" bullets when a new capability lands). `tools/knowledge_gateway_cache.py`'s own docstring
   (`:1-48`) gains a note that this module now also performs Level 2 packet-level revalidation
   (`revalidate_context_packet_row()`), alongside its existing Level 1 orchestration description —
   its "What this is not" section's claim that this module does "no Level 2/Level 3 caching" (`:17`)
   must be corrected: it now performs Level 2 **revalidation-decision** logic, though still no Level 2
   **storage/lookup** (that distinction must be stated precisely, not glossed over).
2. **`docs/plans/knowledge-gateway-mcp-proposal.md` §20**: read the current text of the "Add packet
   dependency records and targeted invalidation" Phase 3 bullet and the exact annotation format the
   Phase 1/2 and this ticket's own sibling child tickets already used, and match it precisely — do not
   invent a new annotation format.
3. **`docs/parity_ledger/infrastructure.yaml`**: add a new entry, `INFRA-348` (confirmed live: 347
   real `INFRA-` entries exist as of this session, `INFRA-347` being the dedup/budget sibling's own
   entry — verified by direct `grep -n "^- id: INFRA-3" docs/parity_ledger/infrastructure.yaml` this
   session), `status: verified`, `priority: P1` (matching this subsystem's existing P1 pattern, per
   investigation.md's own confirmation that no P0 entry is touched), `v2_evidence` citing
   `_evidence_dependencies()`/`PacketAssembly.evidence_dependencies` (`tools/knowledge_gateway_
   packet_assembly.py`) and `_level2_repo_branch_scope()`/`revalidate_context_packet_row()`
   (`tools/knowledge_gateway_cache.py`) with real line anchors as landed, `test_path:
   tests/tools/test_knowledge_gateway_packet_assembly.py` and `tests/tools/test_knowledge_gateway_
   cache.py` (both, mirroring `INFRA-347`'s own single-file-citation style but extended since this
   ticket spans two files), `divergence_note: null` (no Mechanics Bible/engine-contract chapter
   governs this subsystem, confirmed by investigation.md's Mechanics/Engine Constraints section),
   `support_boundary` mirroring `INFRA-346`/`INFRA-347`'s own style (agent-tooling only, no `src/`
   file touched, no live wiring into `_run_knowledge_context()`, no schema/table change — verified in
   the diff). Must validate against `docs/parity_ledger/schema.json`'s `required: ["id", "text",
   "status", "priority"]` plus the `verified`-status conditional requiring `v2_evidence`/`test_path`
   (both present) — confirmed by direct read of the schema this session.

**Do NOT touch:** `evidence_cache_identity_contract.md` §5 itself (investigation.md's own finding: §5's
existing text is already level-agnostic and needs no edit — this ticket's Out of Scope forbids editing
it absent a genuine extension need, and none was found). Do not touch any other `INFRA-*` entry besides
the new `INFRA-348` addition. Do not touch `docs/guidelines/intentional_divergences.md` — no
divergence exists (confirmed, this subsystem is outside Mechanics Bible/engine-contract scope). Do not
touch `tools/retrieval_cache.py`'s own module docstring (unrelated to this ticket's diff).

**Verify:** manual review during Document-Update phase confirms all sub-changes exist; `INFRA-348`
validated against `docs/parity_ledger/schema.json` via this repo's existing parity validation tooling
during the Parity phase (per `test_plan.md`'s own note that this is not part of the pytest scope).

## Scope Guards

- `tools/knowledge_gateway_router.py` stays byte-unchanged — no step opens it for edit; guarded by
  `test_module_does_not_edit_knowledge_gateway_router`.
- `tools/retrieval_cache.py` stays byte-unchanged — no step opens it for edit; guarded by
  `test_no_actual_read_write_functions_added_for_the_new_level2_table` and the new Step 5 guard test.
- `tools/knowledge_gateway_mcp.py::_run_knowledge_context()` is never touched — explicit Out of
  Scope; no step reads or writes it.
- No `check_context_packet_cache()`/`write_context_packet_cache()`-style function is added against
  `retrieval_context_packet_cache_rows` — both new functions this plan adds are pure, standalone,
  independently-callable logic, never wired to a live lookup/write pair.
- No junction table or relational dependency-tracking machinery is added — `evidence_dependencies` is
  consumed and produced as the single, already-frozen `TEXT NOT NULL` JSON-array column the schema
  ticket defined; guarded by the new Step 5 test.
- `tools/knowledge_gateway_packet_assembly.py` is never imported by `tools/knowledge_gateway_cache.py`
  — `revalidate_context_packet_row()` consumes only a plain `row: dict`, never a live `PacketAssembly`;
  guarded by the existing `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`.
- `revalidate_cache_row()`, `is_branch_compatible()`, `working_tree_overlap_forces_revalidation()`,
  `select_validation_basis()`, and `_capability_descriptor_for()` are never modified or reimplemented
  — Steps 2/3 call the latter three directly, unmodified, and leave `revalidate_cache_row()` itself
  byte-unchanged (a new sibling function is added, not a rewrite).
- `working_tree_fingerprint` is never populated or read by this ticket's own new code (DD2) — no step
  writes an invented value into it, and no step reads it for a revalidation decision.
- No semantic/fuzzy/embedding-based dependency matching is introduced — `_evidence_dependencies()`
  and `revalidate_context_packet_row()` both use exact string/path-set logic only, consistent with
  the reused §5 primitives' own exact-set-intersection design.
- No automatic Cache-GC scheduling is added — confirmed by investigation.md that no automatic GC
  exists at either level to "trivially reuse"; this ticket's own Out of Scope carve-out resolves to
  not-applicable.
- `evidence_cache_identity_contract.md` §5 itself is never edited — its existing text is already
  level-agnostic (investigation.md's own finding, re-confirmed by this session's direct read).

## Dependency Map

- Step 1 (packet_assembly.py) is independent of Steps 2/3 (cache.py) — different files, different
  concerns, may be implemented in either order or in parallel.
- Step 3 depends on Step 2 (`revalidate_context_packet_row()` calls `_level2_repo_branch_scope()`).
- Step 4 depends on both Step 1 (needs `PacketAssembly.evidence_dependencies` to exist to build its
  fixture packet) and Step 3 (needs `working_tree_overlap_forces_revalidation()`'s call site
  understanding, though it re-uses the pre-existing function directly — the test asserts Step 1's
  output shape is what that pre-existing function is fed).
- Step 5 depends on nothing but must land after Steps 2/3 are complete, so the guard test's known-count
  baseline (6 `CREATE TABLE IF NOT EXISTS \w+\s*\(` DDL matches, per the Architecture Review
  correction above) reflects the final state of this ticket's diff.
- Step 6 (Document-Update) depends on Steps 1-5 all being in place — it cites real line numbers/test
  paths from the landed code and cannot be written accurately beforehand.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: every cached packet's `evidence_dependencies` accurately records real aggregated dependencies, not a superset | Step 1 (DD1) | `test_evidence_dependencies_aggregated_from_packet_evidence_paths`, `test_evidence_dependencies_excludes_paths_from_omitted_budget_truncated_statements`, `test_evidence_dependencies_empty_in_section16_budget_assembly_failure_not_full_unfiltered_evidence` (new) |
| AC2: a changed cited source causes the affected packet to be invalidated/revalidated (real test, not doc claim) | Step 3 | `test_revalidate_context_packet_row_rejects_on_changed_paths_intersection` |
| AC3: an unrelated changed source does not invalidate a packet with no dependency overlap | Step 3 | `test_revalidate_context_packet_row_survives_unrelated_changed_path` |
| AC4: branch identity remains a hard partition at the packet level | Step 3 (DD3's branch-check-first ordering) | `test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies` |
| AC5: a new commit alone, with unchanged evidence fingerprints, does not force a packet cache miss | Step 3 | `test_revalidate_context_packet_row_survives_new_commit_alone_unchanged_generations` |
| AC6: the §5 reuse-vs-extension finding is documented explicitly in Implementation Notes, with reasoning | Step 6 (content sourced from this plan's DD1-DD4 and investigation.md's Current Behavior section) | Manual review during Document-Update/Finalize |
| AC7: a real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added | Step 6 | Manual/tooling validation against `docs/parity_ledger/schema.json` during Parity phase |

## Flagged for Architecture Review

1. **DD1 — aggregation source correction (`final_context`, not `final_evidence`).** High-confidence,
   directly cited (branch trace of `assemble_packet()`'s two return paths), but it overrides
   investigation.md's own stated conclusion — Architecture Review should independently re-verify the
   §16-branch trace before this lands, since it is the one place this plan diverges from the prior
   phase's finding.
2. **DD4 — fail-closed default when `select_validation_basis()` returns `"FINER"` at Level 2.**
   Genuinely new (not examined by investigation.md), safety-relevant (governs a §4 hard-rule branch),
   and not covered by any of `test_plan.md`'s enumerated 12 tests. Two reasonable alternatives exist
   (fail-open, raise) — Plan has chosen fail-closed with reasoning above and added a new test to cover
   it, but this is exactly the class of decision the ticket asks Plan/Review to make explicitly rather
   than silently.

## Anti-Drift Notes

- **`_evidence_dependencies()` must read `final_context`, never `final_evidence`/`evidence_entries`.**
  DD1's correction exists specifically because the two diverge in the §16 budget-assembly-failure
  branch. A future "simplification" that switches the source back to `final_evidence` "since they're
  usually the same" would silently reintroduce the exact superset-in-total-failure bug DD1's new test
  exists to catch.
- **`revalidate_context_packet_row()` must check branch compatibility strictly first**, before touching
  `evidence_dependencies`/`provider_generations` at all — unlike Level 1, where this ordering is
  enforced by the *caller* (`perform_cache_lookup()`), Level 2 has no such caller yet, so this
  ordering must be enforced *inside* the function itself. Do not refactor this into "branch check as
  just another condition among several" — §5 rule 2's own text requires it to run "before any
  fingerprint comparison is even consulted," and `test_revalidate_context_packet_row_rejects_cross_
  branch_even_with_identical_dependencies` exists to prove this ordering, not just the outcome.
- **The `"FINER"`-basis fail-closed branch (DD4) is deliberate, not a placeholder "TODO."** Do not
  replace it with an actual `row["evidence_fingerprints"]`-style comparison unless a future ticket
  first adds the equivalent column to `LEVEL2_CACHE_COLUMNS`/the DDL (a schema change, out of this
  ticket's scope) — attempting the comparison against a column that does not exist would `KeyError`
  at runtime, exactly the bug class `revalidate_cache_row()`'s own hardcoded-column-names issue
  (investigation.md's central Question 1 finding) already demonstrated is real and easy to introduce
  by careless reuse.
- **`working_tree_fingerprint` stays unpopulated and unread by this ticket (DD2).** Do not "helpfully"
  invent a value for it to "complete" the row shape in a future edit to this ticket's own functions —
  no doc defines one, and the `changed_paths`-intersection mechanism this ticket implements is
  §5 rule 3's complete, sufficient mechanism on its own.
- **Do not reimplement any of the four reused §5 primitives** (`is_branch_compatible()`,
  `working_tree_overlap_forces_revalidation()`, `select_validation_basis()`,
  `_capability_descriptor_for()`) under a new name inside `revalidate_context_packet_row()`. All four
  are called directly, unmodified.
- **`INFRA-347`'s own citations should be spot-checked for drift once this ticket's diff lands**
  (investigation.md's own Parity Ledger Overlap note) — this ticket adds a new field to the same
  `PacketAssembly` dataclass `INFRA-347` also modified; re-verify `INFRA-347`'s line-range citations
  are still accurate after Step 1's field insertion shifts line numbers, per the established
  re-verification convention both prior sibling investigations used for overlapping-file citations.

## Unresolved Questions

None remain fully open — investigation.md's two flagged Risks (`working_tree_fingerprint`'s producer,
DD2; the dict-shaped `provider_generations` comparison, DD3) are both resolved above with concrete,
cited mechanisms. The two genuinely new items this plan's own fact-verification surfaced (DD1's
aggregation-source correction, DD4's fail-closed default) are not left open either — both are decided
with reasoning above — but both are explicitly flagged for Architecture Review's independent
scrutiny in "Flagged for Architecture Review," since neither was examined by investigation.md and
Architecture Review should confirm the reasoning before Implement proceeds.
