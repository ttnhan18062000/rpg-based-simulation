# Core RPG Temporal Axis and Automated Life Simulation Proposal

Date: 2026-08-28
Status: brainstorming proposal for review
Scope: the expected simulation after the proposed core-RPG roadmap and accepted Codex idea portfolio are available
Constraint: this document does not approve implementation, change an existing plan, create tickets, or define a player-control system

## Purpose

The current RPG roadmap describes the simulation mainly across space and social containment:

`entity -> relationship/party -> Household/Clan -> Place -> faction -> world/campaign`

That is necessary but incomplete. A living RPG also needs a temporal direction. An entity acts during a moment, follows routines across days, develops across seasons and years, lives through a finite lifecycle, and leaves consequences that may survive into later generations.

Time is not another containment tree. An entity is not located inside exactly one temporal layer. Its lifecycle overlaps immediate action, daily routine, seasonal development, annual path review, generational succession, and historical memory. Relationships, Households, Places, institutions, commitments, and beliefs each have independent lifecycles crossing the same clock.

This proposal defines a manageable temporal foundation for that expected system. It incorporates:

- the planned M1-M6 core-RPG feature set and its M7-M9 validation surfaces;
- the accepted new-idea portfolio, especially Household continuity, commitments, witnessed deeds, and meaningful failure;
- the accepted temporal extensions: anticipation, care burden, functional aging, provenance, rendezvous, neglect, reserves, opportunity windows, cohorts, and anniversaries;
- a real-world human day as the baseline for ordinary activity;
- a compressed fantasy calendar of four 30-day seasons and one 120-day year;
- universal action-duration rules with explicit modifier sources instead of broad attribute-based time scaling;
- an automated entity life path, consistent with the simulation's existing direction, rather than a new direct-control model;
- a path toward simulating complete lives without requiring real-world hours of manual supervision.

## Executive proposal

Adopt one authoritative world clock with the following design:

1. Ordinary human days follow recognizable real-world durations: 24 hours, normal sleep, meals, travel, work shifts, and social time.
2. The fantasy year is deliberately compressed to 120 days: four seasons of 30 days each.
3. A human ages one year after each personal 120-day interval measured from birth, not at the world's shared New Year boundary. Childhood, adulthood, aging, and other long biological arcs therefore use fantasy years rather than Earth-year duration.
4. A tick advances world time; it does not mean that an entity began or completed one action.
5. Activities have human-reference base durations. A universal formula converts those durations into progress and completion ticks.
6. Ordinary attributes do not directly accelerate time. Skills, traits, equipment, conditions, environments, species rules, and supernatural effects may contribute explicit, activity-scoped multipliers through a separate layer.
7. Entities remain autonomous. Minor choices use RPG cognition and local state; major life paths use bounded rules, projects, commitments, values, relationships, and accumulated history. Seeded deterministic interactions still produce emergent, unscripted lives.
8. Days, seasons, years, and lives must be observable at different levels of detail. Stable routine may be summarized or advanced efficiently, while consequential transitions retain individual events and causes.
9. Every time-sensitive feature declares a small temporal contract instead of relying on unrelated hardcoded tick constants.
10. The year becomes the primary balance horizon for lifecycle and major-path change, while days and seasons remain the main horizons for routine and development.

## Design goals

- Make an ordinary human day understandable without consulting arbitrary tick constants.
- Allow an entity to live a whole life and develop a distinct history.
- Preserve autonomous, deterministic-emergent lives rather than authored plot progression.
- Connect short actions to long consequences without building one universal lifecycle state machine.
- Keep numerical balance inspectable at daily, seasonal, annual, and lifetime scales.
- Prevent a generic Speed or attribute score from multiplying every opportunity available to an entity.
- Permit long simulation runs without rendering or narrating every minor tick.
- Make temporal behavior deterministic and compatible with the authoritative mutation pipeline.
- Reuse planned RPG systems rather than invent parallel goal, memory, family, or reputation engines.

## Non-goals

- Designing direct player control, tactical command input, or a final time-control interface.
- Requiring every day, season, or year to contain a scripted event.
- Simulating every real-world human behavior or calendar convention.
- Supporting relativistic time, local time zones, or multiple asynchronous world clocks.
- Making all features safely skippable through one generic fast-forward algorithm.
- Allowing attributes to accelerate all actions, biology, learning, and relationships through one scalar.
- Replacing domain-specific authoritative updates with a generic time mutation.

## 1. Temporal model: one clock, overlapping horizons

### 1.1 Calendar

The proposed human-facing calendar is:

| Unit | Definition | If the current `2,400 ticks/day` baseline is retained |
|---|---:|---:|
| Minor tick | Current authoritative time quantum | approximately 36 seconds |
| Hour | 60 minutes | 100 ticks |
| Day | 24 hours | 2,400 ticks |
| Season | 30 days | 72,000 ticks |
| Year | 4 seasons / 120 days | 288,000 ticks |
| 70-year life | 8,400 days | 20,160,000 ticks |

The 36-second tick and `2,400 ticks/day` conversion are useful initial anchors because they already appear in the authoritative mechanics documentation. They still require an explicit plan-owner decision before implementation because other code currently uses conflicting conversions.

The calendar intentionally has no required twelve-month layer. A season fills the balancing role normally occupied by a month while also carrying environmental meaning. Weeks may exist as a presentation convenience, but no core lifecycle should depend on them initially.

### 1.2 Horizons, not containers

These horizons are approximate orders of magnitude used for reasoning and balance:

| Horizon | Approximate span | Typical concerns |
|---|---:|---|
| Immediate | `1-9` ticks | reaction, movement step, exchange, state transition |
| Encounter | `10-99` ticks | combat, conversation, rescue, short interaction |
| Activity | `100-2,399` ticks | meal, local travel, work session, sleep segment |
| Daily | `2,400` ticks | complete human routine and need balance |
| Multi-day | `2,401-71,999` ticks | recovery, journey, project work, relationship repetition |
| Seasonal | `72,000` ticks | development, economy, ecology, household change |
| Annual | `288,000` ticks | aging, major path review, role and identity transition |
| Lifespan | millions of ticks | complete entity life, succession, accumulated divergence |
| Generational/historical | multiple lives | inherited memory, institutions, Place history, culture |

The boundaries are descriptive rather than exclusive. A promise may be spoken during one encounter, constrain choices for a season, affect reputation for years, and survive in Household memory after the promisor dies.

### 1.3 Independent lifecycles

Each durable subject interprets the shared clock through its own lifecycle:

- Entity: birth -> dependency -> childhood -> adolescence -> adulthood -> elderhood -> death -> remembrance.
- Relationship: unfamiliar -> repeated contact -> trust/commitment -> strain -> reconciliation, separation, or inheritance.
- Commitment: proposed -> accepted -> active -> fulfilled, renegotiated, abandoned, broken, or expired.
- Household: founded -> growing -> stable -> divided or succeeded -> ended or remembered.
- Project: considered -> adopted -> pursued -> interrupted -> completed, failed, or abandoned -> consequence.
- Place: founded -> occupied -> developed -> damaged -> transformed, abandoned, or ruined -> remembered.
- Institution: formed -> legitimized -> staffed -> expanded -> fractured -> dissolved or succeeded.
- Belief/testimony: witnessed -> reported -> accepted or disputed -> distorted -> forgotten or mythologized.

No one lifecycle owns a temporal horizon. A single year can contain transitions in all of them.

## 2. Human baseline

### 2.1 Ordinary day

Human routines should be balanced from familiar daily time rather than derived backward from action cooldowns.

| Activity | Normal adult range |
|---|---:|
| Sleep | 7-9 hours |
| Morning preparation and meal | 1-2 hours |
| Primary work or travel | 6-9 hours |
| Meals and short breaks | 1-2 hours |
| Household responsibilities | 1-3 hours |
| Social, cultural, religious, or personal activity | 1-4 hours |
| Uncommitted or disrupted time | remaining time |

These are reference budgets, not one mandatory timetable. Role, Place, household duties, health, danger, season, and active projects generate routine variations. A farmer, guard, adventurer, child, elder, injured person, and night worker should not receive the same schedule.

The central constraint is that a day totals 24 hours. Adding a new activity requires displacing, shortening, combining, or interrupting another activity. This makes time a meaningful resource without creating a separate action-point economy.

### 2.2 Human lifecycle

Initial review ranges for humans may use familiar life-stage labels but the compressed fantasy year:

| Life stage | Approximate fantasy age | Main simulation concerns |
|---|---:|---|
| Infant/dependent | `0-2` years | care, guardianship, household survival |
| Child | `3-11` years | learning, bonds, place attachment, habits |
| Adolescent | `12-17` years | apprenticeship, identity, responsibility, coming-of-age preparation |
| Adult | `18-59` years | work, projects, partnership, Household, politics, legacy |
| Elder | `60+` years | health, mentorship, succession, memory, institutional continuity |

These numbers are proposed balance anchors, not final content. Lifespan should be a distribution influenced by species, health, injury, danger, and exceptional effects rather than an identical terminal age.

Long biological durations should use fantasy-calendar units consistently. If pregnancy, dependency, education, or aging instead uses Earth-day assumptions while age uses 120-day years, the lifecycle will contradict itself. Exact durations remain future balance decisions, but every one must state whether it is measured in hours, days, seasons, or fantasy years.

Biological age is elapsed age, not the displayed calendar-year number:

```text
age_years = floor((current_tick - birth_tick) / ticks_per_fantasy_year)
```

An entity born one tick before the world's New Year remains a newborn after that boundary. Its birthday and annual personal review occur after its own full 120-day interval. World-level annual reviews may still use the shared calendar boundary. If several transitions share one tick, their order follows the authoritative phase order and must be defined by the owning feature rather than by calendar presentation.

### 2.3 Year as major-path horizon

The year is the preferred balance horizon for major life direction. It does not force one major event each year. Instead, an annual review asks whether accumulated experience is sufficient to continue or change:

- life stage and biological age;
- primary project and role;
- Household position and dependents;
- important relationships and commitments;
- expertise, habits, values, and turning points;
- home, affiliation, loyalty, exile, or migration pressure;
- health trajectory and succession readiness;
- reputation, remembered deeds, and legacy.

Most annual reviews should preserve the current path. Annual review is a consolidation and eligibility horizon, not the only time a major change may occur. Acute changes such as death, displacement, guardian loss, severe injury, commitment breach, or institutional collapse take effect when their events occur. Seasonal reviews may consolidate development or project progress. Annual review handles slow path continuation, coming-of-age eligibility, role reassessment, succession preparation, and other accumulated changes that do not require immediate resolution. This keeps years meaningful without delaying obvious consequences or creating mechanical event inflation.

## 3. Activity duration and universal speed

### 3.1 A tick is an advancement opportunity

An action does not universally cost one tick. Work may have one of five temporal shapes:

1. Atomic transition: a decision or state change resolves at one boundary.
2. Sustained activity: the entity remains occupied for a real duration.
3. Progress activity: each eligible interval contributes work toward completion.
4. Passive process: need, recovery, decay, aging, or memory changes without occupying the entity's primary activity.
5. Reactive event: an interruption or response occurs under an explicitly bounded reaction rule.

An attack recorded in one tick may represent a combat exchange rather than one literal weapon swing. A work shift should not be hundreds of independent work decisions. Sleeping should occupy hours rather than be an instantaneous restorative button.

### 3.2 Universal formula

Each activity kind chooses exactly one of two compatible representations using the human calendar.

For a duration-defined activity:

```text
combined_rate_modifier = product(all applicable validated modifiers)

effective_duration_ticks =
    max(1, ceil(base_duration_ticks / combined_rate_modifier))

```

For a work-defined activity:

```text
effective_work_rate =
    base_work_rate x combined_rate_modifier

complete when accumulated_work >= required_work
```

An activity must not divide a duration by a dimensional work rate or mix the two representations. Atomic authoritative transitions take at least one tick. Fractional durations round upward so a modifier cannot complete work before enough simulated time has elapsed. Progress accumulation and completion ordering must be deterministic.

### 3.3 Attribute boundary

Broad attributes do not directly enter the time formula. They continue to affect the outcomes they already describe, such as capability, damage, capacity, success, available strategies, or fatigue tolerance.

Time multipliers must be explicit and scoped. Examples include:

- a mining skill affecting mining progress;
- a teaching trait affecting instruction;
- a tool affecting a matching craft;
- an injured arm affecting relevant physical work;
- terrain and load affecting travel;
- a species rule affecting aging or recovery;
- a spell affecting a declared family of actions.

A modifier must not accelerate unrelated processes. Combat haste does not accelerate sleep, pregnancy, relationship development, or aging. A crafting skill does not produce more social encounters per day.

Modifier composition requires a cap or diminishing return before multiple modifier sources are introduced. Four apparently modest `1.2x` modifiers already combine to more than `2x`. The first version should support few sources and conservative bounds.

Each modifier declares its source, activity scope, operation, priority/order, minimum and maximum effective value, and stacking group. Zero, negative, non-finite, or undeclared modifiers are invalid rather than alternate meanings such as instant or reversed time. A broad attribute may contribute only indirectly through an explicit derived skill, condition, or feature whose temporal scope is independently declared; there is no automatic attribute-to-time conversion.

### 3.4 Expected action density

Balance should distinguish engine operations from meaningful activities:

| Scale | Expected human activity |
|---|---|
| Minor operations | many movement steps, perceptions, and internal updates |
| Short actions | multiple conversations, transactions, or task operations per day |
| Routine blocks | approximately 3-8 substantial blocks per ordinary day |
| Deliberate path changes | uncommon within a day |
| Major life transitions | evaluated annually, normally much rarer than annual |

No target count should be treated as an absolute quota. The purpose is to prevent a readiness or cadence formula from implying hundreds of narratively major actions every day.

## 4. Automated life-path model

### 4.1 Scope decision

This proposal assumes the simulation remains entity-autonomous. It does not introduce a controllable avatar, manual action queue, or player command system.

Each entity continuously forms behavior from two cooperating levels:

- Minor RPG behavior: needs, beliefs, relationships, memory, skills, local opportunity, personality, risk, and immediate tactics shape near-term choices.
- Major rule-based path: life stage, role, Household, projects, commitments, institutions, species constraints, and accumulated turning points bound long-term direction.

The result is deterministic-emergent rather than scripted: the same seed and inputs reproduce the same life, while interactions among bounded rules produce outcomes that are not authored as a plot. Rules constrain possibility and consequence; they do not prescribe one story. Minor choices accumulate until thresholds and opportunities make a major path transition possible.

### 4.2 Operating loop

```text
perceive current situation
    -> maintain or interrupt current activity
    -> satisfy urgent needs and duties
    -> advance active project or routine
    -> record salient outcomes
    -> update relationships, memory, and pressures
    -> at seasonal/yearly boundaries, review the longer path
    -> continue, adapt, or transition
```

The entity should not reconsider its life purpose every tick. Immediate behavior may run frequently; project selection, relationship consolidation, role change, and life-path review run at progressively slower or event-triggered cadences.

### 4.3 Childhood and low-agency stages

Childhood must generate history without requiring detailed observation of every routine day. A child remains a simulated entity shaped by:

- Household resources and care;
- guardian and mentor relationships;
- home and Place conditions;
- education, apprenticeship, and duties;
- witnessed events and loss;
- health, displacement, and social opportunities;
- emerging habits, values, expertise, and affiliations.

Routine childhood periods should consolidate into seasonal or annual development outcomes. Salient events remain individually recorded. Coming of age should therefore receive an entity with an earned history rather than a generated adult template, while long uneventful intervals remain computationally and narratively compact.

### 4.4 Planning and future control

The existing project/goal structure is the correct conceptual foundation for long autonomous periods. A future player-control layer could influence priorities, risk tolerance, or long-term plans, but that is outside this proposal. The temporal architecture must not depend on such a layer to function.

## 5. Long-horizon execution

### 5.1 Three distinct concerns

Long simulation is not solved by one speed button. It has three separate concerns:

1. Wall-clock throughput: how quickly exact ticks can execute.
2. Autonomous continuity: whether entities can live without external commands.
3. Temporal resolution: whether stable periods can be advanced without evaluating every minor detail.

The second already matches the project's direction. The first is an engine-performance concern. The third is a proposed temporal capability and carries the greatest simulation risk.

### 5.2 Exact fast execution before interval optimization

The lowest-risk first approach is exact fast execution: run the same authoritative ticks as quickly as possible while reducing rendering, telemetry, and narrative volume. Wall-clock speed must not change outcomes.

Safe interval advancement may later optimize explicitly supported processes. It should advance to the earliest known transition rather than blindly skipping a fixed span:

```text
next activity completion
next need threshold
next contract deadline
next routine boundary
next project checkpoint
next seasonal or yearly review
next scheduled world event
```

At that boundary, the normal authoritative transition is resolved and the next boundary is recalculated.

Safe interval advancement is an optimization and therefore requires authoritative parity with exact tick execution for the same seed and inputs. If a process cannot guarantee parity, it is not eligible for this mechanism. A future approximate population or historical model would be a separately named simulation mode with separately declared truth and is outside this proposal.

An interval cannot be considered safe merely because one entity has no scheduled work. Stochastic draws, unknown incoming events, movement into the area, shared-resource contention, and cross-entity actions are possible invalidators. A subsystem may skip an interval only when it can prove the next relevant boundary or provide an exact deterministic closed-form/event-scheduled equivalent. Otherwise it returns to ordinary ticks.

### 5.3 No generic year skip

A universal `advance_one_year()` operation would be unsafe because it could bypass births, deaths, threats, resource exhaustion, relationship changes, witnessed deeds, and competing events. Each participating subsystem must explicitly provide:

- what can be accumulated safely;
- which thresholds can be crossed;
- which external events invalidate the interval;
- what authoritative update represents the result;
- what summary and Chronicle evidence must be emitted;
- evidence that exact-tick and interval results match for the supported case.

Unsupported or unstable domains return to detailed ticks.

### 5.4 Information compression

Executing millions of ticks is not useful if every minor event is presented at equal prominence. Long-run observation should aggregate repeated routine facts while retaining causal exceptions:

```text
Routine summary: completed 43 ordinary apprentice shifts.
Salient event: mentor was permanently injured during a forge accident.
Annual consequence: apprenticeship extended; caution increased; Household income fell.
```

Chronicle, memory, testimony, and simulation-quality events have different purposes. A routine summary does not replace an entity memory, and telemetry visibility does not prove in-world observer legibility.

## 6. Expected RPG system after the planned features

This section describes the target composition, not the current implementation state.

### 6.1 Immediate entity life

An entity has biological needs, health, wounds, stamina, action readiness, perception, beliefs, goals, projects, skills, habits, values, relationships, commitments, role, affiliation, home, and lifecycle stage. It acts from subjective knowledge rather than omniscient world state.

Time connects these mechanisms:

- daily routine budgets needs, work, travel, care, and rest;
- events interrupt routine through actual perceived pressure;
- project outcomes create learning and turning points;
- repeated choices may shape expertise, habits, and retained values;
- injury and failure change future behavior rather than only subtract resources.

### 6.2 Relationship and commitment life

Relationships change through encounters, time, testimony, fulfilled or broken commitments, rescue, caregiving, betrayal, reconciliation, separation, and death.

Accepted Contracts, quests, party duties, promises, favors, and debts may materialize bounded commitments. They compete with immediate utility and survive across days or seasons until fulfilled, renegotiated, abandoned, broken, or expired.

Witnessed deeds prevent reputation from becoming global omniscience. Salient actions propagate from perceiver evidence to testimony, local reputation, and eventually Chronicle or campaign memory.

### 6.3 Family and Household life

Species classification, reproduction, marriage, dependents, coming of age, guardianship, adoption, mentorship, Household membership, shared home resources, and succession form one temporal family arc.

The Household is the durable unit between entity and Clan/faction. It carries membership, residence, shared access, responsibility, succession, and remembered continuity without requiring a full property-law simulator.

Childhood, apprenticeship, partnership, parenthood, elderhood, death, mourning, inheritance, and guardianship operate on seasonal and annual horizons while remaining interruptible by events.

### 6.4 Place, economy, and institution life

The expected Place hierarchy gives spatial identity to homes, settlements, Camps, Nests, Lairs, ruins, resources, institutions, and changing ownership. Temporal behavior gives those Places histories:

- settlement growth and decline;
- seasonal production and scarcity;
- work, vacancy, apprenticeship, and succession;
- transformation, damage, abandonment, and restoration;
- changing ownership, affiliation, and cultural character;
- remembered attachment, exile, return, and political identity.

Travel duration limits which opportunities, relationships, markets, witnesses, and threats an entity can causally reach. Spatial range and temporal budget must therefore be balanced together.

### 6.5 Memory, identity, and legacy

The planned memory/reputation milestone and accepted proposals allow consequences to outlive their initiating event:

- personal memory changes later choice;
- public reputation depends on observation and transmission;
- failure and success create bounded adaptation;
- values and loyalties emerge from costly repeated choices;
- dying wishes, feuds, reputation, Household history, and mentorship cross generations;
- testimony may decay, conflict, or become myth;
- Places and institutions retain selected history;
- Chronicle renders significant continuity without becoming authoritative social knowledge.

This is where the temporal axis meets the roadmap's legacy layer. A death is immediate, Household succession is annual/lifecycle-scale, mourning is seasonal, and inherited reputation may last generations.

## 7. Completed target state and concrete wiring

This section turns the temporal ideas into an expected system contract. Names are conceptual and remain subject to schema review; the important decisions are ownership, data flow, and which facts must be durable.

### 7.1 Architecture decision: shared calculation, domain-owned state

Three approaches were considered:

| Approach | Benefit | Cost | Decision |
|---|---|---|---|
| Each feature owns its own tick logic | Low initial coordination | Repeats current unit drift and incompatible formulas | Reject |
| One generic temporal state machine owns every lifecycle | Maximum theoretical reuse | Centralizes unrelated domain rules and creates a large universal mutation surface | Reject |
| Shared calendar/duration contracts with domain-owned state and evaluators | Consistent units without erasing boundaries | Requires every feature to declare its temporal contract | Adopt |

The completed system has a small shared temporal foundation:

- calendar conversion and boundary queries;
- activity-duration and work-rate calculation;
- explicit modifier validation and composition;
- common temporal-contract vocabulary;
- boundary information used by domain evaluators.

It does not own Household care, retirement, commitments, storage, relationships, projects, or memory. Those domains read shared time calculations and emit their own typed updates through the authoritative pipeline.

The accepted trade-off is some repeated orchestration across domains in exchange for understandable ownership. A generic temporal framework should be reconsidered only if several shipped domains exhibit the same complete lifecycle and update shape, not merely because they all read a clock.

### 7.2 Expected shared data after completion

The completed system needs a small set of configuration records. These are definitions, not per-tick mutable state.

#### Calendar profile

```text
ticks_per_hour
hours_per_day = 24
days_per_season = 30
seasons_per_year = 4
season_order
```

The profile converts named human/fantasy units into ticks and identifies hour, day, season, shared New Year, and personal-birthday boundaries. Core logic should not carry independent `ticks_per_day` constants.

#### Activity definition

```text
activity_kind
occupancy_shape: atomic | sustained | passive | reactive
progress_model: none | duration | work
base_duration_ticks or required_work/base_work_rate
occupancy_channel
interruptibility
valid_modifier_families
completion_effect_kind
summary_category
```

This maps the five conceptual shapes in section 3.1 into data rather than replacing them with a second taxonomy. A progress activity is a sustained activity whose `progress_model` is `work`; another sustained activity may use `duration`. Atomic and reactive transitions normally use `none`, while passive processes keep their rate and update rules in their owning domain. An activity chooses at most one of duration or work semantics; it never mixes dimensional rates and durations.

#### Temporal modifier definition

```text
modifier_id
source_kind: skill | trait | equipment | condition | environment | species | supernatural
activity_scope
multiplier
stack_group
composition_order
minimum_effective_value
maximum_effective_value
```

The modifier catalog prevents a broad attribute or unrelated skill from silently changing elapsed time.

#### Species lifecycle profile

```text
species_id
dependent_years
child_years
adolescent_years
adult_start_year
elder_start_year
expected_lifespan_distribution
reproduction_duration
sleep_baseline
recovery/activity modifier references
```

Human data is established first. Other species extend the same clock through explicit profiles rather than reinterpreting a day or year.

#### Routine profile

```text
role_or_life_stage
preferred activity blocks
minimum need blocks
seasonal variations
allowed substitutions
review cadence
```

Routine profiles generate candidates and constraints, not fixed scripts. Needs, danger, commitments, Household duties, projects, and perceived opportunities may interrupt them.

### 7.3 Expected authoritative state after completion

Only facts needed for future simulation decisions belong in authoritative state.

#### Entity temporal state

- `birth_tick` or equivalent personal-age origin;
- current sustained activity, including kind, start, expected work/duration, progress, and interruption state;
- existing projects, objectives, concerns, commitments, relationships, turning points, health, and lifecycle stage;
- bounded recent seasonal evidence summaries when annual reasoning requires them;
- explicit guardian/care responsibility references where applicable;
- accepted rendezvous or other scheduled commitments;
- cumulative mechanical outcomes such as expertise, habits, values, reputation, and relationship changes.

Derived facts such as displayed age, current season, deadline imminence, reserve coverage, and functional role fitness should be calculated from authoritative inputs rather than stored redundantly.

#### Household temporal state

Assuming Household continuity is accepted, its completed state needs:

- members and dependents;
- home and shared-storage references;
- guardian/caregiver responsibilities;
- reserve policy or target coverage by important resource kind;
- bounded unresolved care/maintenance deficit;
- formation, membership, succession, and ending timestamps;
- current responsibilities whose neglect has mechanical consumers.

It does not need a detailed calendar for every member or a full property-law ledger.

#### Place and institution temporal state

- current type, ownership, services, capacity, and transformation state from the roadmap;
- scheduled or recurring domain events only where they affect decisions;
- explicit staffing/maintenance responsibilities;
- economic reserves where the institution owns them;
- bounded transformation and major-history references;
- vacancies, apprenticeship/succession relationships, and active institutional projects.

#### Historical and observer state

Mechanical state retains bounded evidence required by future decisions. Chronicle, behavior episodes, warehouse summaries, and presentation data retain richer explanations outside the primary decision state. A readable summary must not become an omniscient belief shared by every entity.

### 7.4 Authoritative data flow

Each temporal behavior follows the same boundary while retaining domain ownership:

```text
prior AuthoritativeState
    -> clock boundary or domain event becomes due
    -> owning domain reads known/permitted inputs
    -> shared calendar and duration helpers calculate time facts
    -> owning domain evaluates rules deterministically
    -> typed domain StateUpdate is proposed
    -> normal 37-phase refinement resolves conflicts and conservation
    -> next AuthoritativeState contains accepted outcomes
    -> events feed cognition, testimony, Chronicle, and SimQ as appropriate
```

Shared helpers are pure calculations. They never mutate state. Interval advancement, if later supported, must produce the same domain updates and ordering as the exact ticks it replaces.

### 7.5 How proposed numeric data is determined

No temporal value should be added merely because it sounds plausible. Every value passes through this sequence:

1. **Name the fictional meaning and unit.** For example, hours of care per day or seasons of apprenticeship—not an unexplained tick count.
2. **Choose an anchor.** Human reference, existing tuned mechanic, accepted content definition, or desired lifecycle outcome.
3. **Calculate upward.** Determine its daily, seasonal, annual, and lifetime consequences.
4. **Calculate backward.** Start from the desired number of lifetime roles, projects, relationships, births, or transitions and derive the required seasonal/daily rate.
5. **Check opportunity cost.** Confirm that time used by one activity is unavailable to conflicting activities.
6. **Run ordinary, pressured, and extreme scenarios.** Do not tune only one entity or seed.
7. **Check monotonic rules.** Increasing stored food cannot increase reserve urgency; increasing distance cannot improve time feasibility.
8. **Sweep ranges.** Observe outcome distributions rather than selecting one hand-tuned value.
9. **Promote to data only when variation is required.** A single universal invariant may remain a reviewed default; species, roles, activities, or content variants belong in catalogs.

For example, a three-year apprenticeship contains twelve seasons. If the intended routine is twenty training days per season and six training hours per day, the expected ordinary work is:

```text
12 seasons x 20 days x 6 hours = 1,440 training hours
```

The work requirement can be calibrated around this total. Skills, teaching quality, interruptions, tools, and health provide explicit modifiers or lost hours; a broad Intelligence or Speed stat does not silently halve the calendar.

### 7.6 Temporal extension 1: anticipation and preparation

**Status and owner:** Partial foundation in deadlines, concerns, projects, blockers, subjective knowledge, and temporal pressure. Cognition/strategy owns the new evaluation.

**New durable data:** None initially. Calendar events are shared facts; hidden threats require perceived evidence, beliefs, leads, or commitments already known to the entity.

**Derived logic:**

```text
imminence = clamp(1 - time_remaining / preparation_window, 0, 1)
deficit = clamp((required_amount - available_amount) / required_amount, 0, 1)
preparation_pressure = knowledge_confidence x imminence x deficit x consequence_severity
```

`preparation_window` and `required_amount` must be positive definition values. A condition requiring no preparation produces zero deficit; an event with no positive preparation window is immediate pressure handled by its owning domain rather than this formula. Remaining time is clamped at zero after the deadline.

**Producer:** deadline, seasonal-boundary, known threat, project, or Household-reserve evaluation.

**Update:** a typed Concern or project-score input. Anticipation never directly grants resources or completes preparation.

**Consumers:** strategic project selection, procurement, training, travel planning, Household allocation, and risk evaluation.

**Initial scenarios:** prepare for winter with insufficient food; ignore an unknown invasion; finish a commitment before its deadline; abandon preparation after the predicted threat is disproved.

### 7.7 Temporal extension 2: Household time and care burden

**Status and owner:** New composition of planned Household, dependents, guardianship, caregiving, health, routines, and commitments. Household/cooperation owns allocation; lifecycle owns dependent consequences.

**Derived demand:** care requirement is derived from life stage, health, wounds, and dependency rather than authored separately for every entity. Its unit is **caregiver-hours of effective attention per dependent per day**. Parallel caregivers may divide that requirement, but overlapping attention cannot be counted twice unless the care definition explicitly requires multiple caregivers.

Possible human calibration seeds—not accepted balance values—are:

| Condition | Shared Household care demand |
|---|---:|
| Infant | 6-10 hours/day |
| Young child | 1-4 hours/day |
| Temporarily injured adult | 1-6 hours/day |
| Severely dependent adult or elder | 4-10 hours/day |

**Minimal durable data:** guardian/caregiver assignments, last fulfilled boundary, and a bounded accumulated care deficit. Individual care actions need not be permanently recorded.

**Daily logic:**

1. Derive each dependent's care demand.
2. Find eligible Household caregivers.
3. Allocate available time using responsibility, bond, health, existing commitments, and workload.
4. Reserve or advance care activity.
5. Compare supplied care with required care.
6. Accumulate or reduce bounded care deficit.
7. Emit consequences only after reviewed thresholds.

**Updates:** Household responsibility/allocation, entity routine progress, bounded care deficit, and domain-specific health/development/social effects.

**Consumers:** child development, dependent recovery, trust/attachment, Household cohesion, caregiver fatigue, available work/project time, and observable neglect reputation.

### 7.8 Temporal extension 3: functional aging and retirement

**Status and owner:** Partial overlap with life stages, health, wounds, scars, stamina, roles, expertise, mentorship, apprenticeship, and the planned Empty Chair. Lifecycle owns assessment; role/institution domains own transition.

**New durable data:** No generic `functional_age` score initially. Current capability is derived from existing evidence.

```text
role_fitness =
    age_stage_baseline
    x health_condition
    x chronic_injury_effect
    x role_specific_capability
    x environmental_support
```

The formula evaluates fitness for a role; it does not become a universal action-speed multiplier.

**Producer:** personal birthday/annual review, with immediate reevaluation after permanent injury or severe illness.

**Logic:** compare role fitness, expertise, Household need, personal projects, successor availability, values, and institutional demand. Continue, reduce workload, mentor, change role, suspend work, or retire.

**Updates:** lifecycle/identity/project transition and, only when a role is released, an institutional vacancy signal. Death is not the only vacancy producer.

**Consumers:** apprenticeship, economic vacancy, Household income, mentorship, succession, care demand, and legacy.

### 7.9 Temporal extension 4: bounded temporal provenance

**Status and owner:** New connective requirement reusing world events, project outcomes, turning points, behavior episodes, Chronicle, and campaign timeline. Each domain emits causal evidence; lifecycle consolidation owns bounded mechanical summaries; observer systems own prose.

**Expected authoritative period evidence:**

```text
period_id and covered tick range
entity/Household subject
dominant activity totals
important interruption event IDs
project outcome IDs
fulfilled or broken responsibility IDs
major relationship changes
mechanical deltas
top transition causes
```

**Bound:** retain only the recent summaries required by path decisions—for example, four seasonal summaries—and a reviewed maximum of salient causal references per period. Permanent consequences move into existing turning points, expertise, habits, values, relationships, or reputation. Older readable detail moves to Chronicle/warehouse history.

**Producer:** seasonal consolidation plus immediate salient events.

**Consumers:** annual path review, explanation surfaces, Chronicle, campaign carry-forward, and debugging. Observer prose is derived and cannot modify beliefs or state by itself.

**Failure guard:** `skill +4` is insufficient provenance. The evidence must explain whether the gain came from ordinary practice, mentorship, crisis experience, or another supported cause.

### 7.10 Temporal extension 5: shared availability and rendezvous

**Status and owner:** Mostly new, but it should reuse proposal/acceptance, commitments, Place identity, travel estimation, and activity occupancy. The commitment domain owns the accepted record and its lifecycle; social, project, Household, or institutional domains may propose one for their purpose.

**Expected accepted record:**

```text
participants
place_id
window_start_tick
window_end_tick
purpose
status: proposed | accepted | attended | missed | cancelled | expired
```

This is a commitment subtype rather than an independent social engine.

**Producer and logic:** an owning-purpose evaluator proposes a rendezvous when deliberate coordination is required. Acceptance creates the typed commitment update. Accepted rendezvous are reevaluated when travel feasibility changes and at their opening, closing, or participant-arrival boundaries: propose -> appraise -> confirm travel feasibility -> reserve availability -> require actual co-presence -> attend/miss/cancel/expire -> emit a typed commitment outcome plus any purpose-specific proposal.

**Consumers:** marriage, mentorship, apprenticeship, reconciliation, recruitment, testimony, group expeditions, and institutional meetings.

**Scope guard:** ordinary conversations remain opportunistic. Only deliberate interactions that repeatedly fail without coordination use a rendezvous.

### 7.11 Temporal extension 6: absence and neglect

**Status and owner:** New composition of relationship timestamps, commitments, Household duties, home attachment, projects, and institutional roles. The domain that owns a responsibility also owns its neglect consequence.

**Expected maintenance obligation:**

```text
subject
responsible_entity_id
review_interval
last_fulfilled_tick
tolerance_duration
severity
```

**Derived pressure:**

```text
overdue_ratio = max(0, current_tick - due_tick) / tolerance_duration
neglect_pressure = obligation_strength x overdue_ratio x dependency_severity
```

`due_tick = last_fulfilled_tick + review_interval`. Both `review_interval` and `tolerance_duration` are positive definition values. The obligation becomes due at `due_tick`; pressure is zero through that tick and begins on the next elapsed tick. A zero-tolerance immediate breach is a separate owning-domain event rule rather than an input to this ratio.

**Updates:** concern/commitment pressure first; relationship, Household, health, or institutional consequences only when owning rules cross a threshold.

**Scope guard:** absence alone does not decay every friendship. Neglect applies only to explicit care, protection, mentorship, maintenance, leadership, or close-relationship responsibilities with a real consumer.

### 7.12 Temporal extension 7: seasonal reserves and preparation

**Status and owner:** Planned economy/settlement overlap plus proposed Household shared storage. Household or institution owns policy; existing resource systems own material transfers.

**Expected reserve policy:**

```text
resource_kind
target_coverage_days
minimum_emergency_coverage
known seasonal consumption modifier
```

**Derived logic:**

```text
expected_daily_consumption = known consumers x per-consumer need
coverage_days = available_quantity / expected_daily_consumption
reserve_deficit = max(0, target_coverage_days - coverage_days)
```

Quantities, needs, and coverage targets are non-negative and use the resource system's canonical units. If expected consumption is zero, coverage is treated as sufficient and reserve deficit is zero; invalid negative data is rejected at definition or update validation rather than normalized by this evaluator.

**Producer:** daily/seasonal Household or institutional assessment using real membership and storage.

**Updates:** procurement/rationing/trade/migration/aid Concern or project. All inventory changes continue through conservation-checked resource transactions.

**Calibration:** one-season food coverage is a reasonable winter-preparation experiment, not an accepted universal target. Production, spoilage if introduced, travel, Household size, and risk determine the final value.

### 7.13 Temporal extension 8: opportunity windows and missed chances

**Status and owner:** Partial overlap with expiry ticks, quest opportunities, deadlines, projects, and travel. The opportunity's originating domain owns the window; strategy owns feasibility appraisal.

**Expected window fields:**

```text
available_from_tick
available_until_tick
expected_duration
required_place
reappearance_rule
```

**Feasibility rule:**

```text
estimated_travel_time
+ expected_activity_duration
+ safety_buffer
<= time_remaining
```

An entity should not adopt a known opportunity it cannot plausibly reach and complete. Uncertain travel or duration uses subjective estimates rather than world omniscience.

**Updates:** project candidate score, acceptance/rejection, expiry, delay, or alternate-path evidence. Permanent loss is reserved for genuinely unique opportunities.

### 7.14 Temporal extension 9: generational cohorts

**Status and owner:** New and explicitly outside the completed target until reproduction, childhood, Place history, witnessed events, and cultural memory are stable. If promoted, lifecycle/history consolidation owns derivation; culture or memory must first name a concrete mechanical consumer.

**Derived identity inputs:** birth year, birth Place, childhood Places, and salient shared formative events. Do not author a label such as `war generation` directly.

**Later producer, logic, and update:** a seasonal or annual history-consolidation pass groups entities only when enough members share bounded historical evidence, derives cohort tendencies from that evidence, and allows individual history to override the aggregate. It emits no authoritative cohort update until a reviewed culture/memory consumer proves that repeated derivation is insufficient; until then it may produce observer-only analysis.

**Scope guard:** no new durable cohort registry is justified until a consumer in M5/M6 needs it and derivation cost is measured.

### 7.15 Temporal extension 10: anniversaries and recurring memory

**Status and owner:** New and explicitly outside the completed target as a standalone feature. If promoted, the domain retaining the salient memory or named observance owns evaluation and any resulting update; calendar logic only supplies the recurrence boundary.

**New durable data:** None initially. Derive anniversaries from a retained salient event tick and the calendar.

**Later producer, logic, and update:** a personal-anniversary or named-observance boundary queries only retained eligible events. The owning memory, Household, or Place evaluator checks whether the subject still knows and values the event and may emit its normal typed memory-attention, mourning, ritual-project, or testimony proposal. Calendar recurrence never mutates those domains directly.

**Scope guard:** no global anniversary scan or registry. Only bounded significant memories and named institutional observances are eligible.

### 7.16 Completed autonomous life flow

When the roadmap and proposed temporal features are complete, an ordinary human life can proceed without external commands:

```text
birth creates personal age origin and Household/dependent relationships
    -> daily routine advances needs, care, work, travel, and relationships
    -> known future conditions produce preparation pressure
    -> commitments and opportunity windows compete for finite time
    -> seasonal boundaries consolidate projects, reserves, care, and evidence
    -> personal birthdays update age and review slow life-path eligibility
    -> acute events immediately interrupt and may create turning points
    -> functional capacity and circumstances change roles over time
    -> mentorship, retirement, vacancy, and succession transfer continuity
    -> death resolves commitments, Household membership, mourning, memory, and legacy
    -> later generations inherit only through explicit social and historical paths
```

The expected result is not a scripted biography. The same rules produce different lives because entities encounter different Places, people, needs, knowledge, opportunities, injuries, commitments, and world events. Determinism guarantees replay for the same seed and inputs; it does not make the path authored or uniform.

### 7.17 Wiring acceptance checklist

A temporal feature is ready for later planning only when reviewers can identify:

- authoritative data owner;
- configuration/data source and unit;
- producer trigger or cadence;
- knowledge/perception boundary;
- deterministic decision logic;
- typed StateUpdate owner;
- conflict/conservation refinement path;
- downstream mechanical consumers;
- entity/observer/Chronicle/SimQ visibility;
- exact-run and long-horizon behavior;
- ordinary, pressured, extreme, and boundary scenarios;
- expected daily, seasonal, annual, and lifetime frequency;
- monotonic balance invariants;
- explicit scope guard preventing global scans or unrelated effects.

If any row is unknown, the feature remains a brainstorm candidate rather than an implementation-ready plan.

## 8. Status: existing, planned, and new

### 8.1 Existing or partial foundations

The present repository already contains important foundations:

- authoritative `tick` and `world_time` advancement;
- system cadences and deterministic scheduling;
- readiness, stamina, movement, cooldowns, and multi-tick interaction progress;
- hunger, sleep debt, rest pressure, age ticks, and life-stage concepts;
- projects, objectives, blockers, concerns, and strategic intelligence;
- Contracts, relationships, reputation fragments, beliefs, memory, Chronicle, and campaign episodes;
- ecology, demographics, calamity, Place/Region-adjacent state, and periodic world systems;
- automated entity behavior without a direct-control requirement.

These are foundations, not proof of a coherent temporal model. Several are partial, dormant, duplicated, or calibrated against incompatible tick assumptions.

### 8.2 Planned feature dependencies

The temporal proposal assumes the target defined by the [RPG Design Roadmap](../../plans/rpg_design_roadmap/rpg_design_roadmap.md) and its milestone plans:

- M1 closes correctness, activation, and observable-loop gaps.
- M2 supplies species, population, Clan, ownership, Place-transition, interaction, and cognition foundations.
- M3 supplies reproduction, marriage, dependents, coming of age, and population feedback.
- M4 supplies settlement/institution development, expansion, Clan lifecycle, information hubs, and economic vacancy.
- M5 supplies inherited reputation, feud, dying wish, generational memory, and belief/legacy behavior.
- M6 supplies affiliation change, drifting loyalty, home/place attachment, exile, and refugee identity.
- M7-M9 supply legibility, SimQ mapping, world-corpus reachability, long-run scenarios, and regression evidence.

The accepted [Core RPG New-Idea Portfolio](2026-08-27-core-rpg-new-idea-portfolio.md) extends that target as follows:

| Candidate | Expected temporal disposition |
|---|---|
| A. Household continuity | Independent Household lifecycle across years and generations |
| B. Promises, favors, debts, and oaths | Commitment lifecycle across encounters, days, or seasons |
| C. Witnessed deeds and testimony | Evidence propagation and decay across encounters through generations |
| D. Meaningful failure and adaptation | Event-triggered turning points with bounded recovery/decay |
| E. Values earned through choices | Fold into cognition as slow evidence accumulation |
| F. Personal life projects | Long project templates reviewed seasonally/annually |
| G. Mentorship and technique traditions | Fold into teaching/expertise across seasons or years |
| H. Guardianship and adoption | Fold into M3/Household as event-triggered family transitions |
| I. Caregiving and rescue | Fold into cooperation/recovery at immediate and daily horizons |
| J. Apprenticeship and role succession | Fold into careers/vacancy across seasons or years |
| K. Mourning and death consequences | Bounded post-death effects across days, seasons, and memory |
| L. Conflicting identities and loyalties | Defer until identity substrates exist; use slow accumulated pressure |
| M. Reconciliation and restorative action | Later relationship/commitment proposal lifecycle |
| N. Property, permission, and theft | Deferred cross-cutting ownership work; duration not independently owned here |
| O. Downtime and reflection | Fold into routine and existing recovery cadences |
| P. Local customs and cultural rites | Deferred until culture substrate; normally seasonal/institutional |

Candidates A-C retain independent proposal identities; D is a focused integration; E-P normally fold into or defer behind their named roadmap owners.

### 8.3 Genuinely new temporal capabilities

The following are new proposal identities rather than simple restatements of existing plans:

1. Authoritative calendar vocabulary, including the 120-day fantasy year.
2. A universal activity-duration and explicit modifier contract.
3. Sustained routine blocks tied to a 24-hour human budget.
4. Seasonal consolidation and annual major-path review.
5. Fantasy-year biological aging and human life-stage balance.
6. Temporal contracts for every time-sensitive feature.
7. Long-horizon execution contracts and safe boundary-based interval advancement.
8. Multi-resolution life summaries connecting routine, salient events, Chronicle, and legacy.

Some may become infrastructure rather than player-visible features, but none is adequately owned by the current RPG roadmap.

## 9. Conflicts and required changes

### 9.1 Conflicting calendar constants

The authoritative [World Evolution Mechanics](../../mechanics/05_world_evolution.md) states `2,400 ticks/day`, while raid logic uses `100 ticks/day`. Other systems use raw intervals such as 30, 50, 100, 200, 500, 1,000, 2,000, and 5,000 ticks without a shared calendar meaning.

Required direction: choose one calendar authority and express feature timing through named units or centralized duration data. Existing raw constants must be classified before conversion; their current gameplay behavior should not automatically be interpreted as intended fictional duration.

### 9.2 Aging conflict

Current state uses a default maximum age of `10,000` ticks, while the demographic cohort model uses age-bracket thresholds around `3,000` and `7,000`. Under `2,400 ticks/day`, an entire current life lasts only a few days. These findings and the duplicate life-stage concern are also recorded in the [RPG Design Roadmap](../../plans/rpg_design_roadmap/rpg_design_roadmap.md).

Required direction: represent human age in fantasy-calendar time, reconcile duplicate life-stage representations, and migrate lifespan balance away from direct inheritance of old raw tick thresholds.

### 9.3 Instantaneous routine conflict

Current eating and sleeping behave as one-tick restorative actions, while needs accumulate per tick. This models a consumable effect rather than a human routine.

Required direction: distinguish starting, advancing, interrupting, and completing sustained activities. Need rates and restorative effects must be recalibrated from the daily budget together.

### 9.4 Cadence-duration conflation

A system running every ten ticks does not mean its activity lasts ten ticks. A one-tick state transition may create a season-long commitment. A yearly review may make no change.

Required direction: separately name evaluation cadence, activity duration, cooldown, deadline, persistence, and memory/decay horizon.

### 9.5 Speed conflict

Readiness speed currently controls major-action eligibility, movement uses a different stamina path, and a broad combat `speed` attribute is not a coherent universal duration input.

Required direction: retain domain capability attributes but remove any expectation that they automatically determine elapsed time. The new modifier layer owns explicit rate changes.

### 9.6 Planned-feature timing gaps

The current milestone plans describe what family, settlement, memory, and political features do, but usually not how long they last, how often they evaluate, how they decay, or how they behave during long-run advancement.

Required direction: add temporal-contract review to future plan updates and ticket scoping. This proposal requests those later changes; it does not edit the current plans.

### 9.7 Test-horizon conflict

Existing 5,000-tick runs cannot observe even current elder thresholds, much less a 72,000-tick season or 288,000-tick year.

Required direction: distinguish short exact scenarios, seasonal/lifecycle scenarios, and long-horizon acceleration or interval tests. A feature cannot claim lifecycle coverage from a run that never reaches its first meaningful boundary.

## 10. Temporal contract for future features

Every time-sensitive feature should answer:

| Field | Question |
|---|---|
| Base duration | How long does the activity or state normally last? |
| Calendar unit | Is it expressed in ticks, hours, days, seasons, or years? |
| Evaluation cadence | How often is a decision or threshold checked? |
| Activity occupancy | Does it occupy the entity's current activity? |
| Progress rule | What accumulates and at what base rate? |
| Modifiers | Which explicit modifier families may change the rate? |
| Modifier validation | What are the source, scope, order, stack group, valid range, and effective cap? |
| Interruptions | Which needs or events pause, cancel, or redirect it? |
| Transition | What completes or changes the lifecycle? |
| Persistence | What survives completion, separation, or death? |
| Decay | What weakens, heals, expires, or is forgotten? |
| Downstream effects | Which other lifecycles receive consequences? |
| Long-run support | Exact ticks only, parity-proven safe interval support, or unsupported? |
| Summary/legibility | What is visible to entity, observer, Chronicle, and SimQ? |
| Expected frequency | How often should it materialize per day, season, year, or life? |

This contract should remain small. It does not prescribe one implementation class or generic time engine.

## 11. Balance framework

Balance should be checked in both directions.

### 11.1 Bottom-up

```text
action duration
    -> daily activity capacity
    -> seasonal production and relationship exposure
    -> annual development
    -> lifetime opportunities and legacy
```

An activity that is slightly too fast may become hundreds of extra outcomes per year and thousands across a life.

### 11.2 Top-down

```text
expected lifespan
    -> expected major paths and transitions
    -> years available per path
    -> seasonal progress needed
    -> daily activity budget
```

If a normal entity should plausibly master one or two professions, raise a Household, sustain several important relationships, and complete a few major projects, the daily and seasonal rates must support that target without allowing every entity to master everything.

### 11.3 Core balance surfaces

- sleep, food, work, care, travel, and free-time hours per day;
- distance reachable per hour/day and which Places become accessible;
- routine output and consumption per season;
- skill and project progress per season/year;
- relationship contacts and meaningful changes per season/year;
- commitment creation, conflict, fulfillment, and failure rate;
- births, deaths, coming-of-age, and Household transitions per year;
- major turning points and path changes per life;
- information propagation and forgetting across distance and years;
- population, institution, settlement, and culture change across generations;
- exact-tick throughput and long-run simulation cost.

Balance data should begin with human baselines and a small number of explicit content values. Species and supernatural variations should be added only after the human scenario is stable.

## 12. Proposed feature portfolio and priority

| Proposal | Status relative to current roadmap | Priority | First responsibility |
|---|---|---:|---|
| Calendar authority and 120-day year | New cross-cutting foundation | P0 | Reconcile units and named conversions |
| Human daily/lifecycle baseline | New balance foundation | P0 | Define reference durations and fantasy-year aging |
| Temporal contract | New planning requirement | P0 | Make timing assumptions explicit before feature work |
| Duration/rate formula | Partial concepts, new shared contract | P1 | Base duration plus explicit scoped modifiers |
| Sustained routine activity | Partial routine/interaction overlap | P1 | Work, sleep, meals, travel, interruption |
| Seasonal consolidation | New connective capability | P1 | Development/economy/relationship summaries |
| Annual major-path review | New lifecycle capability | P1 | Continue or transition from accumulated evidence |
| Lifecycle integration | Planned M3/M5 plus new Household ideas | P1 | Childhood through death and succession |
| Long-run exact fast execution | Existing performance direction, new lifecycle target | P1 | Millions of deterministic ticks without presentation overload |
| Anticipation and preparation | Partial deadline/project foundation | P1 | Convert known future pressure into current concerns/projects |
| Household time and care burden | New Household/M3 composition | P1 | Make dependency consume finite routine time |
| Functional aging and retirement | Partial life-stage/Empty Chair overlap | P1 | Derive role fitness and produce non-death role exits |
| Bounded temporal provenance | Partial event/Chronicle overlap, new mechanical summary | P1 | Preserve causes across seasonal/annual consolidation |
| Safe interval advancement | New, high-risk optimization | P2 | Explicitly supported stable processes only |
| Life summaries and temporal legibility | Partial Chronicle/campaign overlap | P2 | Connect routine aggregates to salient causal events |
| Shared availability and rendezvous | Mostly new proposal/commitment extension | P2 | Coordinate important autonomous multi-party activity |
| Absence and neglect | New composition of explicit responsibilities | P2 | Let overdue duties create bounded pressure/consequences |
| Seasonal reserves | Planned economy plus Household storage | P2 | Convert coverage deficits into procurement/rationing pressure |
| Opportunity windows | Partial expiry/project overlap | P2 | Reject unreachable opportunities and preserve missed-path evidence |
| Generational cohorts | New, dependency-heavy | P3/deferred | Derive cohorts only after reproduction/history consumers exist |
| Anniversaries | New, thin memory extension | P3/deferred | Derive recurrence only from bounded salient memories |
| Future player planning/time controls | Not currently required | P3/deferred | Separate future design after autonomous simulation works |

P0 means design authority must be settled before later lifecycle features are balanced. It does not authorize immediate implementation or imply these items should bypass the existing roadmap.

## 13. Suggested integration with the existing roadmap

This proposal should not become a tenth linear milestone that blocks everything. Its responsibilities should be distributed by dependency:

1. Before further M2-M6 balance decisions, settle calendar authority, human baseline, and the temporal-contract vocabulary.
2. M2 features declare their timing and spatial-reach assumptions, especially population, Place transitions, cognition, property, and relationships.
3. M3 owns concrete human/species lifecycle durations, fantasy-year aging, childhood, reproduction, coming of age, dependents, and Household adjacency.
4. M4 owns seasonal settlement, economy, vacancy, apprenticeship, travel, and institutional cadence.
5. M5 owns persistence, decay, testimony, generational transfer, mourning, and historical memory horizons.
6. M6 owns the time needed for affiliation, loyalty, attachment, exile, and refugee identity to change.
7. M7 requires both machine visibility and meaningful temporal/observer legibility.
8. M8 ensures calendar, lifecycle, routine, and seasonal configuration can enter compiled worlds.
9. M9 adds daily, seasonal, annual, lifespan, and multi-generation scenario horizons rather than relying on one tick count.

Household continuity, commitments, witnessed deeds, and meaningful failure should carry temporal contracts when reviewed for promotion. The other accepted portfolio ideas should normally fold into their named roadmap owners rather than become independent temporal systems.

## 14. Review scenarios

### Scenario A: ordinary adult day

A healthy worker sleeps, eats, travels, completes a work shift, handles Household duties, socializes, and returns to sleep. Total activity fits 24 hours. Needs do not force multiple full meals or sleeps every few hours. Minor decisions do not become Chronicle events.

### Scenario B: interrupted routine

A guard begins a shift. A witnessed assault creates an emergency. The shift pauses, travel consumes time, combat resolves at detailed scale, rescue creates a commitment/reputation consequence, and the remaining routine is replanned without adding hours to the day.

### Scenario C: explicit rate modifier

Two otherwise similar miners work for the same duration. One has a relevant skill and better tool, producing more progress through declared multipliers. Neither gains faster aging, sleep, relationships, or unrelated crafting.

### Scenario D: automated childhood

A child lives through several years under a Household and guardian. Ordinary education and duties consolidate seasonally. A parent death, displacement, and mentor bond remain salient individual events. Coming of age consumes this history when selecting a role and project.

### Scenario E: stable year

An adult completes four seasons without a major transition. The annual review records continued role, relationships, and project rather than manufacturing a dramatic event.

### Scenario F: changing life path

Repeated project failure, injury, a Household need, and an economic vacancy accumulate across seasons. At annual review the entity adopts a new apprenticeship. The change is explainable from prior events rather than a random yearly reroll.

An acute vacancy, displacement, or guardian death does not wait for annual review. Its immediate state change occurs on the event tick; seasonal or annual review later consolidates how it changed the entity's longer path.

### Scenario G: death and continuation

An elder dies after a multi-decade life. Active commitments resolve appropriately; Household membership and shared access persist for survivors; mourning affects close bonds; an apprentice may fill the vacancy; witnessed deeds and reputation transfer only through their accepted rules; Chronicle records the significant arc.

### Scenario H: full-life execution

A deterministic human life runs from birth through death across millions of fictional ticks without external commands. Exact fast execution preserves outcomes. Supported stable routines may later use parity-proven interval advancement. Summaries explain years of continuity and every salient interruption has an authoritative causal event.

### Scenario I: time-speed parity

The same seed and inputs run under normal presentation and maximum exact fast execution. State hashes and significant events match. Any safe interval optimization produces the same authoritative result for its declared supported case; otherwise the process is not eligible to skip ticks.

### Scenario J: spatial-temporal reach

An entity cannot work a full shift, visit a distant Place, maintain several local relationships, and return home unless travel time permits it. A faster route or mount changes declared travel rate only; it does not multiply unrelated daily opportunities.

### Scenario K: birth near a calendar boundary

A child is born one tick before the shared New Year. The world enters a new year on the next tick, but the child remains age zero. The child's first birthday and personal annual review occur only after 288,000 elapsed ticks, with deterministic ordering if another lifecycle event shares that tick.

### Scenario L: compressed pregnancy and reproduction

A human pregnancy uses an explicitly reviewed number of fantasy seasons rather than an accidental Earth-day or raw-tick constant. Conception, interruption, birth, Household membership, population-cohort feedback, guardian responsibility, and the newborn's personal birthday remain consistently ordered.

### Scenario M: interval contention

Two entities depend on the same limited resource while a third may enter the Place. The system refuses interval advancement unless it can preserve exact deterministic contention and arrival ordering. It returns to detailed ticks rather than awarding the resource twice or ignoring the incoming entity.

### Scenario N: simultaneous transitions

A work activity completes on the same tick that hunger becomes critical, a commitment expires, and a seasonal boundary occurs. The authoritative phase order produces one deterministic result, no transition is applied twice, and the temporal summary preserves the actual cause order.

### Scenario O: nonhuman lifecycle

A nonhuman species declares different aging, sleep, recovery, or activity modifiers through species-scoped rules. The human calendar remains the reference clock, the species does not inherit human lifecycle durations accidentally, and its modifiers do not affect unrelated domains.

## 15. Main risks and safeguards

| Risk | Safeguard |
|---|---|
| One universal time engine becomes too large | Shared vocabulary and formula; domain lifecycles remain separate |
| Millions of ticks are computationally impractical | Exact fast execution first; bounded interval support by subsystem |
| Fast execution or interval optimization changes outcomes | Require parity; unsupported cases return to ordinary ticks |
| Every year forces artificial drama | Annual review permits but does not require transition |
| Short year creates biological contradictions | Measure all long biology in declared fantasy units |
| Speed bonuses create runaway opportunity | No broad attribute scaling; scoped modifiers with composition bounds |
| Routine automation hides meaningful life | Aggregate repetition, retain salient causal events |
| Temporal constants remain scattered | One calendar authority and named duration data |
| Features become globally high-frequency | Declare expected materialization frequency and impact range |
| Spatial expansion ignores travel budget | Review distance and time together |
| Childhood remains empty or expensive | Seasonal development plus event-level exceptions |
| Chronicle becomes omniscient memory | Keep observer, entity knowledge, testimony, summary, and telemetry distinct |

## 16. Decisions accepted in this brainstorm

- Time is an overlapping axis/fabric, not a containment layer.
- The ordinary human day uses recognizable real-world behavior and 24 hours.
- One fantasy year contains four 30-day seasons, totaling 120 days.
- A human biologically ages one year per fantasy year.
- The year is the primary lifecycle and major-path balance horizon.
- Actions do not universally cost one tick.
- Activity duration uses a universal formula and explicit modifier sources.
- Broad attributes do not automatically scale activity time.
- Entity life paths remain automated and deterministic-emergent through minor RPG behavior and major bounded rules.
- Direct player control and command design are deferred.
- A complete life may span millions of ticks; presentation and long-run execution must not require manual action-by-action attention.
- Existing and planned RPG systems should be connected through temporal contracts rather than replaced by a new monolithic engine.
- Shared calendar/duration calculation should be reused while authoritative state and transition logic remain owned by their domains.
- Anticipation, Household care burden, functional aging/retirement, and bounded temporal provenance are P1 temporal extensions.
- Rendezvous, explicit neglect, seasonal reserves, and opportunity windows are P2 extensions folded into their owning domains.
- Generational cohorts and anniversaries remain deferred until their named consumers and prerequisites exist.

## 17. Decisions still requiring review

- Whether the existing 36-second tick remains the final minor time quantum.
- Exact human life-stage boundaries and lifespan distribution.
- Fantasy-calendar duration of pregnancy, recovery, education, apprenticeship, and other long activities.
- Initial routine-block data and role-specific schedule templates.
- Modifier stacking rule and maximum non-supernatural rate.
- Which processes first qualify for safe interval advancement.
- Which exact equivalence evidence is sufficient before a subsystem may use interval advancement.
- How campaign episodes and the continuous world clock relate across inactive periods.
- How much historical detail remains in authoritative state versus Chronicle/warehouse summaries.
- Long-run performance targets for one life, one Household generation, and a populated world.

## Requested updates after review approval

If this proposal is accepted, maintainers should later review—not automatically edit—the current RPG proposal and plan documents for the following changes:

1. Add the temporal axis beside the existing spatial/layer model.
2. Add the 24-hour day, four-season/120-day year, and fantasy-year aging decisions.
3. Add a temporal contract to feature review and future ticket scope.
4. Recalculate M3 lifecycle assumptions and all existing raw age thresholds.
5. Add seasonal and annual horizons to M4-M6 feature expectations.
6. Add long-run exact fast execution, interval-support classification, and temporal summaries to the roadmap's infrastructure considerations.
7. Expand M9 scenarios beyond fixed short tick counts to daily, seasonal, yearly, lifespan, and generational boundaries.
8. Cross-link the accepted Codex new-idea portfolio so Household, commitments, witnessed deeds, meaningful failure, caregiving, apprenticeship, mourning, and personal projects receive explicit time behavior.
9. Record direct player control as deferred and avoid making autonomous lifecycle simulation depend on it.
10. Add the shared-calculation/domain-owned-state architecture and the wiring acceptance checklist to future temporal feature reviews.
11. Route the ten temporal extensions through their named M2-M6 and Household owners rather than creating one universal time epic.

No current brainstorm, plan, ticket, code, or agent record is modified by this document.

## References

- [Core RPG New-Idea Portfolio](2026-08-27-core-rpg-new-idea-portfolio.md)
- [Core RPG Feature Review](2026-08-27-core-rpg-feature-review.md)
- [Core RPG Plan and Brainstorm Update Request](2026-08-27-core-rpg-plan-brainstorm-update-request.md)
- [Brainstorm-to-Plan Crosswalk Review](2026-08-27-brainstorm-plan-crosswalk-review.md)
- [RPG Design Roadmap](../../plans/rpg_design_roadmap/rpg_design_roadmap.md)
- [M2 Foundational Systems](../../plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md)
- [M3 Family, Species, and Adult Life](../../plans/rpg_design_roadmap/rpg_m3_family_species_epic.md)
- [M4 Beyond the City](../../plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md)
- [M5 Memory, Reputation, and Legacy](../../plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md)
- [M6 Political Identity and Belonging](../../plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md)
- [World Evolution Mechanics](../../mechanics/05_world_evolution.md)
- [Minimal Deterministic Kernel](../../engine/contracts/minimal_kernel.md)
