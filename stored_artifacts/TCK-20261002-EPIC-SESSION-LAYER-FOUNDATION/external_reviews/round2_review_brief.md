You are the **local planning/design agent** for the session-layer working process.

This is a **second-round external AI architecture review** of the current `session_layer_working_process.md`.

The external AI reviewed the updated plan after the first review had already been dispositioned. It does **not** have direct access to the live repository/harness beyond the supplied review document, so:

- treat repository-local evidence as stronger than the external review;
- do not blindly adopt an external recommendation if repo evidence contradicts it;
- keep anything that still depends on actual Claude Code/harness behavior explicitly gated on M0;
- however, if the external review identifies an internal contradiction in the plan itself, fix the contradiction rather than deferring it to M0.

Do **not implement** any session-layer code, hook, launcher, registry, or ticket in this task.

Your job is:

1. inspect the current plan and relevant existing repository contracts;
2. evaluate the external review points below;
3. update the plan where appropriate;
4. perform a consistency pass across the entire plan after those edits;
5. produce **one summary file only** describing what changed and any remaining questions/comments.

Do not create implementation tickets yet.

---

# External AI review round 2 — required items to evaluate

## 1. Rework session identity and binding

The external reviewer accepts the distinction between:

- logical role;
- runtime session instance;
- human-readable session name.

However, it challenges the current choice of:

```text
session_name -> role
```

as the authoritative binding across `/clear`.

The updated plan currently relies on a claim that duplicate `--name` sessions are automatically renamed to a variant such as `rpg-implementer-2`.

The external reviewer checked current official Claude Code documentation and reports that multiple local sessions may instead share the same human-readable name, with other identifiers used to disambiguate them.

Therefore:

### Re-check the actual platform evidence

Do not assume either the external review or the current plan is correct.

Use the already planned M0 tests as the source of runtime truth.

Before M0, the design should avoid relying on uniqueness of `session_name`.

### Preferred conceptual model

Keep:

```text
role
    logical identity

session_id
    current runtime instance

session_name / session_title
    UX / recovery signal
```

A `/clear` creating a new runtime `session_id` is not itself a problem.

The role can be resolved again for the new runtime instance.

Continuity should primarily come from:

```text
role configuration
+ role handover
+ batch state
```

rather than requiring a permanent process identifier across clears.

### Investigate signal precedence

M0 should determine which of these signals are actually stable enough:

```text
agent_type
SESSION_ROLE
session_title
session_id
```

Do not prematurely make `session_title` the root of identity.

A reasonable candidate model to test is:

```text
SessionStart
    -> resolve role from trustworthy available signals
    -> bind current session_id to resolved role
    -> write runtime binding record
```

The binding record remains observational/runtime state, not the canonical role definition.

### Concurrency

Do not enforce the one-writer invariant primarily by inspecting process names.

The actual exclusive resource is the writer access to a worktree/branch/batch.

Prefer an explicit runtime writer lease/lock or an equivalent repository-native mechanism.

Also inspect the current schema:

```yaml
placement:
  worktree_writer: agent-working-implementer
  concurrency:
    max_sessions: 1
    writer_slots: 1
```

If a non-writer design role carries `writer_slots: 1`, the resource is modelled at the wrong level.

`max_sessions` belongs naturally to a role.

The writer slot belongs naturally to the worktree/resource.

Fix this conceptual inconsistency.

---

## 2. Fix authority failure semantics

The external reviewer agrees with the new split:

```text
semantic / organisational boundary
    advisory-first

authority / destructive boundary
    hard boundary
```

Keep that distinction.

However, the current plan says both:

```text
authority is fail-closed
```

and:

```text
if the PreToolUse hook cannot parse the tool input, fail open
```

Those statements are incompatible for privileged actions.

### Required correction

For an operation that falls into the authority/destructive class:

```text
classified forbidden
    -> deny

classified as requiring user authority
    -> ask / require user confirmation

classified allowed
    -> continue according to policy

classification/parsing uncertainty
    -> ask, not silently allow
```

If Claude Code's actual hook API does not support this exact behavior, M0e should record that and the design must choose the cheapest safe fallback.

Do not claim "fail-closed" unless the actual mechanism supports the claim.

### Define the threat model

The plan should explicitly distinguish:

#### Guardrail threat model

The system protects against:

- agent mistakes;
- stale role context;
- accidental destructive commands;
- permission drift;
- ordinary model behavior taking an action outside the configured authority.

#### Adversarial-shell threat model

A process with arbitrary shell execution deliberately trying to bypass the hook using indirect commands, wrappers, scripts, another executable, or modified policy files is a different security problem.

Unless the repository has OS-level isolation or equivalent enforcement, do not imply that `PreToolUse` is an adversarial security sandbox.

Describe hard authority boundaries accurately as deterministic agent/runtime guardrails within the actual platform threat model.

---

## 3. Reconsider the pinned authority digest

The first review recommended a stronger authority trust boundary.

The updated plan introduced:

```text
registries/session_authority.yaml
```

plus a hash/digest pinned outside the worktree under the user's home directory.

The external reviewer agrees with separating authority from ordinary role configuration, but questions whether the external digest is a real trust boundary.

### Core issue

If Claude Code runs as the same OS user and can write arbitrary files under that user's home directory, then:

```text
repo file
+ $HOME digest
```

are two filesystem locations but not necessarily two security principals.

That mechanism may be useful for accidental tamper/drift detection without being a true root of trust.

### Required action

Define what this mechanism is supposed to protect against.

If it is mainly:

```text
accidental drift / unauthorized plan-level mutation
```

describe it as tamper evidence / integrity guardrail.

Do not overstate it as cryptographic authority isolation.

Also inspect whether authority decisions depend only on `session_authority.yaml`.

They may also depend on:

```text
role
functions
capability
generated agent definition
authority
```

If the digest remains in the plan, consider whether the correct thing to digest is a **canonical session-policy bundle**, not just the authority file.

However, do not expand v1 unnecessarily.

It is acceptable to defer the external hash pin as defense-in-depth if the basic governing-file + deny/ask authority mechanism already provides the required v1 control.

Record the decision and reasoning.

---

## 4. Separate message delivery from message authorization

The update to section 9.5 is directionally useful:

- ownership dispute is separate from unavailable owner;
- cross-session wake behavior is M0-gated;
- a minimal durable inbox exists only if the platform's own delivery is insufficient.

Keep those ideas.

However, the external reviewer identifies a new distinction:

```text
message delivered successfully
!=
message is authorized to cause work
```

If a role session is launched with:

```text
crossSessionInbound = accept
```

that may solve reliable delivery.

It does not automatically enforce this repository's topology.

The plan currently states a hub-and-spoke structure:

```text
implementer
    -> own planner/designer
    -> other domain planner
```

Yet any peer able to send a message may potentially send an actionable request to another role.

### Required addition

Define inbound message semantics by message type/source.

A candidate model:

```text
finding / fyi
    may be received from any known session role

question
    may directly reach the named semantic owner when appropriate

request / handoff / dispatch
    actionable only from authorized upstream roles

peer message
    never creates user authority
```

Do not necessarily hard-block this in v1 unless evidence justifies it.

But the role card/routing contract should distinguish:

```text
delivery
routing
authorization to dispatch work
```

### Planner availability

The external reviewer also challenges making the planner a bottleneck for purely informational cross-domain traffic.

Consider allowing:

```text
finding
question
```

to go directly to the known owner across domains.

Keep:

```text
dispatch
work assignment
handoff that changes another role's queue
authority decision
```

through the appropriate planner/design hub.

The intended topology then becomes approximately:

```text
information may bypass the hub
work assignment may not
```

Evaluate this against existing repository behavior before adopting it.

---

## 5. Run a full internal-consistency pass

After applying or rejecting the architecture changes above, re-read the **entire plan**, not only the changed sections.

The external review found several likely stale contradictions introduced by incremental edits.

At minimum check all of these.

### 5.1 Canonical location of session-role configuration

The plan currently appears to mention both:

```text
registries/session_roles.yaml
```

and:

```text
agent-orchestration/sessions/
```

as if each is the canonical home.

Choose one canonical source of truth.

If `agent-orchestration/` is already the provider-neutral orchestration contract and the session layer is intentionally part of that contract, putting the session contract under:

```text
agent-orchestration/sessions/
```

may be cleaner.

If not, retain `registries/session_roles.yaml`.

But there must be only one canonical definition.

Any secondary representation must be clearly:

```text
generated
indexed
or referenced
```

rather than another source of truth.

### 5.2 Standing grants wording

Find and fix stale wording such as:

```text
the user edits the manifest
```

if authority has moved into `session_authority.yaml` or another dedicated authority source.

### 5.3 Section 12 open questions

Remove or rewrite stale questions whose decisions were already made.

For example, do not simultaneously say:

```text
authority boundaries are hard from day one
```

and still list:

```text
advisory only at first?
recommendation: advisory
```

as an unresolved question.

### 5.4 Deferred items

Do not list:

```text
hard enforcement of boundaries
```

as deferred if hard authority boundaries are explicitly part of v1.

Clarify that only later hardening of **semantic** boundaries is deferred.

### 5.5 Milestone M5

If M5 now contains hard authority enforcement plus advisory semantic enforcement, rename or rewrite the milestone accordingly.

Do not keep a milestone named only:

```text
Advisory boundaries
```

if that no longer describes its deliverable.

### 5.6 M0 description

The spike now contains substantially more than five checks.

Remove stale wording such as:

```text
the five verified facts
```

if tests are now labelled a-m.

### 5.7 M6 / M7 dependency

Check the current statement that expanded M6 analytics may happen "after M7".

If M7 depends on:

```text
M6 + four weeks
```

that is impossible.

Separate:

```text
minimum M6 measurement needed for M7
```

from optional later analytics if necessary.

### 5.8 Monitoring source of `session_role`

The plan currently allows launcher bypass and says the role can be recovered at SessionStart.

If monitoring still reads `session_role` solely from:

```text
SESSION_ROLE
```

then resumed sessions that bypass the launcher may lose correct attribution.

Prefer:

```text
SessionStart resolves the role
    -> writes resolved runtime binding / sidecar

monitoring
    -> reads that resolved per-session binding
```

`SESSION_ROLE` may be an input signal but should not be the sole source if launcher bypass is supported.

### 5.9 Batch metrics

The plan correctly says:

```text
PR green != batch done
batch done requires Finalize
```

Therefore do not define:

```text
batch cycle time = dispatch -> PR green
```

unless it is explicitly called implementation/PR latency.

Prefer:

```text
batch cycle time = dispatch -> finalized

implementation latency = dispatch -> PR green

finalization latency = PR green -> finalized
```

if all three are useful.

### 5.10 Manual orchestration metric

Keep:

```text
manual orchestration actions per completed batch
```

as the headline outcome metric.

But do not use raw:

```text
user prompts per role per batch
```

as if every user prompt were undesirable orchestration.

The architecture explicitly wants:

```text
fewer repeated instructions
not fewer genuine user decisions
```

Count or sample categories such as:

```text
role reminder
routing correction
manual wake
worktree correction
boundary reminder
handover recovery
```

Do not penalize legitimate owner decisions, design feedback, or new requirements.

### 5.11 `route.py <path-or-topic>`

The current deterministic routing model is based mainly on:

```text
owns
owns_not
routes
path globs
```

The decision to reject semantic `subjects` for v1 is reasonable if there is no demonstrated need.

But if there is no deterministic "topic" ownership model, do not advertise:

```text
route.py <path-or-topic>
```

Either define what a `topic` is, or reduce v1 to path / explicit route-key lookup.

Do not smuggle semantic routing into an unspecified free-text model.

---

# Specific previous-review dispositions

Do not reopen every first-round decision.

The following first-round outcomes remain reasonable unless new repo evidence contradicts them:

- keep domain × function composition;
- report per-role override creep;
- separate identity / responsibility / capability / placement / authority;
- authority configuration receives stronger governance than ordinary role metadata;
- semantic boundaries are advisory-first;
- role and runtime session instance are separate concepts;
- manifest revision/staleness is surfaced;
- no semantic `subjects` abstraction in v1 without evidence;
- ownership dispute and owner unavailability are separate;
- `bounce_if` stays removed;
- batch lifecycle is derived rather than stored in a second batch registry;
- commit-subject equivalence is informational only;
- branch/worktree hygiene is not part of the core control-plane proof;
- the session layer remains a thin control plane, not a second workflow engine.

The purpose of this round is to make the updated architecture **internally coherent and aligned with actual runtime semantics**, not to redesign everything again.

---

# M0 handling

Anything that depends on actual Claude Code/harness runtime behavior must remain a spike result, not a planning assertion.

In particular, keep explicit verification for:

- identity signals after startup/resume/clear/compact;
- `/clear` runtime session-id behavior;
- duplicate names;
- rename;
- fork;
- launcher bypass;
- `--agent` behavior;
- `PreToolUse` command/path matching;
- behavior on parsing/classification uncertainty;
- cross-session inbound accept/hold/refuse behavior;
- wake behavior;
- dialog expiry;
- prompt-submit payload if still used for metrics.

If official documentation and prior local observations disagree, M0 should record the actual local behavior and the plan should be updated from that evidence.

---

# Scope discipline

Do not expand this task into implementation.

Do not:

- write launcher code;
- write hooks;
- create session-role files;
- create authority files;
- create inbox tooling;
- create branch-pruning tooling;
- change Claude settings;
- create implementation tickets.

This task is **plan correction and architecture cleanup only**.

After the plan is internally consistent, stop.

---

# Required final artifact

After updating the plan, create **exactly one new summary file**.

Do not create multiple review files, investigation files, disposition files, or implementation tickets for this task.

Suggested name:

```text
session_layer_external_review_round2_summary.md
```

The summary should be concise and self-contained.

It must contain:

## 1. Changes made

For each meaningful change:

```text
- what changed;
- where in the plan;
- why it changed;
- whether it came from external review, repo evidence, or consistency cleanup.
```

## 2. External-review points not adopted

For anything you intentionally reject or adapt rather than adopt:

```text
- external suggestion;
- decision;
- repository evidence / architectural reasoning;
- whether M0 could change that decision later.
```

Do not hide disagreements.

## 3. Remaining assumptions / unverified platform behavior

List only things that still depend on M0 or runtime evidence.

Clearly separate them from decided architecture.

## 4. Remaining questions for the owner or external AI

Only include questions that genuinely require a decision or further review.

Do not include resolved questions simply because they appeared in an earlier version of the plan.

## 5. Readiness statement

End with one of:

```text
READY FOR M0 TICKETING
```

or:

```text
NOT READY FOR M0 TICKETING
```

If not ready, list the exact blockers.

---

# Final response behavior

Once the plan has been updated and the single summary file has been written:

- do not dump the rewritten plan into chat;
- do not produce another long narrative review;
- do not create extra artifacts;
- respond only with:
  - the path to the updated plan;
  - the path to the one summary file;
  - the readiness result;
  - any owner decision that blocks progress, if one actually remains.

This is still a **planning/review task only**. No implementation should begin from this instruction.
