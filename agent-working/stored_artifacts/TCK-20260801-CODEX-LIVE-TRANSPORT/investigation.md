---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-LIVE-TRANSPORT
artifact_type: investigation
tags: [ai, security, testing]
---

# Investigation — TCK-20260801-CODEX-LIVE-TRANSPORT

## Findings

### Existing real subprocess precedent is deliberately the wrong operation

`tools/agent_replay_codex/invoker.py::run_codex_replay` is the sole repository
source that constructs `codex exec`. It checks consent before creating a subprocess,
runs in a temporary scratch directory, and proves that the real repository tickets,
monitoring, and Codex config remain unchanged. Its `tests/agent_replay_codex/
conftest.py::real_codex_replay` fixture is opt-in and session-scoped; missing CLI or
consent produces `pytest.skip`.

The fixture's skip pattern and command construction safety are reusable precedent.
The replay transport itself is not reusable: its purpose is proving a real repository
does not change, whereas a later controlled pilot must prove a strictly declared,
reviewed change and rollback outcome.

### The existing harness is deliberately one half of the future live path

`tools/agent_codex_realrepo_pilot_harness/preflight.py::ordinary_preflight` already
validates Codex identity before derived-path I/O; then candidate/request/policy
containment, owner/rollback request content, enabled surface, no concurrent claim,
policy/request/baseline hash binding, and a policy-self-excluded tree snapshot.
It intentionally refuses the canonical project root.

`boundary.py::invoke_after_authority` safely supports a scratch test invoker after a
dual-authority object and captured preflight. Its private
`_invoke_live_after_authority` / `_admit_live_root` instead requires the canonical
project root. This is structurally inert today: `PreflightResult` can only be
produced by ordinary preflight, which rejects that root. The transport ticket must
resolve this with a separately reviewed live-preflight representation; passing a raw
root or weakening ordinary admission would violate the harness's containment design.

### Durable reusable proof primitives already exist

- `proofs.py::capture_policy_baseline` captures a symlink-free baseline and excludes
  only the self-referential policy file.
- `assert_post_run_proof` requires the captured policy bytes to remain unchanged,
  permits only allowlisted paths, exact declared historical target transitions, and
  exact monitoring suffix rows with prefix preservation.
- `rollback.py::ScratchConfigAdapter` contains test-only config capture/restore to
  a scratch `.codex/config.toml`; it is not a production config mutator.
- `authority.py::issue_live_authority` demands both exact `"1"` gates:
  `CODEX_LIVE_PILOT_HUMAN_SIGNOFF` and
  `CODEX_REALREPO_PILOT_LIVE_CONSENT`.

The new transport must compose these public primitives. It must not copy their
validation logic or turn `ScratchConfigAdapter` into a production config writer.

## Constraints

- The owner authorized capability construction, not any real invocation, hook
  registration, `.codex/config.toml` change, or provider-attributed monitoring write.
- The reserved stale-status candidate must remain unimplemented and the two parent
  activation tickets remain `BLOCKED`.
- A default test run must require neither the Codex CLI nor a consent environment
  variable; any real invocation test is explicitly requested and skips cleanly if
  either condition is absent.
- No dangerous Codex bypass flags may be constructed under any path.
- The ticket requires independent architecture review of both plan and actual diff.

## Architecture decisions to resolve in Plan/Review

1. Define an immutable `LivePreflightResult` (or equivalent private capability)
   which can be created only after a real-root no-write preflight and which cannot be
   forged from an ordinary/scratch `PreflightResult`.
2. Define the transport's minimal public API: it should accept that live-preflight
   capability and an authority object, not raw root, command fragments, environment,
   or a caller-controlled sandbox bypass.
3. Decide whether the existing `CODEX_REALREPO_PILOT_LIVE_CONSENT` is the transport
   gate or whether a distinct gate is needed. Reuse is preferred unless review finds
   a distinct authorization meaning; neither choice authorizes actual use here.
4. Specify the prompt/input contract as immutable, reviewable evidence rather than
   a dynamically assembled arbitrary command string.

## Architecture Review resolutions

1. `LivePreflightResult` is the right capability shape only when its sole sanctioned
   constructor is a private module-level live-preflight factory that performs genuine
   real-root validation. A frozen dataclass alone is not sufficient in Python. The
   implementation must add an AST containment test proving no source path outside
   that factory constructs the capability.
2. Reuse the existing two exact-value gates; do not introduce a third environment
   variable. However, the transport's subprocess-invocation entry point must re-read
   both values as its literal first authorization operation, rather than trusting a
   potentially stale authority object issued earlier.
3. The transport API accepts no prompt/text parameter. Its fixed argv and fixed
   template derive only from the validated live-preflight capability's existing
   ticket/evidence fields, following the replay invoker's wrapper-template pattern.

## Risks

- A live preflight implementation is inherently capable of reading the real root;
  tests must use only synthetic refusal doubles and never call it successfully.
- A transport that accepts raw `Path`, shell text, environment, or broad command
  options could bypass the reviewed boundary even if its nominal caller is safe.
- Reusing replay containment assertions verbatim would reject a legitimate pilot's
  declared writes; post-run proof must use the harness's captured expected-write
  policy instead.

## Parity ledger overlap

This is agent-operational tooling. A parity disposition must be decided during the
ticket's Parity phase; do not pre-create an entry before actual scope/diff review.
