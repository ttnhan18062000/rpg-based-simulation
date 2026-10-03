# External AI Review — Session-Layer Working Process

## Reviewer position and review boundary

I am an **external AI reviewer**. I do **not** have direct access to the repository, its runtime environment, the live Claude Code sessions, the actual hook payloads, the current branch/worktree state, or the historical incidents except through the review document provided to me.

This review therefore distinguishes three categories explicitly:

1. **Source-grounded observations** — conclusions supported directly by the supplied `session_layer_working_process.md`.
2. **External architectural inference** — conclusions I derive from the described system using general software architecture, control-plane, workflow, RBAC/capability, distributed coordination, and agent-system design principles.
3. **Assumptions requiring verification** — claims that depend on the actual Claude Code harness, repository implementation, operating environment, or runtime behavior and therefore should not be treated as verified facts until the proposed spike or repository evidence confirms them.

I am reviewing the **session-layer architecture and rollout plan**, not the RPG simulation logic, workflow internals, or the quality of individual Claude Code agents.

---

# 1. Executive assessment

The proposed session layer addresses a **real architectural layer that already exists operationally but is currently encoded informally**.

The supplied evidence shows that approximately seven long-lived interactive sessions already have distinct domains, functions, worktrees, handover behavior, ownership expectations, and peer communication paths. The current coordination model relies heavily on per-machine memory, manually typed instructions, handover notes, and the human owner acting as router and scheduler.

The plan therefore does **not** appear to be inventing an orchestration abstraction prematurely. It is formalizing behavior that already exists.

The central architectural direction is sound:

> move repeated session identity, ownership, routing, worktree, and boundary instructions from conversation into repo-versioned configuration.

This matches the stated purpose of turning session setup from conversation into configuration while preserving the user's authority over genuinely human decisions.

I recommend continuing with the session-layer direction.

However, I would change several important parts of the design **before implementation tickets are created**, primarily around:

- separation of responsibility versus authority,
- session identity,
- manifest trust boundaries,
- stale-session handling,
- routing durability,
- concurrency semantics,
- the scope of v1.

My largest concern is that the current `session_roles.yaml` design risks becoming a **god registry** containing identity, ownership, runtime topology, permissions, routing, and user authorization at the same trust level.

My preferred conceptual architecture is:

```text
Human owner
    |
    | policy / authority
    v
Session control plane
    |
    +-- role identity
    +-- responsibility / ownership
    +-- capability
    +-- authority
    +-- routing
    +-- session binding
    +-- runtime placement
    +-- state / observability
    |
    v
Long-lived interactive sessions
    |
    v
Existing agents / workflows / tools
```

The session layer should remain a **thin control plane**, not become another workflow engine.

---

# 2. Evidence that the problem is real

The strongest part of the plan is the problem statement.

The document provides multiple concrete incidents:

- role information distributed across multiple memory files;
- stale ownership information causing a misroute;
- shared memory causing role confusion after context loss;
- SessionStart being unable to determine which handover belongs to the current session;
- a batch merged while tickets remained `inprogress`;
- severe worktree and branch accumulation causing disk exhaustion;
- session role names leaking into the `agent` monitoring vocabulary;
- the human owner functioning as both router and clock.

These incidents are not all the same problem.

They fall into several distinct architectural categories:

```text
Identity problem
    session does not reliably know who it is

Responsibility problem
    ownership information is stale or ambiguous

Authority problem
    what a session may do is scattered or conversational

Lifecycle problem
    context reset, handover and batch completion are informal

Routing problem
    sessions require the human to resolve destination and liveness

Runtime placement problem
    branches/worktrees are not sufficiently inventoried

Observability problem
    role identity and existing agent identity are conflated
```

That decomposition matters because the solution should not collapse those categories into one undifferentiated role file.

---

# 3. Domain × function decomposition

## Assessment

I support the proposed decomposition:

```text
Role = domain + function-set
```

with reusable function templates, reusable domain overlays, and small role-specific entries.

This is preferable to one independently maintained prompt or role card per session.

The current roster is intentionally sparse, which is also a positive property. The design does not force every domain to have plan/design/implement/review roles when that organizational distinction does not currently exist.

## Why I think this decomposition is correct

This separates two relatively orthogonal questions:

```text
What kind of work does this actor perform?
        function

What semantic area is this actor responsible for?
        domain
```

That allows policies such as:

```text
implement
    may edit implementation
    performs Finalize
    owns branch delivery duties
```

to be defined once, while:

```text
rpg
    owns simulation paths
    reads Mechanics Bible
    obeys simulation-specific gates
```

is also defined once.

This is structurally more resistant to drift than maintaining seven largely duplicated role documents.

## Where this model is likely to break first

My concern is not the composition itself.

The likely failure mode is that the role entry becomes an escape hatch:

```yaml
role:
  special_case_1:
  special_case_2:
  special_case_3:
  ...
```

until most meaningful behavior lives in per-role overrides.

If that happens, the abstraction would technically remain `domain × function`, but operationally the project would be back to manually maintained role definitions.

### Recommendation

Treat per-role differences as **exceptions**, not the normal policy layer.

The validator or roster review should surface role-specific complexity, for example:

```text
number of role-level overrides
number of routes unique to one role
number of authority exceptions
```

Not necessarily as a blocking metric, but as a warning that the composition model may be drifting.

---

# 4. The role manifest should not become a god registry

The current sketch includes:

```yaml
domain
functions
session_name
worktree
worktree_writer
owns
owns_not
may_write
routes
handover
needs_user
grants
```



Those fields represent at least four different concepts.

I recommend the architecture explicitly distinguish:

```text
1. Identity
2. Responsibility
3. Capability
4. Authority
```

For example:

```text
Role
 ├── identity
 │    domain
 │    functions
 │
 ├── responsibility
 │    semantic ownership
 │    routing destination
 │
 ├── capability
 │    tools
 │    readable/writable paths
 │
 └── authority
      push
      merge
      workflow execution
      destructive operations
      governing-file changes
```

This distinction is more important than whether they physically live in one YAML file or several.

A session may own a **decision** but not be permitted to implement it.

Another session may be allowed to implement a change without owning the semantic decision.

For example, the supplied roster already demonstrates this distinction:

- design/review roles can own direction;
- implementers perform the actual commits;
- the user retains merge and governance authority.

The schema should represent that distinction directly rather than relying on prose interpretation.

---

# 5. Authority and grants require a stronger trust boundary

This is the most important design change I recommend.

The plan proposes storing standing grants in the manifest as dated and quoted user grants.

The intention is good:

```text
peer messages cannot manufacture authority
only user-originated grants count
```

However, there is a security/control-plane concern if the same repository configuration that says:

```text
this role may push
```

can be modified by the actor whose permission is being evaluated.

Even if process rules say such a modification requires user confirmation, architecture should avoid allowing an actor to modify its own authority source unnoticed.

Conceptually:

```text
subject
    should not control
policy deciding what subject may do
```

## Recommendation

Separate authority from ordinary descriptive role configuration at least conceptually, and preferably mechanically.

Possible structure:

```yaml
roles:
  rpg-implementer:
    responsibility: ...
    capability: ...
```

and a protected authority section or separate file:

```yaml
authority:
  rpg-implementer:
    commit: true
    push:
      standing_grant: batch-delivery
    merge: false
    governing_files: false
```

I am **not** asserting that two physical files are required.

The requirement is:

> authority configuration should have a higher trust boundary than normal roster configuration.

This could be achieved by:

- separate file ownership,
- a protected section,
- a hard PreToolUse restriction,
- a literal-user-confirmation requirement,
- or another repository-native mechanism.

---

# 6. Advisory-first enforcement should be split into two classes

The document proposes advisory enforcement first, followed by hardening only after measuring recurring violations.

I agree with this approach for **semantic and organizational boundaries**, but not for every authority boundary.

These should initially remain advisory:

```text
wrong semantic owner
editing a neighboring domain
unusual route
handoff formatting
possible responsibility overlap
```

They are context-dependent and prone to false positives.

However, some boundaries are deterministic and high consequence:

```text
merge without authority
remote branch deletion
governing-file modification
editing the authority policy itself
destructive repository operations
```

For these, waiting four weeks for violation telemetry does not provide much architectural value.

### Recommendation

Explicitly divide enforcement into:

```text
semantic boundaries
    advisory-first

authority / destructive boundaries
    hard from the start
```

This preserves the repository's report-first philosophy where ambiguity exists without weakening controls that have clear semantics.

---

# 7. Role and session instance should be different concepts

The plan currently defines a session as a running instance of a role and proposes refusing a launch if the same role name already appears to be live. 

The immediate operational reason is understandable:

```text
two writers on one branch/worktree are dangerous
```

However, this risks encoding:

```text
one role == one process
```

as an architectural truth.

I recommend the model instead become:

```text
Role
    |
    +-- Session instance A
    +-- Session instance B
```

with explicit concurrency policy:

```yaml
role: rpg-implementer

concurrency:
  max_sessions: 1
  writer_slots: 1
```

Today both values might be one.

That is fine.

The advantage is that the architecture is then saying:

```text
concurrency is currently forbidden by policy
```

rather than:

```text
the role and the process are the same entity
```

This matters later if the system introduces read-only clones, investigations, overflow sessions, or multiple isolated branches under the same semantic role.

The truly exclusive resources are likely to be:

```text
branch
worktree writer slot
possibly active batch
```

rather than the role itself.

---

# 8. Session identity should not primarily depend on human-readable session names

This point is partly an **external architectural inference** and partly a **runtime assumption that must be verified in M0**.

The plan relies on:

```text
--name
SESSION_ROLE
--agent
SessionStart
```

to identify a role at runtime.

I recommend treating these differently:

```text
session_id
    runtime identity

role
    logical identity

session_name/session_title
    display identity

agent_type
    configuration validation signal
```

The stable binding should conceptually be:

```text
session_id -> role
```

not:

```text
session_name == role
```

A human-readable name is useful operationally but should not carry the full security or ownership semantics of the role.

### Assumption requiring M0 verification

I am assuming the harness exposes a sufficiently stable unique runtime session identifier across the lifecycle events needed by this design.

The supplied document states that `SessionStart` includes `session_id`; I have not independently observed that runtime in this repository.

If the runtime semantics differ, the exact implementation must change while preserving the conceptual distinction.

---

# 9. Resume outside the launcher is an important failure mode

The plan focuses on:

```text
cc <role>
```

and launcher-mediated resume.

A real user can potentially resume a session through a native path that bypasses the launcher.

That creates a question:

```text
How is role identity recovered if SESSION_ROLE was established only by the launcher?
```

The current fallback of injecting nothing for an unknown role is safe, but it weakens the goal of reliable full-session automation.

## Recommendation for M0

Add tests for:

```text
launcher start
session exits
native resume without launcher
role recovery
```

If role information is naturally persisted by the harness, use it.

If not, consider a small runtime binding record such as:

```text
session_id
role
manifest_revision
worktree
created_at
```

The precise storage location should be chosen based on existing repository conventions.

---

# 10. Manifest revision should become part of session state

The plan correctly recognizes staleness as a primary failure mode and proposes a staleness sweep for invalid paths, roles and references.

However, there is another form of staleness:

```text
session starts under manifest revision A

manifest changes to revision B

session resumes while its context still contains assumptions from A
```

Re-injecting a new role card is helpful, but it does not guarantee that stale policy already present in the context will be ignored.

## Recommendation

Bind a session to a manifest revision or digest.

Example conceptual runtime metadata:

```text
session_id
role
role_manifest_revision
```

On SessionStart:

```text
if current manifest revision != bound revision:
    report that role configuration changed
    show the relevant semantic diff
    refresh the binding
```

Different changes may require different treatment.

Example:

```text
documentation/path update
    refresh context

authority reduction
    force explicit re-evaluation before privileged action
```

This directly addresses the supplied evidence that role information can become stale extremely quickly.

---

# 11. Path ownership is useful but cannot fully represent semantic ownership

The motivating failure included a content-versus-tooling split around the same registry concept.

The proposed solution remains largely path-oriented:

```text
owns
owns_not
routes
```

That will work for most repository boundaries.

However, if one physical artifact carries multiple semantic concerns, path globs cannot fully represent ownership.

I do **not** recommend line-level ownership. That would be brittle and operationally expensive.

Instead, consider an optional semantic ownership primitive:

```text
subject
```

Example:

```yaml
subjects:
  mechanism-registry-content:
    owner: rpg-feature-planning
    artifacts:
      - registries/mechanisms.yaml

  mechanism-registry-tooling:
    owner: agent-working-design
    artifacts:
      - tools/mechanism_registry/**
```

Routing can then resolve:

```text
explicit semantic subject
        first

path ownership
        fallback
```

This should remain optional.

Most files should continue to be routed by paths.

Use semantic subjects only where the repository genuinely has content/tooling or policy/implementation splits that cannot be represented cleanly by filesystem ownership.

---

# 12. One-bounce routing is good for ownership disputes

The rule:

```text
one bounce, then the user
```

is a sensible protection against silent peer-to-peer ping-pong.

I recommend keeping it.

However, the plan currently mixes two different situations:

```text
A. recipient is not the owner

B. recipient is the owner but currently unavailable
```

These should not have the same resolution.

For an ownership dispute:

```text
A -> B
B rejects ownership
one corrected route
then human escalation
```

is reasonable.

For availability:

```text
owner known
owner session offline/busy
```

the system should preferably retain the request durably rather than escalating the human simply because a terminal is inactive.

This distinction becomes more important as the project moves toward full automation.

---

# 13. Add a minimal durable inbox before attempting auto-wake

The document correctly defers automatic wake behavior because actual runtime behavior is unresolved. 

I agree with deferring auto-wake.

But there is a missing primitive between:

```text
real-time SendMessage
```

and:

```text
human remembers that another role needs work
```

I recommend a very lightweight durable message queue or inbox.

For example conceptually:

```yaml
id:
from_role:
to_role:
type:
artifact:
request:
created_at:
status:
```

with statuses such as:

```text
pending
acknowledged
resolved
```

This does **not** need to be a new orchestration engine.

It can be a small file-backed mailbox, reuse existing handover infrastructure, or another existing repo-native mechanism.

Its purpose is only:

```text
do not lose cross-session work because the receiving interactive process was not awake
```

If live messaging works, it remains the fast path.

When a session starts or resumes, it can check pending messages.

This improves:

- offline recipient handling,
- post-clear recovery,
- crashes,
- long-running busy sessions,
- owner visibility into pending work.

---

# 14. The message envelope is slightly over-specified for v1

The proposed envelope contains:

```text
type
batch
needs_user
artifact
asked
bounce_if
```



The concept of typed peer messages is useful.

However, I would question whether `bounce_if` belongs in every message.

Ownership/bounce policy is part of the routing architecture.

If every sender independently encodes the condition for rerouting, process knowledge is duplicated into conversational payloads.

A smaller envelope may be sufficient:

```yaml
type:
from:
to:
batch:
artifact:
request:
needs_user:
```

Then routing policy remains centrally defined.

This better matches the project's stated principle of defining information once.

---

# 15. Batch Finalize is one of the strongest sections

The batch rules are well motivated by the incident where code was merged while tickets remained in progress.

The explicit rule:

> a batch is not done until Finalize ran

is the correct direction.

I recommend making the implied lifecycle explicit enough for status tooling to derive:

```text
dispatched
    |
acknowledged
    |
implementing
    |
PR open
    |
PR green
    |
finalized
    |
merged
```

The important semantic distinction is:

```text
PR green != batch complete
```

Finalize remains part of completion.

I agree with avoiding a separate batch registry in v1 if the existing PR and ticket artifacts already contain sufficient durable state.

The goal should be to **derive**, not duplicate.

---

# 16. Worktree and branch management is useful but not session-layer core

The worktree and branch incident is real and severe: the document reports hundreds of branches, several gigabytes of worktrees, and a disk-full incident blocking a push.

The proposed tooling is generally conservative:

- status is read-only;
- pruning is dry-run by default;
- backup mappings are written first;
- open/recent/checked-out branches are skipped;
- remote deletion remains user-approved.

I support those principles.

However, I would make two changes.

## 16.1 Commit-subject equivalence should never establish deletion safety

The plan already recognizes this heuristic as imperfect.

Under squash merges, rebases, edited commit messages, and differently reconstructed patches, commit-subject equivalence does not prove that a branch is safely integrated.

Use it only as:

```text
informational hint
```

not:

```text
deletion eligibility
```

Strong deletion evidence should come from exact PR/head relationships, sufficiently reliable Git equivalence, or explicit human confirmation.

## 16.2 Worktree hygiene should not block v1

The disk incident justifies building this tooling.

But it is primarily:

```text
repository hygiene / operations
```

rather than the core architectural proof of the session layer.

If scope must shrink, branch pruning and worktree retirement should move later without delaying:

```text
role binding
routing
authority
handover
session startup
```

---

# 17. Observability should focus on whether human orchestration actually decreases

The plan proposes:

- misroutes,
- bounces,
- idle stalls,
- handoff latency,
- batch cycle time,
- role-boundary warnings,
- `/clear` count,
- context re-read cost.

These are all potentially useful.

For the first version I would reduce the primary metric set.

Suggested core measures:

```text
1. misroute count/rate
2. manual owner intervention count
3. dispatch -> acknowledgement latency
4. dispatch -> finalized latency
5. role-boundary violations
```

The metric I think is missing is the most direct business metric for the session layer:

```text
manual orchestration actions per completed batch
```

Examples of human orchestration actions:

```text
telling a session its role
correcting an ownership route
telling a session which worktree to use
waking a peer manually
repeating a permission boundary
recovering a lost handover
telling a role where to send a question
```

The purpose of this project is not simply to produce more metadata.

Its success should be measurable as:

```text
fewer repeated human coordination actions
```

`/clear` token cost can remain a secondary optimization metric.

---

# 18. M0 is correct, but it should test more lifecycle cases

I strongly support the existence of M0.

The document itself correctly labels several platform facts as unverified and requires positive controls before building against them.

That is good architecture practice.

The currently proposed tests are valuable.

I would add four more:

```text
f. start via launcher, then resume outside launcher

g. rename the live session after launch

h. fork a session and observe role/session identity behavior

i. modify the role manifest between launch and resume
```

These test whether the conceptual distinction between:

```text
role
session identity
display name
agent definition
manifest version
```

survives real lifecycle behavior.

### Assumption

I am assuming the runtime provides enough hooks or stable session metadata to implement a reliable role binding.

That must remain an assumption until M0 demonstrates it.

---

# 19. Proposed milestone restructuring

The current sequence is:

```text
M0 harness spike
M1 manifest
M2 launcher
M3 routing
M4 worktree/branch hygiene
M5 advisory boundaries
M6 observability
M7 first-month review
```



I would preserve the general progression but restructure responsibilities slightly.

## Suggested sequence

```text
M0 — Runtime spike

Verify:
- session identity
- resume behavior
- clear behavior
- fork behavior
- agent definition behavior
- hook information
- idle messaging
- path/tool interception behavior
```

```text
M1 — Role model and registry

Deliver:
- identity/responsibility/capability/authority schema
- role composition
- validator
- migration of memory notes to pointers
```

```text
M2 — Session binding

Deliver:
- launcher
- role binding
- own-handover injection
- manifest-revision tracking
- duplicate/conflicting writer detection
```

```text
M3 — Routing and durable handoff

Deliver:
- route command
- message convention
- one-bounce ownership rule
- durable pending inbox / acknowledgement
```

```text
M4 — Operational visibility

Deliver:
- what is active
- which role owns what
- branch/worktree/current batch status
- Finalize visibility
- disk warnings
```

```text
M5 — Boundary enforcement

Deliver:
- hard authority boundaries
- advisory semantic boundaries
- role-boundary monitoring
```

```text
M6 — Repository hygiene

Deliver:
- branch pruning
- worktree retirement
- cleanup assistance
```

```text
M7 — Evidence review

Use measured data to:
- simplify rules
- harden useful advisory checks
- remove unused configuration
- retire unused roles
```

This keeps repository cleanup valuable but prevents it from expanding the critical path of the session-layer architecture.

---

# 20. Recommended v1 scope

The current plan is somewhat broad.

A minimal version that proves the architectural hypothesis only needs to answer:

```text
Who am I?

What do I own?

What am I allowed to do?

Where should I work?

Who owns something outside my boundary?

What work is currently pending for me?

What state survives /clear or resume?
```

Therefore my recommended v1 is:

```text
1. role schema + validator
2. launcher
3. session-id-to-role binding
4. role-aware SessionStart
5. own-handover-only injection
6. route lookup
7. minimal durable peer handoff
8. basic authority boundary enforcement
```

The following can reasonably follow later:

```text
full branch pruning
automatic worktree retirement
expanded retro analytics
policy ratchets
automatic waking
advanced concurrency
```

This would reduce implementation risk while testing the core hypothesis quickly.

---

# 21. Architectural invariant: control plane, not workflow engine

I recommend adding this explicitly to the design:

> **The session layer is a control plane for long-lived interactive sessions. It is not a second workflow engine.**

The session layer should know:

```text
identity
responsibility
authority
routing
placement
session lifecycle
handover state
coordination state
```

It should not own:

```text
feature decomposition
implementation algorithms
domain decisions
test strategy internals
workflow phase internals
simulation semantics
```

Those remain in the existing planning, workflow, agent, ticket and domain systems.

The supplied document already has the right non-goal direction: it says the layer should extend rather than replace the agent/workflow layer and should reduce repeated instructions rather than remove human authority.

I recommend elevating that from a non-goal into an explicit architecture invariant.

---

# 22. Review of the specific questions in the document

## 22.1 Domain × function composition

**Recommendation: retain it.**

Four function templates plus domain overlays is a strong default decomposition.

Monitor per-role exceptions so role entries do not gradually become independent policy documents.

---

## 22.2 Repo-versioned role manifest

**Recommendation: retain a repo-versioned source of truth, but refine its model.**

Do not treat all fields as one class of information.

Separate conceptually:

```text
identity
responsibility
capability
authority
runtime placement
```

Path globs should remain the default ownership mechanism, with semantic subjects available only for known intra-file or cross-cutting ownership splits.

---

## 22.3 Advisory-first enforcement

**Recommendation: partially retain.**

Use advisory-first for semantic/process policy.

Use hard enforcement immediately for deterministic authority/destructive boundaries.

---

## 22.4 Launch-time role binding

**Recommendation: retain the launcher, but do not use the display name as the root identity.**

Prefer:

```text
session_id -> role
```

and use name/title for human usability.

Add stale manifest detection and direct-resume tests.

---

## 22.5 Routing

**Recommendation: retain static ownership plus runtime liveness.**

Keep the one-bounce rule for ownership disputes.

Do not escalate merely because the owner is offline.

Add a small durable mailbox or pending-handoff mechanism.

---

## 22.6 Grants and authority

**Recommendation: retain explicit user-originated standing grants, but give them a stronger trust boundary.**

Do not allow the authority subject to silently redefine the authority policy controlling itself.

---

## 22.7 Worktree and branch hygiene

**Recommendation: the proposed conservative ceiling is appropriate.**

Dry-run, backup, exact safeguards, and human approval for destructive shared actions are sensible.

Do not use commit-subject equivalence as proof of safe deletion.

Move this outside the minimum session-layer critical path if necessary.

---

## 22.8 Observability

**Recommendation: reduce the initial set.**

Prioritize:

```text
manual orchestration interventions per batch
misroutes
dispatch/ack latency
dispatch/finalize latency
boundary violations
```

The `/clear` efficiency metrics can remain secondary.

---

## 22.9 Phasing

**Recommendation: retain M0 first.**

Then prioritize:

```text
role model
session binding
routing/handoff
authority
```

before advanced hygiene and long-term metrics.

---

# 23. Assumptions made by this external review

The following statements are **assumptions**, not facts established by repository inspection.

## A1. The incident descriptions are accurate

I assume the incidents, branch counts, worktree usage, misroutes, and workflow behavior described in the supplied document are accurate representations of the repository.

I have not independently reproduced them.

---

## A2. The current roster is approximately stable

I assume the seven-session roster is representative enough to design against:

```text
rpg-feature-planning
rpg-implementer
agent-working-design
agent-working-implementer
test-architecture-reviewer
test-architecture-implementer
world-rule-catalog-design
```

If sessions appear and disappear daily, a manifest may need a more dynamic model.

The document describes the roster as small and relatively stable, so I am reviewing under that assumption.

---

## A3. Sessions are long-lived enough that persistent role identity matters

I assume these are not disposable one-task agent processes.

The document describes them as long-lived interactive sessions with context resets, handovers and cross-session communication.

If instead sessions become mostly ephemeral, part of this design may become unnecessary.

---

## A4. Session identity can be obtained reliably from the runtime

I assume there is a usable stable session identifier available to hooks or runtime tooling.

This must be tested in M0.

If not, another binding mechanism will be required.

---

## A5. Native resume/fork/rename behavior may bypass launcher assumptions

This is an architectural risk I am inferring.

I do not know whether the actual harness preserves sufficient role metadata automatically.

That is why I recommend explicit M0 tests rather than assuming the failure exists.

---

## A6. Repository-level authorization can be meaningfully enforced by hooks/tool policy

I assume hooks or agent tool allowlists can reliably prevent at least some classes of clearly forbidden operations.

The exact strength and semantics of this mechanism are not verified by me.

If the harness cannot strongly enforce them, the authority recommendations remain conceptually correct but need another enforcement mechanism.

---

## A7. Runtime liveness is not the same as durable ownership

I assume a role can be the correct owner while its interactive session is offline, idle, cleared, or busy.

Therefore I recommend separating routing from availability.

---

## A8. The project wants incremental automation, not autonomous governance

The document repeatedly states that the user retains authority over merges, governing-file edits, major workflows and destructive operations.

My recommendations assume this remains a project invariant.

If the long-term goal changes to fully autonomous governance, the authority model would require a substantially different design.

---

## A9. Existing workflow/agent systems remain authoritative below this layer

I assume the current ticket pipeline, workflows, agent definitions, monitoring system and delivery process remain in place.

The session layer should coordinate **between interactive sessions**, not replace those systems. The supplied architecture explicitly states this boundary.

---

## A10. Token efficiency matters materially

The document states that token efficiency can be preferred even at some time cost and gives context-reload behavior as a measured concern.

My recommendation for short role cards, define-once configuration and narrow context injection assumes this remains an important project objective.

---

# 24. Items I would require the planner to resolve before child-ticket implementation

Before implementation tickets are finalized, I would ask the planner to resolve these seven architecture decisions explicitly.

### 1. Separate the role model into conceptual layers

At minimum document:

```text
identity
responsibility
capability
authority
runtime placement
```

even if some share one physical YAML file.

### 2. Define the authority trust boundary

State precisely:

```text
who may edit grants/authority
how such changes are recognized as user-approved
what happens if an unauthorized role attempts to modify them
```

### 3. Define role versus session-instance semantics

Specify whether:

```text
one role may have multiple session instances
```

even if v1 sets `max_sessions: 1`.

### 4. Define the stable runtime binding

Specify the authoritative mapping:

```text
runtime session identity -> logical role
```

and what happens after resume, clear, rename, fork and launcher bypass.

### 5. Add manifest-revision handling

Specify what happens when a live or resumed session's role definition changed since it began.

### 6. Separate ownership dispute from owner availability

Keep one-bounce escalation for ownership disagreement.

Create durable pending work for a known but unavailable owner.

### 7. Shrink the v1 proof

The first release should prove:

```text
zero repeated role setup
correct ownership lookup
stable role identity
reliable handover
correct authority boundaries
reduced human routing
```

before expanding into repository hygiene and sophisticated analytics.

---

# 25. Final architectural conclusion

The project already has a de facto session layer.

Today it is encoded in:

```text
human memory
Claude memory
handover files
terminal naming conventions
worktrees
peer messages
typed instructions
```

That is why the failures described in the document are recurring coordination failures rather than isolated mistakes.

Formalizing the layer is justified.

The strongest architectural form of this proposal is not:

```text
a smarter multi-agent orchestrator
```

but:

```text
a thin, repo-versioned control plane for persistent AI development sessions
```

Its job should be limited to:

```text
who the session is
what it is responsible for
what it may do
where it operates
where it routes work
what state survives context loss
what requires human authority
```

The existing ticket, workflow, subagent and implementation layers should continue deciding **how the actual engineering work is performed**.

I would proceed with the initiative after revising the design around seven points:

1. separate identity, responsibility, capability and authority;
2. protect authority/grant configuration with a stronger trust boundary;
3. separate logical roles from runtime session instances;
4. bind roles to stable runtime session identity rather than primarily to names;
5. track manifest revision and stale-session state;
6. add durable cross-session pending work and separate availability from ownership disputes;
7. reduce v1 to the smallest control-plane slice that demonstrates lower human orchestration.

With those changes, the proposed layer has a clear architectural boundary and a credible path toward AI-first development automation without prematurely turning the repository into a general autonomous orchestration platform.
