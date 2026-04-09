Create a complete, detailed, production-grade state machine for [SYSTEM].

Requirements:
- At least 10 states (prefer 12–16 if needed)
- At least 50 directed transitions
- No placeholder states like “Misc” or “Other”
- Every state must have:
  - name
  - purpose
  - entry actions
  - exit actions
  - invariants
- Every transition must have:
  - source state
  - target state
  - trigger/event
  - guard condition
  - action/effect
  - priority if multiple transitions can fire
- Include:
  - normal flow
  - failure states
  - timeout states
  - retry/recovery paths
  - manual override/admin paths
  - initialization/bootstrap state
  - terminal/shutdown state

Output format:
1. A short architecture summary of the machine
2. A state table listing all states and their responsibilities
3. A transition table listing every edge explicitly
4. A diagram in [Mermaid / PlantUML / Graphviz DOT]
5. A validation section that reports:
   - total number of states
   - total number of transitions
   - unreachable states
   - dead-end states
   - conflicting transitions
   - missing recovery paths

Constraints:
- Make the machine logically consistent
- Avoid redundant transitions unless justified
- Prefer hierarchical grouping if the diagram becomes unreadable
- Do not invent transitions without triggers
- Do not skip the transition table
- Do not stop until the machine satisfies the minimum counts

After generating the first version, review it and fix:
- unreachable states
- ambiguous guards
- duplicate edges
- missing error recovery
- states with too many responsibilities

Better versions depend on output target:

For **Mermaid**:
Generate the final diagram in Mermaid stateDiagram-v2 syntax.


For **PlantUML**:
Generate the final diagram in PlantUML state diagram syntax.


For **Graphviz** when the machine is very large:
Generate the final diagram in Graphviz DOT with subgraphs/clusters for related state groups.


The smarter way is to force the agent into **two passes**:
Pass 1: Design the state catalog and transition table only.
Pass 2: After validating counts and consistency, generate the diagram code.


That prevents the usual garbage where the picture looks complex but the logic is incomplete.

If you want higher quality, give the agent a domain instead of asking for abstract complexity. Example:


Create a detailed state machine for an autonomous RPG entity with combat, fleeing, looting, resting, trading, investigating, social interaction, recovery, injury, patrol, escort, and death handling.


That works better because transitions become grounded instead of decorative.

The most important line is this one:


Do not skip the explicit transition table. The diagram alone is not accepted.


Without that, the agent will almost always cheat.

Priority Plan

What you must change in mindset or assumptions:
Stop asking for diagrams. Ask for a formal machine specification plus a diagram.

What actions you must take immediately:
Use a prompt that forces state table, transition table, counts, and validation before rendering.

What you must stop or eliminate:
Stop accepting visual complexity as proof of logical completeness.

The consequences and opportunity cost if you fail to change:
You will get a diagram that looks impressive, but it will be useless for implementation because the guards, triggers, and recovery logic will be missing.
