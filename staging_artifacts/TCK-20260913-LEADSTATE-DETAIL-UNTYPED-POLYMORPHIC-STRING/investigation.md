# Investigation — TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING

## The declared-intent check finds an answer, not just a question

Ran the Context Scan (search_docs, then graphify/grep) before treating "which shape should
`detail` be" as an open design question. It isn't fully open: **the Mechanics Bible already
declares it.**

`docs/mechanics/04_strategic_cognition.md`, § "Leads (Knowledge)" (Certified Level 1 Authoritative):

> A `Lead` is a stored piece of information about a resource or location.
> - **Subject**: What the lead is about (e.g., "Iron Ore").
> - **Detail**: Where it is located (e.g., `(45, 12)`).
> - **Certainty**: High, Medium, or Low.

This is the authoritative, already-declared contract: `detail` is a location — a coordinate. Per
`CLAUDE.md`'s own Authoritative Mechanics Rule ("In case of ambiguity... the Mechanics Bible takes
precedence"), convention 1 (parseable `"x,y"`) is not one of three equally-valid options to choose
between — it's the one the Bible already names. Conventions 2 (region_id) and 3 (free text) are
divergences from declared intent, not alternatives requiring a discriminated union to accommodate.

No parity ledger entry (`docs/parity_ledger/strategic_cognition.yaml`) tracks conformance to this
specific Bible line — a real, separate parity gap, noted below.

## Re-counted every producer and consumer, not trusting the ticket's own list (per instruction)

### Convention 1 — coordinates (the declared shape)
**Producers, live today:** `GuildAction.visit()` (`src/town/guild.py`, fixed this batch) →
`BeliefCycleSystem.process_observation()` (`belief.py:181`, passes the coordinate straight
through). Confirmed via this batch's own real corpus-profile runs: this is the *only* real,
reachable, non-test producer of `kind="location"` lead `detail` in the entire codebase today.
**Consumers, live today:** `intelligence.py:419,625`, `redirection.py:92`, `scorers.py:220` — 4
sites, all resolving a material blocker by parsing `detail` as coordinates. All correctly fed by
the one live producer above.

### Convention 2 — exact `region_id` match
**Consumers, live today:** `src/domains/information/phase.py:148`,
`src/domains/information/contradiction.py:60` — both inside `InformationBeliefPhase`, gated
`ENABLE_BELIEF_ASSIMILATION`. Checked reachability directly rather than assumed: this flag
defaults `ON` (confirmed in an earlier batch), so **this consumer code is genuinely live**, unlike
most of what this arc finds.
**Producers: none reachable.** The one plausible producer of a real region_id-shaped `detail`
(`GuideInformationProvider` et al., `src/world/providers/information.py`, e.g.
`detail="north_ruin"`) has zero production callers (confirmed by `TCK-20260912-CAPABILITY-CONTEXT-
REGION-ENEMY-DATA-ALWAYS-EMPTY`'s own investigation). `BeliefCycleSystem.process_rumor()`
(`belief.py:143`) is real and wired, but its only real caller,
`GuildIntelSystem.update()` (`src/systems/social_systems/guilds.py:46`), is itself confirmed dead
code (zero callers, per `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`'s own
Gap 1 finding). **So convention 2 has a live consumer and no live producer** — the inverse of this
arc's usual shape, and worth naming as such rather than folding into "three conventions" as if all
three were symmetric.

### Convention 3 — free narrative text
**The one real, live producer** (`GuildAction.visit()`) was fixed to emit coordinates this batch —
it no longer produces free text. Checked the other candidate producers named in the original
filing for reachability, since "caller-supplied" isn't the same as "actually supplied a real
value":
- `src/domains/information/normalizer.py:66,80` — `detail=details.get("clue_location", "")`.
  Grepped every write to a `"clue_location"` key anywhere in `src/`: **zero.** This producer always
  emits `detail=""` in practice — a separate, real defect (an intended data field that nothing
  ever populates), not a live free-text convention.
- `src/world/providers/information.py` (`GuideInformationProvider` etc.) — zero production
  callers, confirmed above.
- `src/strategy/leads.py`'s `LeadService.create_lead()` — a generic factory taking `detail` as a
  plain caller-supplied string; grepped every call site: **zero real callers anywhere.** Entirely
  unreached, not part of the live picture either.

**So convention 3 is not currently live at all.** It was live only through the one producer this
batch already fixed.

## What this changes about the ticket's own framing

The original filing's "three mutually incompatible conventions" is accurate about what the *code*
contains, but overstates what's *live*. The real, current picture: **one live, Bible-declared
convention (coordinates) with a live producer and live consumers; one convention (region_id) with
live consumers and no live producer; one convention (free text) with no live producer left at all
after this batch's own fix.** This changes the shape of the fix from "design a discriminated union
to hold three real formats" to something narrower: **decide what to do about the region_id
consumers that currently can never match anything real.**

One concrete option, not a decision: `phase.py:148`/`contradiction.py:60` could resolve a
coordinate-shaped `detail` to a real region via `LegalityServiceV2.get_region_for_position()`
(`src/engine/legality.py:44` — the same real, existing machinery `TCK-20260912-CAPABILITY-CONTEXT-
REGION-ENEMY-DATA-ALWAYS-EMPTY` found and declined to wire without a caller) and compare *that* to
`region_id`, rather than expecting `detail` itself to already be a region_id string. That would
make all three real code paths agree with the Bible's own declared coordinate shape and give the
long-dead region_id consumers a real chance to fire for the first time — but it's a design choice,
not a foregone conclusion, and is reported here rather than implemented.

## Typed-shape question, given the above

With only one convention genuinely live and Bible-declared, the "discriminated union per `LeadKind`"
option from the original filing is more machinery than the current evidence calls for. A narrower
option: keep `detail: str` but document and test it as *always* a parseable coordinate for
`kind="location"` (matching the Bible), fix the region_id consumers to derive their own comparison
from it rather than expecting a second format, and treat `PERSON`/`CONCEPT`/`OBJECT`/`EVENT`-kind
leads' own `detail` usage (not investigated in depth here — `lead_routing.py:59` uses `detail`
generically as a routing target for `LOCATION` only) as a separate question if evidence later shows
they need something else. Recommending the narrower option over a new discriminated type, given
what's actually reachable today — but this is exactly the kind of call the ticket's own AC requires
review before acting on.
