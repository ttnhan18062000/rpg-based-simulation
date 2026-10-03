---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-READPATH-GATE
artifact_type: investigation
tags: [ai, agent-monitoring, observability, process-improvement, testing, workflows]
---

# Investigation — TCK-20260731-PARITY-READPATH-GATE

## Current Behavior

### `tools/parity_index.py` — the read-path system under review (read in full, 708 lines)

Phase 2's read functions, confirmed present and working:

- `entry(entry_id, db_path=None)` (line 485-531): exact `entries` lookup by PK, joins
  `code_refs`/`test_refs`/`constraint_refs`/`ticket_refs` (each row annotated with a synthesized
  `selection_reason`, line 507) and `entry_health`. Returns `{"found": False}` for an unknown ID
  (line 493) — never `None`/empty dict.
- `impact(changed_path=None, test_path=None, symbol=None, db_path=None)` (line 534-593): exact-match
  `WHERE path = ?` against `code_refs`/`constraint_refs`/`ticket_refs` (for `changed_path`) and
  `test_refs` (for `test_path`), unions matches, sorts by `(priority, status severity, entry_id)`
  (line 575-581), returns `{"status": "no_filter_provided"|"no_match"|"ok", "results": [...]}`.
  `--symbol` is an accepted no-op (line 585-589) — never narrows a query, per
  `v1_decisions_phase0.md`'s path-only-links decision.
- `health(subsystem=None, priority=None, db_path=None)` (line 596-643): joined
  `entry_health`/`entries` query, ordered `(shard, id)`, plus a `ledger_generation` summary header.
- `_connect_readonly` (line 87-92) opens `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)` —
  a real architectural guard: any accidental write attempt from these three functions fails loudly.

This is the system Gate A must exercise, unmodified, against a real corpus — confirmed via direct
read that no `impact`/`entry`/`health` code exists to change and none is authorized to change here
(ticket's own Out of Scope: "changing the index/legacy tools to improve the score during the
review").

### Legacy comparison targets — read in full, unchanged since Phase 2's own investigation

- `tools/parity_ledger_scan.py::find_p0_intersection` (line 36-59): P0-only, `v2_evidence`-only,
  substring match, scans only the 8 `CANONICAL_LEDGER_FILES` (line 24-33, **excludes
  `faction.yaml`**). No dedup, no explicit no-match marker.
- `tools/gate_checks/parity_updater_static.py::derive_mapping`/`cross_reference_touched`
  (line 39-119): all-priority, ANY-of-multi-shard accumulation from `v2_evidence` regex matches,
  same 8-file canonical scan (line 34, imported **by identity** from `parity_ledger_scan`), silent
  `except Exception: continue` on a malformed shard (line 55-56).

Both are the two independent "legacy selection" surfaces Gate A's rubric must run each corpus case
through, per the idea doc's own Gate A bullet ("review false negatives, false positives, selection
size, and analyst effort against the existing scan").

### `tests/tools/test_parity_index.py::TestEquivalenceFixtures` (line 776-910, read in full) — Phase 2's synthetic proof, the nearest existing evidence

Four tests already prove, on **fabricated fixture data** (`_make_corpus` with invented IDs
`COMB-501`/`COMB-502`, `CM-601`/`SC-601`, `TR-701`, `FAC-801`), that:
1. `find_p0_intersection` is P0-only where `impact` is all-priority (line 778-812).
2. `derive_mapping`'s ANY-of-multi-shard semantics is matched by `impact` (line 814-844).
3. `derive_mapping` silently skips a malformed shard while the index importer aborts the whole
   build — a labeled, intentional divergence, not reconciled (line 846-874).
4. A `faction.yaml` entry (`FAC-801`) is invisible to both legacy functions but surfaced by
   `impact`/`entry` (line 876-910).

**This is unit-test evidence of code correctness, not Gate A's required evidence.** Gate A's own
scope text calls for "a predeclared set of real tickets or ticket-like fixtures" — `_make_corpus`'s
fixtures are synthetic constructions built to exercise a specific code path, not derived from any
real ticket's actual changed-files list or a real ledger entry's real history. No script,
document, or corpus that runs Gate A's rubric against real data exists yet anywhere in the repo —
confirmed via `grep -rl "Gate A\|read-path payoff" tools/ tests/ docs/ staging_artifacts/
stored_artifacts/` returning only the idea doc itself and this investigation's own future files.

### `docs/plans/.../idea_parity_ledger_sqlite_context_integration.md` "Gate A — Read-path payoff review" (read in full, line 400-408)

> Use the read-only impact query on a predeclared set of real tickets or ticket-like fixtures and
> review false negatives, false positives, selection size, and analyst effort against the existing
> scan. Proceed to any write/context work only if the index demonstrates a material precision,
> coverage, or context-size advantage without a regression in obligation recall. Otherwise retain
> the present ledger and close or backlog the later phases.

Combined with the Observability section's promotion paragraph (line ~379-383): "Promotion from
shadow to a workflow-provided packet requires the existing context-retrieval promotion thresholds
plus parity-specific proof that the index catches every reference selected by the legacy scan on a
representative fixture corpus, and that no newly observed missed obligation is attributable to the
packet narrowing." This is the literal evidentiary bar this ticket's decision must clear or
explicitly fail to clear.

## Mechanics/Engine Constraints

None. Consistent with Phase 0/1/2's own repeated findings, independently reconfirmed here: this is
agent-infrastructure/process-review work — no `docs/mechanics/` chapter or `docs/engine/` contract
governs parity-ledger tooling or its review gates. `docs/engine/contracts/context_packet_contract.md`
is explicitly named in Related Docs as "boundary only" — read in full and confirmed it documents a
**not-yet-implemented** future `ContextRequest`/`ContextPacket` schema ("No `src/` or `tools/` code
... exists yet, and none is added by this ticket"). This ticket must treat it as informational
framing for what a later, separately-authorized phase would consume — never as license to construct
or wire a real packet here. Likewise `docs/observability/retrieval_retention_redaction_policy.md`
is boundary-only: its MAY/PROHIBITED list (hashes/IDs/counts/reason codes permitted; raw
prompt/retrieved-content text prohibited) constrains what any effort/measurement log this ticket
produces may record, if it records anything resembling a monitoring-style event at all.

## Parity Ledger Overlap

No `docs/parity_ledger/*.yaml` entry's `status`/`v2_evidence` needs to change as a result of this
ticket, and no new entry is required — this ticket is a review/decision-gate over existing tooling,
producing no `src/` behavior change (reconfirmed: `grep -rl "PARITY-READPATH\|read-path payoff"
docs/parity_ledger/` returns zero matches). The three informational-only precedent entries Phase
0/1/2 already found remain the closest prior art, unchanged: **`INFRA-289`, `INFRA-290`,
`INFRA-291`** (`docs/parity_ledger/infrastructure.yaml`, lines 5710/5779/5859) — each documents a
`tools/agent-monitoring/*.py` module's migration onto a derived SQLite index with a
comparison-test proving field-for-field parity or a labeled narrow divergence. None require edits.

Two concrete **real, non-synthetic** parity-ledger entries were located during this investigation
that are directly usable as Gate A corpus cases (see Prior Work below for how they were found):

- **`FAC-012`** (`docs/parity_ledger/faction.yaml`, added by commit `68f168ff`,
  `TCK-20260702-SIMQ-UPLIFT2-FACTION`): `status: verified`, `priority: P1`, `v2_evidence` cites
  real `src/worldbuilding/schema.py`, `src/worldassembly/schema.py`, `src/worldbuilding/compiler.py`,
  `src/worldassembly/resolver.py` paths. Satisfies the ticket's explicit "faction source-path case"
  requirement with genuine data, not a fabricated fixture.
- **`INFRA-296`/`INFRA-297`/`INFRA-299`/`INFRA-300`** (`docs/parity_ledger/infrastructure.yaml`,
  added by commit `ab06fc10`, `TCK-20260729-SHADOW-PACKET-CALL-SITE`/
  `TCK-20260729-SHADOW-BASELINE-COMPARISON`): real entries whose `v2_evidence` cites
  `tools/agent-monitoring/generate_retro.py` among other paths.

No P0 entry is at risk from this ticket (no `src/` change, no `v2_evidence` touched, no gate
behavior changed — Out of Scope forbids all three).

## Prior Work

- **`stored_artifacts/TCK-20260731-PARITY-IMPACT-PROOF/`** (plan.md, investigation.md, test_plan.md
  — read in full) — the direct Phase-2 predecessor whose evidence this Gate reviews. Its Decisions
  1-2 (test-narrowing precedent, `--symbol` no-op) and its Anti-Drift Notes are settled and must not
  be reopened here. Its own investigation.md explicitly scoped the equivalence proof to "small,
  synthetic, `tmp_path`-isolated fixtures... not a live-corpus replay" — which is exactly why Gate A
  exists as a separate, real-data review rather than treating Phase 2's green tests as sufficient.
- **`stored_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/`, `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/`**
  (Phase 0/1) — corpus facts (9 shards, 1,945 entries, `faction.yaml` has 0 P0 entries) and binding
  `v1_decisions_phase0.md` architecture decisions this ticket inherits without reopening.
- **`tickets/done/TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS.md`** (read in full; no
  `stored_artifacts/` folder exists for it — it closed as **hotfix tier**, so no staging artifacts
  were required, confirmed via its own Tier field and Assumptions section citing precedent). This
  is the "decision-gate precedent, distinct scope" the ticket names: it produced
  `docs/ai/shadow_promotion_gate_thresholds_decision.md`, a rubric-shaped decision doc with (a) an
  explicit falsifiable bar per named criterion, (b) a sample size grounded in a real tool output
  field rather than an invented round number, (c) a labeled section stating a precondition currently
  holds at zero (there, zero real shadow events; here, likely zero prior Gate-A reviews), and
  (d) explicit "not defensible a priori — stated as risk" honesty for criteria lacking real grounding
  rather than fabricating a number. This ticket's GO/NO-GO/INCONCLUSIVE decision document should
  mirror that same shape and rigor — same genre of artifact (a reviewable decision doc under
  `docs/ai/` or an equivalent staging location), not the same subsystem or scope.
- **`docs/parity_ledger/infrastructure.yaml` INFRA-289/290/291`** — precedent shape for "read path
  migrates from linear scan to derived index, comparison test proves parity or documents narrow
  divergence" — the same precedent shape Phase 2 already cited; still no direct documentation of
  `parity_index.py`/`parity_ledger_scan.py`/`parity_updater_static.py` themselves.
- **Git-history mining for real ticket-derived corpus cases** (this investigation's own new work,
  not reused from a prior artifact): `git log --oneline -- docs/parity_ledger/` returns 74 commits
  where a real ticket's `Files Changed` touched the ledger. Two were read in full via `git show`:
  - `68f168ff` (`TCK-20260702-SIMQ-UPLIFT2-FACTION`) added `FAC-012` to `faction.yaml`, citing four
    real `src/` paths, in the same commit that changed those exact `src/worldbuilding/`/
    `src/worldassembly/` files. This is a genuine, reviewable, immutable (pinned to a git SHA)
    ticket-derived case, not a synthetic fixture.
  - `ab06fc10` (`TCK-20260729-SHADOW-PACKET-CALL-SITE`/`SHADOW-BASELINE-COMPARISON`) added
    `INFRA-296`/`297`/`299`/`300` to `infrastructure.yaml` in the same commit that changed
    `tools/agent-monitoring/generate_retro.py` and `.claude/workflows/implement-ticket.js`.
  - `git log --oneline -- docs/parity_ledger/faction.yaml` shows only 3 total commits ever touching
    that shard, so `FAC-012` is effectively the only real, ticket-attributable faction case
    available without also using a synthetic/fabricated one.
  - Many more candidates exist across other shards (e.g. `46c5ae59`
    `TCK-20260716-PLACELEGAL-HARDLAW`/`TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` touching
    `world_dynamics.yaml`) if the rubric needs more than two real cases.

## Risks and Open Questions

1. **No Gate A execution harness exists anywhere** — confirmed via repo-wide grep. This ticket's
   Scope requires "reproduce results," which implies *some* script or documented, re-runnable
   procedure that builds the index, runs `impact`/`entry`/`health` and the two legacy functions
   against the same corpus, and records both outputs. Whether that harness is a throwaway script
   under `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/` (never touching `tools/`) or purely
   a documented sequence of `python3 -c "..."` commands transcribed into the decision doc is an open
   question for Plan — **not assumed here**, since the ticket's Out of Scope line ("any
   context-packet/retrieval-cache/workflow/gate/config/monitoring mutation") does not explicitly
   authorize or forbid a review-only script living outside those named systems.
2. **Corpus "immutability" is a real correctness risk, not a formality.** `docs/parity_ledger/*.yaml`
   entries continue to be edited by unrelated, ongoing tickets (74 commits and counting). A case
   pinned only to an entry ID (e.g. "`FAC-012`") without also recording the git commit SHA / blob
   hash of the ledger file at corpus-freeze time could silently drift — a later ticket could touch
   `FAC-012`'s own `v2_evidence`, or add a second entry citing the same `src/` path, changing the
   "expected obligation set" without the corpus being aware. Plan must decide the pinning mechanism
   (commit SHA + `canonical_fragment_hash`, most likely, since `parity_index.py` already computes
   that hash per entry at line 231-233) before results are captured, not after a mismatch surfaces.
3. **Phase 2's `TestEquivalenceFixtures` synthetic fixtures must not be mistaken for, or silently
   substituted as, this ticket's "immutable, ticket-derived cases."** They are valid evidence of
   code-path correctness but were built by `_make_corpus` specifically to exercise a code branch,
   not derived from any real ticket's actual `files_changed`. The ticket's own Scope text explicitly
   requires "legacy edge fixtures **plus** immutable, ticket-derived cases" — both are required, not
   either/or.
4. **"Consistently measured analyst effort" has no existing tool to reuse.** `generate_retro.py`
   measures agent run `duration_s`/`cost_proxy_score` (machine effort), not human-analyst review
   effort. `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS`'s own precedent for an analogous gap
   ("no existing tool computes causal attribution... must propose a new method rather than reference
   an existing one") applies directly here: Plan must either define a simple, consistent manual
   measurement (e.g., a self-reported time-per-case log with a fixed unit) or explicitly flag
   analyst-effort measurement as qualitative/best-effort rather than fabricate false precision.
5. **AC #4's "GO... demonstrates faction/all-shard coverage, fewer false positives, or smaller
   selection size without recall regression" is an OR of three possible advantages, not all three.**
   Faction/all-shard coverage is already structurally demonstrable from `FAC-012` (Parity Ledger
   Overlap above). Whether the index also produces fewer false positives or a smaller selection size
   on the two real non-faction cases found here can only be known by actually running both legacy
   functions and `impact` against them — this is Gate A's own execution work, not something
   Investigation can pre-determine.
6. **P0 coverage of the real corpus is unverified.** Neither `FAC-012` (P1) nor the confirmed-present
   `INFRA-296`/`297`/`299`/`300` set (priorities not yet individually verified in this pass) is
   confirmed P0. `find_p0_intersection`'s own legacy behavior is P0-only, so if the rubric's recall
   claim is meant to cover P0 obligations specifically, Plan should verify at least one real or
   documented-fixture P0 case exists in the final corpus, or explicitly state P0 recall is
   unverified by real data alone.

## Anti-Drift Hazards

- **Do not let "reproduce results" become a de facto Phase 3/4 implementation.** Any harness script
  this ticket produces must never construct a real `ContextPacket`, call
  `tools/context_packet_assembler.py`, or touch `.claude/workflows/implement-ticket.js` — both are
  named Related Code Areas as "protected boundary; no edit expected" / "protected regression
  boundary."
- **Do not "fix" `find_p0_intersection`, `derive_mapping`/`cross_reference_touched`, or
  `impact`/`entry`/`health` to improve the review's own score.** The ticket's Out of Scope forbids
  this explicitly. Any discrepancy Gate A finds must be adjudicated and recorded, never patched away
  mid-review — patching the tool under review to make the gate pass is exactly the kind of
  gate-substance violation CLAUDE.md's Hard Rules forbid.
- **Do not silently substitute Phase 2's synthetic `TestEquivalenceFixtures` cases for this ticket's
  required real, ticket-derived corpus.** They remain valid, separate evidence; they are not a
  shortcut around building the real corpus this ticket's own Scope requires.
- **Do not average discrepancies away.** AC #3 requires zero *unexplained* obligation false
  negatives against the adjudicated set — every mismatch must be individually adjudicated, not
  rolled into a summary pass rate that hides one case's failure.
- **Do not leave the corpus unpinned.** Every case must record a git commit SHA and/or the entry's
  `canonical_fragment_hash` at capture time — an un-pinned "current live YAML" reference is not
  reproducible once any other ticket next edits `docs/parity_ledger/`.
- **A GO decision must not imply, hint at, or pre-authorize any config/workflow/gate change.** The
  ticket is explicit that GO "only authorizes later ticket scoping, NOT implementation" — the
  decision doc's "next action" field must name a future ticket to scope, not a change to make now.
