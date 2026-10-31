
## RETRO-2026-W44: note stamped at 45 runs

<!-- retro-note runs=45 -->
**2026-10-29, lead-planner-u24 (owner go: #715 6492223703). The week is still open; this covers 45 runs.**

**What failed most?**
- No run ended in a gate failure, and all 45 are DONE. The only blocking verdicts are 20 from the Finalize self-check (`done_checker_static`); 14 were fixed and rerun, and 2 were rerun with no change.
- Four W44 blocks have no recorded outcome:
  - three tickets of the #779 batch: EVENT-RECORDER-NEVER-GIVEN-THE-RUN-ID, OBSERVABILITY-GUIDE-NAMES-EVENT-FIELD-CATEGORY and QUALITY-HUB-WRITES-A-SCORE-LINE;
  - PARITY-PAYDOWN-WORLD-DYNAMICS.
- Action: the closing seats (rpg-implementer-3, and the ubuntu lane for the world_dynamics paydown) record `gate_ledger.py outcome` for those ids. This is bookkeeping only.
- The ledger also lists older unresolved ids (W41-W43). They are not this week's.
- Server-side merge friction is not in this data, but it was the most frequent delivery failure today:
  - #782 went CONFLICTING twice and #779 once, each time on `docs/REGISTRY.yaml` only.
  - Each one cost a fresh main-merge, a push ask and a CI cycle.
  - Action: agent-working-planner-u24's proposed ticket to stop committing `docs/REGISTRY.yaml` in PRs. It needs an owner go, and lead-planner-u24 recommends it.

**What was slow?**
- No slow runs are recorded, and the derived average is 22 min. But duration is unknown for 19 of 45 runs (42%), and cost for the same 19.
- Every run was hand-closed; no pipeline runs ran. Gate and phase numbers therefore describe hand closures only.
- The real latency this week was owner-ask round trips and CI cycles between pushes, which this report does not measure.
- Action: run the batch-latency section (`--latency-prs`) over this week's merged PRs (#779 to #784) at the week close.

**What to change?**
- The routing candidates are Review and Architecture-Verify. Standard-tier hand closes skipped both in 24 of 24 runs, reason `no_hand_tool`; hotfix runs skipped Parity in 18 of 20, which is expected.
  - In practice, the domain planner's PR review stands in for Review, but nothing records it as a Review event.
  - Action, for agent-working-designer-u24 to decide: either record the planner's PR OK as a Review event on the ticket's run, or state in the tier docs that a hand close's Review is the PR review.
- Handover recovery is 16 of 17 manual orchestration actions. Seats ran far past the 250k context cap: rpg-implementer reached 405k and rpg-planner 347k.
  - The post-merge context check (lead routine) catches it, but resets wait for a HARD boundary that a long evidence job pushes back.
  - Action: a seat over 250k writes its handover before starting any multi-hour job, so a /clear does not have to wait for that job.
- 32 summaries are truncated (over 200 chars). This is a prompt-length habit in hand closures, low priority.

**What worked?**
- All 45 runs are DONE with no failed or blocked events.
- Routing owner asks through the lead, logged first on #715, plus standing approvals S1-S4, kept every push and merge traceable to an owner comment id.
- Verifying a seat's claimed head locally before putting an ask to the owner (diff against the approved head, and `git merge-tree` against main) caught nothing wrong this week, but made each yes cheap.
- Paired-run evidence plus event-level traces (D73 s46, :1610 s46) turned two would-be blind merges into an evidence-based hold (#781) and an accepted, disclosed STOP (:1610).

**Measurement Watchlist** (`docs/agent-monitoring/README.md`):
- `TCK-20260924-DELIVERY-COST-MEASUREMENT` (`gh_calls_per_pr`) is still not checkable. Its recheck waits on TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH, which is not dispatched. No verdict yet; the row stays.
