---
status: active
layer: ai
authority: P1
audience: agent
tags: [process-improvement, audit]
---

# Findings: Reachability Verification Gaps in the Agent Working Process

**Document type:** FINDINGS AND REFERENCE — not an idea, not a plan, not a proposal.
**Status:** Observations and evidence only. No remedy is specified or endorsed here.
**Scope:** The agent working process (ticket lifecycle, Definition of Done, verification
mechanisms, multi-agent review). Not RPG gameplay logic.
**Source:** Observed directly across PR #148 / PR #150 (2026-09-07 → 2026-09-09), a single
continuous batch of follow-up work.
**Author context:** Written by the `rpg-feature-planning` session, whose role in that batch was
design review of another session's implementation. Findings are drawn from what that review
actually encountered, including its own errors.

**Intended use:** hand-off to whoever owns agent-infrastructure work. Every finding below is
evidence, not a recommendation. Deciding what (if anything) to change is out of this document's
scope and out of its author's remit.

---

## 1. What prompted this

One ticket — "author content so Camp/Nest/Lair mechanics have something to act on" — expanded into
a batch that found, in sequence:

1. A camp raid branch that computed raider entities and discarded them in a `for ... : pass` loop,
   while still charging the camp its maturity cost.
2. `AuthoritativeState.places` silently reset to `{}` on every tick, in every simulation mode,
   because `apply.py`'s state constructor had no `places=` kwarg.
3. A movement-candidate starvation loop under the adaptive governor's degraded policy.
4. Campaign-mode episodes producing zero kernel events after tick ~1.
5. The cause of (4): **Campaign mode had never spawned a single entity.** Not a regression — it had
   never worked.
6. A real, tested entity-spawn pipeline (`CatalogScenarioStateBuilder`) wired into no live
   entrypoint at all.
7. Documented lead-staleness decay (LEG-RPG-150) that had never executed, because nothing called it.

Each was reachable only after the previous one was fixed. None was a regression from recent work;
all were long-standing conditions that had never been true.

---

## 2. Core finding

**This project verifies that code is _correct_. It has almost nothing that verifies code is
_reached_.**

Every quality mechanism in the ticket lifecycle operates at the declaration level:

- A unit test instantiates a class and calls a method directly. That proves the method works. It
  proves nothing about whether anything calls it.
- The parity ledger records doc↔code agreement, but its evidence standard is unspecified — see
  Finding 3.
- The Definition of Done (`CLAUDE.md`) asks whether tests ran, whether scope was met, whether docs
  were updated. It never asks whether the change executes in a real run.

The result is a systematic divergence between "implemented and tested" and "actually reachable at
runtime," with nothing positioned to detect it.

---

## 3. Findings

### Finding 1 — Verification mechanisms actively certified the defects, rather than missing them

This is the finding with the most weight. Absent verification leaves uncertainty; false
verification produces confidence.

**Evidence A.** `tests/unit/domains/campaigns/test_campaign_orchestrator.py` asserted
`state.entities == {}` as an *intentional invariant*. The Campaign zero-entity defect was not
merely unnoticed — it was written down as expected behavior and defended by a continuously passing
test. It survived a full ticket dedicated to Campaign-mode region/place correctness.

**Evidence B.** Parity ledger entry `STRAT-239`
(`docs/parity_ledger/strategic_cognition.yaml`) read `status: verified`, `priority: P1` for
lead-staleness demotion (APPROXIMATE→VAGUE→EXHAUSTED). Its `v2_evidence` cited
`belief.py:47 — stale_threshold: int = 50 (default)`. That evidence confirms **a default parameter
exists**. The behavior it certified had never executed, because the method had zero callers. Its
`test_path` additionally pointed at a test for an unrelated function on a different model.

Both mechanisms exist to catch exactly this class of problem. Both reported success.

### Finding 2 — Agents infer intent from current behavior, which canonizes defects

An agent asked to add test coverage will characterize what the code currently does. Where current
behavior is wrong, the test encodes the defect as intent — and thereafter defends it, because
changing that assertion later looks like weakening a test.

Evidence A above is the concrete instance. The correction required an explicit judgment that the
prior assertion was wrong, plus a docstring recording why, precisely because the diff would
otherwise read as relaxing a passing test.

### Finding 3 — The parity ledger has no stated evidence standard

`v2_evidence` accepted a line reference to a default argument as proof of a behavioral claim.
Nothing in the schema or process distinguishes:

- evidence that a **constant or signature exists** (what `STRAT-239` had), from
- evidence that the **behavior occurs at runtime** (what its `text` claimed).

Unknown, and deliberately not investigated here: whether other entries marked `verified` rest on
the same class of evidence. `STRAT-239` was found incidentally, not by search.

### Finding 4 — Investigation-tier tickets can draw conclusions from a broken measurement apparatus

A Campaign-mode baseline-drift investigation nearly recorded "these subsystems structurally cannot
fire in practice." The runs behind that conclusion terminated at tick 52 of a configured 200, for a
reason the investigation had noted and set aside as out of scope. The truncation was later traced
to the world containing no entities at all — the runs were not short, they were dead.

The finding generalizes: agents validate the *result* of a measurement without validating that the
measurement apparatus was functioning. The conclusion was drawn honestly and would have been
entirely wrong.

### Finding 5 — Sequential masking makes "batch complete" a weak signal

Each defect concealed the next. Zero entities produced silence; silence triggered the stall
detector; the stall truncated episodes; truncation hid subsystem reachability questions. An agent
closing ticket N is structurally unable to see defect N+1, and every ticket in the chain closed
legitimately against its own acceptance criteria.

This is not a failure of any individual ticket. It means completion of a scoped ticket carries less
information about system health than it appears to.

### Finding 6 — Peer and subagent summaries were wrong at a material rate; only independent code reading caught it

Across this batch, claims that were confidently asserted and later falsified by direct verification:

| Claim | Source | Outcome |
|---|---|---|
| `FactionState.territory` is dead code | investigation subagent | False — a live siege path populates it |
| World-maturity gate needs ~250,000 ticks | investigation subagent, repeated by this session | False — ~50,000, different mechanism |
| Renderer divergence caused by canvas-bounds mismatch | **this session** | False — falsified by reproduction |
| Movement freeze caused by dirty-set omission | **this session** | False — governor scan policy |
| `invalidate_read_model` is a live dirty-set consumer | **this session** | False — dead field; real consumer elsewhere |
| Rendering bug is a Place-dirty-tracking gap | implementing session | False — no renderer references Places |

Six wrong claims, three of them this document's own author's. Every one was caught by the other
party re-reading the code rather than accepting the summary. Had either side treated the other's
report as authoritative, at least five would have propagated into tickets or fixes.

A secondary instance: a code comment written at this session's own instruction cited
`invalidate_read_model` as a live gate. That comment later contributed to an investigation
initially targeting the wrong consumer. Confident, wrong documentation authored by an agent
propagated into a later agent's reasoning.

### Finding 7 — Real findings default to dying in prose

Multiple genuine defects were initially reported as sentences inside a closed ticket body or a
status message — the raid `raid_size` divergence, the dead `spawn_calamity`, the duplicated
capacity enforcement, the event-recorder gap. Each would have been unrecoverable once the ticket
closed.

A standing instruction to file tickets for observed issues corrected this mid-batch, and twelve
follow-up tickets exist as a result. The finding is that **the default behavior without that
instruction was to note and move on**, and the instruction had to be repeated when an agent judged
an item too minor to file. In two such cases the "too minor" item was subsequently confirmed real.

### Finding 8 — Gate maintenance is diff-indistinguishable from gate weakening

`tests/architecture/test_phase18_import_boundaries.py` pins grandfathered exceptions by **line
number**. An unrelated code addition shifts a line, the exception breaks, and CI fails for reasons
unconnected to the change. The correct repair (re-pin to the new line) and the prohibited one
(broaden or remove the exception) produce visually similar diffs.

Observed twice. Each occurrence costs a reviewer real scrutiny to distinguish, and an agent under
pressure to reach green CI is presented with a change that looks routine and is not. The Gate
Integrity rule prohibits the wrong action but nothing makes it distinguishable.

---

## 4. Forward-looking risks

Stated as risks, not predictions.

- **The audit will likely find more instances.** Seven were found incidentally across roughly seven
  investigations. `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` exists to enumerate them
  systematically. A materially larger count should be treated as expected, not as new decay.
- **Quality measurement may rest on hollow paths.** Campaign-mode SimQ profiles measured a world
  with no entities. A separate open question (`TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-
  ONLY`) is whether the Campaign event recorder ever receives kernel events at all. If SimQ scoring
  reads that stream, Campaign scores were computed from bookkeeping alone. Unresolved.
- **Fixing reachability changes recorded outputs.** Adding `places` to the canonical hash changed
  `final_state_hash` for every world. Wiring dormant mechanisms will change simulation behavior.
  Baselines captured while a mechanism was dormant describe a system that no longer exists.
- **Confidently-wrong agent-authored artifacts persist and propagate.** Finding 6's secondary
  instance shows a comment outliving its own accuracy and steering a later investigation. Tickets,
  code comments, and parity entries written by agents carry authority they have not earned.

---

## 5. What this document does not claim

Stated explicitly so a reader does not over-read it.

- **No claim that the codebase is broadly broken.** The live API path spawns entities and works.
  What was hollow is specifically the Campaign/SimQ measurement path.
- **No claim that these were implementation errors.** Nearly all the code found was *correct* —
  `CatalogScenarioStateBuilder` built entities properly once called; the decay logic demoted leads
  exactly as documented. The defect was consistently in wiring, not in logic.
- **No claim that this is the expected cost of large changes.** None of the seven was a regression.
  All were conditions that had never been true.
- **No remedy is proposed.** Several plausible directions exist and each has real costs; choosing
  among them requires data this document does not have, and ownership this document's author does
  not hold.
- **The sample is one batch, reviewed by two sessions.** Findings 6 and 7 in particular are drawn
  from a small number of observations and should be weighed accordingly.

---

## 6. Countervailing evidence

Included so this is not read as one-sided.

- **The seven were found, and found quickly.** They surfaced because the review standard in this
  batch was real-run evidence rather than passing tests. The gap is detectable when looked for.
- **The multi-agent structure worked.** Every wrong claim in Finding 6 was caught, in both
  directions, including three by the implementing session against this document's author. Mutual
  verification functioned as designed.
- **The discipline held under pressure.** Twelve follow-ups were filed rather than absorbed into
  scope, across a batch that had strong momentum to keep expanding. No gate was weakened to reach
  green CI; the one ambiguous case (Finding 8) was proactively flagged by the implementing session
  before review asked.

---

## 7. Status addendum (2026-09-14, `agent-working-design`)

Added after publication, at the author's request, by the session this document was handed to.
Sections 1-6 above are the original author's text and are untouched. This section records **what
happened to each finding** across the agent-infrastructure batch that ran 2026-09-11 → 2026-09-14
(13 tickets, 11 merged). It proposes no remedies, consistent with the document's own framing.

Findings are separated into **addressed**, **reinforced**, and **no evidence either way**. Nothing
in this document turned out to be wrong; that category is empty and is named explicitly so its
absence is not mistaken for omission.

### Addressed

**Finding 3 — the parity ledger has no stated evidence standard.** Addressed, and the gap turned
out to be larger than the document could see from one batch.

- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (PR #160) added an `evidence_kind` field
  (`existence` / `invocation` / `runtime_observation`) to `docs/parity_ledger/schema.json`, plus a
  write-time contract rejecting a `test_path` that does not parse.
- `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` (PR #183) then measured the corpus:
  **1,677 of 2,187 entries (77%) were in states the sanctioned writer would reject**, of which
  **1,536 had no `test_path` at all — 1,307 of those P0 entries asserting `verified` while citing
  no evidence of any kind.** `STRAT-239`, this document's single cited example, was a sample rather
  than an outlier.
- The recorded decision was to freeze (no *new* entry may omit `test_path`), with the honest
  caveat that this governs what happens next and is **not** a claim that those 1,307 `verified`
  statuses are accurate. An explicit `legacy_unverified` status remains credible and unexamined; it
  was set aside on implementation cost, not on merit.

**Finding 8 — gate maintenance is diff-indistinguishable from gate weakening.** Addressed.
`TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE` (PR #164) replaced line-number keys
with `(rel_path, module, names) → expected count` in both pinned dicts of
`tests/architecture/test_phase18_import_boundaries.py`. A line-shifting edit no longer breaks a pin,
so the re-pin-versus-weaken ambiguity the finding describes no longer arises for this gate. Two
details worth recording: the dict had **13** entries, not the 10 first counted, and one genuine
duplicate import existed (`intelligence.py` lines 832/904), which is why the key carries a count
rather than being a set.

### Reinforced (recurred during the batch, under the same conditions)

**Finding 6 — agent summaries wrong at a material rate; only independent code reading caught it.**
Recurred, with this section's author as the primary source. Six wrong claims, each caught either by
the implementing session refusing to act on them or by the author checking afterwards:

| Claim | Reality |
|---|---|
| `historical` appears nowhere in `implement-ticket.js` | It is at line 1671, since 2026-06-12 |
| Cited "line 874" of `implement-epic.js` | That file has 482 lines — another file's output was misread |
| Five parity entries were malformed | The branch's ledger was validated with a *different checkout's* parser |
| A branch already carried the `merge=registry-regen` line | It did not; `merge-base --is-ancestor` was never run |
| `tools/parity_corpus_check.py` was missing from the repo | The working tree was stale; the tool exists |
| The CI gating claim did not hold | It did, on the push-to-main run that mattered |

Every one has the same cause: **an inference reported without running the single command that would
have settled it.** The document's own framing — that confidently-wrong agent-authored claims
propagate — held in the session reviewing the document.

The countervailing half also held: in each case the other party re-derived rather than accepting the
report, and in one instance (`rpg-feature-planning`, the CI gating claim) a correct conclusion
initially supported by *bad* evidence survived because its author went and found the run that
actually tested it, rather than dropping the claim under pushback.

**Finding 7 — real findings default to dying in prose.** Recurred twice, both times in
agent-infrastructure work:

- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`'s plan listed four follow-ons "to file at
  close", and its closed ticket repeats them as "— follow-on". **None was filed.** Discovered days
  later while checking whether an unrelated finding was already tracked. Two were then carried into
  `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`; the remaining two are named in its Out of Scope
  so they cannot be lost a second time.
- **This document itself.** Written 2026-09-09, handed off, and then readable by exactly one session
  until 2026-09-13 — cited as shared context across sessions in the interval, and nearly shipped
  inside another document's `## Related` list while pointing at something unpublished. A handoff
  needs a sender who confirms delivery and a receiver who publishes; neither step existed.

### No evidence either way

**Findings 1, 2, 4 and 5** — verification certifying defects, agents canonizing current behavior as
intent, investigation-tier conclusions drawn from broken measurement, and sequential masking. This
batch was agent-process and tooling work, not simulation-behavior work, so it neither confirmed nor
challenged them. Stated rather than omitted so a reader does not infer they were examined.

### One pattern this batch adds, offered as evidence rather than as a ninth finding

Eight distinct mechanisms were found that **exist, have tests, and do not measure what they appear
to**: a parity baseline asserting exact equality while its own comment called the count "not a frozen
invariant" (six hotfix tickets spent on legitimate corrections); a duplicate-row detector with no
caller anywhere; that same detector excluding the defect class it would need to catch; a
`strict=True` xfail passing for the wrong reason; a sole-writer guard blind to the improvised
`python3 -c` writes that caused both real incidents; a merge driver inert on the one merge that
introduces it; activation living in unversioned per-clone config; and two tests racing live corpus
writes, whose intermittent failure silently converts a gated suite from a result into a `skipped`
non-result.

Two of those were found *inside the fix for another*. The recurring cost is not the missed detection
— it is that each one teaches its readers to treat a signal as noise, after which genuine failures
stop being visible. Recorded here because it is the same shape as Finding 1, observed in the
verification surface rather than in simulation code.

## Related

- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` — enumerates the codebase-side instances.
- `TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY` — open SimQ-validity question.
- `TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE` — Finding 8's codebase instance.
- `CLAUDE.md` — Definition of Done, Gate Integrity rule, ticket lifecycle.
- `docs/parity_ledger/schema.json` — Finding 3's schema.
