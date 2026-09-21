---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Authority

**Purpose/scope.** What makes a proposed world-state transition semantically *authorized* to
occur — as distinct from whether the actor is mechanically able to attempt it (capability),
happens to hold the affected thing (ownership), correctly understands the situation (knowledge),
or merely has the chance to try (opportunity/reach). Authority here is **foundational transition
legitimacy**, not specifically political authority — Politics/authority & war (a later domain)
earns its own, narrower semantics on top of this, per the roadmap's own guardrail against
automatically unifying a foundational concept with a similarly-named later-domain one.

**Status.** Foundational Batch 02, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-2-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

---

## AUTH-01 — Authority is distinct from capability

> An actor may be mechanically able to perform an action (capability) without being authorized to
> (illegal/rejected), and an actor may be authorized to perform an action without currently being
> capable of it. Neither implies the other.

**Disposition: ACCEPT.** This is the core distinction the batch instruction asked to establish,
and it is a genuine two-way finding, not just a restatement of CAUSE-04.

**Repository evidence: SUPPORTED, in both directions.** *Capable but not authorized:*
`LegalityServiceV2` rejects a mechanically-executable attack via `SELF_ATTACK_ILLEGAL` and
`FRIENDLY_FIRE_ILLEGAL` — the actor has every stat needed to land the hit; the action is refused
purely on actor/target-relationship grounds, which is an authority question, not a capability
one. *Authorized but not capable:* a clan leader's authority to resolve a join request
(`clan.leader_entity_id`) is checked and used purely by identity/role — `core_actions.py` never
gates it on the leader's own current combat/stamina capability — while `SKILL_ON_COOLDOWN`/
`INSUFFICIENT_READINESS` show the same repository has a fully separate, well-developed capability-
gating vocabulary elsewhere. The two systems never conflate the questions.

**Scenarios:** [TAR-S06](../scenarios/foundational-batch-02.md#tar-s06),
[TAR-S07](../scenarios/foundational-batch-02.md#tar-s07).

---

## AUTH-02 — Authority is distinct from ownership

> Holding or governing something does not by itself authorize every action on it, and being
> authorized to act on something does not require personally owning it.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `TownResolutionSystem`'s tax/vault mechanics extract gold
from entity inventories and deposit it into a faction vault under governance authority — the
governing system never becomes the *owner* of that gold (Conservation Law RPG-AUTH-003 requires
it always land in a vault or building, i.e., ownership stays with the faction/institution, not the
authority exercising the extraction). Authority to govern and ownership of the governed resource
are two separately tracked things.

**Scenarios:** none yet directly probe this rule; flagged for the future Economy/resources batch,
where governance-vs-ownership content is dense.

---

## AUTH-03 — Authority is distinct from knowledge

> Correctly believing that a transition should occur does not authorize causing it. An actor's
> knowledge or judgment is an input to a decision, never a substitute for the authority check
> that decision's resulting action must still pass.

**Disposition: ACCEPT.** Kept deliberately narrow — this is the Authority-family half of a
distinction OWN-04/OWN-06 and Batch 01's FND-S18 already drew from the Causality/State-Ownership
side (a belief, even a correct one, never becomes committed authority to act).

**Repository evidence: SUPPORTED, by construction rather than by a dedicated check.** Belief/lead
records (`BeliefEntry`, `LeadState`) feed `estimate_threat()`, which informs a decision, but the
resulting proposed action still passes through the same legality/capability gates
(`LegalityServiceV2`) as any other proposal — an entity's confident belief that an attack is
justified does not exempt the resulting attack from `SELF_ATTACK_ILLEGAL`/`FRIENDLY_FIRE_ILLEGAL`
if it happens to target the wrong entity.

**Scenarios:** [TAR-S08](../scenarios/foundational-batch-02.md#tar-s08).

---

## AUTH-04 — Authority is distinct from opportunity/reach

> Having the chance to act — being adjacent, unobserved, or otherwise positioned to attempt a
> transition — does not by itself authorize it. Reach (see `reach.md`) asks *can this subject
> possibly affect that one at all*; Authority asks *is this specific transition legitimate*. Both
> must independently hold.

**Disposition: ACCEPT.** This is the explicit boundary line between this family and Reach,
stated so neither family's future author accidentally absorbs the other's job.

**Repository evidence: SUPPORTED.** `LegalityServiceV2.verify_occupancy`/`is_adjacent` establish
*reach* (spatial opportunity); `SELF_ATTACK_ILLEGAL`/`FRIENDLY_FIRE_ILLEGAL` are checked as a
fully separate condition on top of reach being satisfied — an adjacent, in-range, capable actor
can still have their action refused on authority/legality grounds alone.

**Scenarios:** [TAR-S06](../scenarios/foundational-batch-02.md#tar-s06) (the same scenario as
AUTH-01, since friendly-fire illegality is simultaneously the cleanest evidence for both: reach
and capability are both satisfied, and authority is still what fails).

---

## AUTH-05 — Proposal content alone is insufficient to establish authority

> Transition legitimacy may depend on the acting subject's identity, role, or mandate, the
> surrounding context, the target, and current state — not on the proposed transition's content
> alone. The same proposed content may be legitimate or illegitimate depending on any of these
> factors independently; content alone never establishes authority by itself.

**Disposition: ACCEPT, refined 2026-09-21 — broadened from actor identity alone to the full set
of factors legitimacy may depend on.** The original wording ("Authority is checked on the
actor/transition pair") implied identity of the actor was the only thing beyond content that
mattered. That's too narrow: the repository's own evidence shows *target* and *current state*
independently affecting legitimacy too, not only who the actor is. The key law this rule states
is now the general one — content alone is never sufficient — rather than a specific claim about
which single factor (actor identity) supplies the rest.

**Repository evidence: SUPPORTED, across multiple independent factors.** *Target-relative:*
`FRIENDLY_FIRE_ILLEGAL`/`SELF_ATTACK_ILLEGAL` — the same "attack" content is legitimate against a
hostile target and illegitimate against an ally or self; only who the target is changes.
*Current-state-relative:* combat legality also distinguishes `TARGET_INCAPACITATED` from a fully
active target — the same attack content can be treated differently depending on the target's own
current state, a factor independent of actor identity entirely. Both confirm legitimacy is a
function of several independent factors, never content in isolation.

**Scenarios:** [TAR-S08](../scenarios/foundational-batch-02.md#tar-s08),
[TAR-S09](../scenarios/foundational-batch-02.md#tar-s09) (the positive counterpart: an authorized
actor's proposal does flow into committed state through the authoritative apply path).

---

## AUTH-06 — Authority attached to a role or mandate may survive occupant change, only while that role or mandate remains valid

> Authority attached to a persistent role or mandate may survive occupant change when that role
> or mandate itself remains valid. Succession changing who holds the authority is one possible
> outcome; the role or mandate ending entirely — taking the authority with it — is another. This
> rule does not decide which outcome applies for any specific later-domain institution.

**Disposition: ACCEPT, refined 2026-09-21 — corrected from an unconditional claim to a
conditional one.** The original wording ("the authority persists through a change of occupant")
was too strong: it implied succession *always* happens and the authority always survives. The
repository's own evidence shows the opposite outcome is equally real — when no eligible successor
exists, the role/mandate itself ends rather than persisting indefinitely waiting for one. This is
the Authority-family counterpart to ID-06's succession finding, viewed from the authority side —
and, like ID-06, its job is to state that both outcomes are possible and require explicit
handling, not to assume one.

**Repository evidence: SUPPORTED, for both outcomes.** *Authority survives occupant change:*
`ClanLifecycleService.process_succession()` replaces `leader_entity_id` with a new member's id
(`leader_entity_id_set`) while every mechanism that checks "who is the leader" keeps working
unchanged against the new occupant. *Role/mandate ends instead:* `process_succession()`'s own
docstring confirms it returns `(None, None)` — no succession — when the leader is dead/inactive
and no scoreable member remains, explicitly deferring to `process_dissolution()`, which sets
`dissolved_tick` once the clan has no members and no assets left. The leadership role does not
wait indefinitely for a future successor; it ends with the clan.

**Scenarios:** [TAR-S14](../scenarios/foundational-batch-02.md#tar-s14) (added 2026-09-21 — the
role/mandate ending outcome, directly challenging this rule). Batch 01's FND-S15/FND-S16 remain
the evidence for the succession-survives outcome.

**Open question, per the roadmap's guardrail:** whether *political* authority (a future
Politics/authority & war domain concept) inherits this conditional rule unchanged, or earns its
own refined version — and, more specifically, what makes a political role/mandate "remain
valid" — is explicitly not decided here; the guardrail requires that domain to investigate on
its own rather than assume automatic unification.

---

## Cross-domain links recorded here

- AUTH-02 → Economy/resources (governance vs. ownership of governed resources)
- AUTH-03 → Perception/knowledge/information, Causality (OWN-04/OWN-06, FND-S18)
- AUTH-04 → Reach (the explicit family boundary; see `reach.md`)
- AUTH-06 → Family/lineage & succession, Politics/authority & war (role-persistence through
  succession; explicitly not pre-unified with either domain's own eventual authority semantics)

## Open questions carried forward

1. Whether a currently-incapacitated role-holder (e.g., a wounded or exhausted clan leader) is
   *meant* to retain full, unaffected authority, or whether that is an unintended repository gap
   rather than a deliberate design choice, is not conclusively verified this batch — `core_
   actions.py`'s join-request handling does not gate leader authority on the leader's own combat/
   stamina state, but whether that is correct-by-design or simply unexamined was not settled.
   Flagged as PARTIAL evidence, not resolved here.
2. AUTH-06's open question (does political authority inherit this rule unchanged?) is deferred to
   the Politics/authority & war batch, per the roadmap's guardrail — not decided in advance.
