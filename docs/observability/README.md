# GDAD Observability

The GDAD graph is a **spec for development work** — a DAG of authored intentions that an orchestration runtime executes. This directory documents how that runtime makes its execution *observable*: what's running, how far along it is, whether it's healthy, and whether the work is staying in integrity with the rest of the graph.

---

## What This Is, Actually

This is not just visual candy on a graph. It is documentation for a **spec-driven, observable development runtime**:

- The graph is the spec (DAG of capabilities, authored intent)
- The orchestration runtime executes that spec (agent dispatch, evaluator firing, retry logic)
- Observability is the window into that execution (live node state, milestone progress, evaluator results)

The visual layer (animations, ticks) is a consequence of the runtime — not the point. The point is that the runtime is inspectable and the spec is the source of truth.

---

## Directory Structure

```
docs/observability/
├── README.md               ← You are here
├── milestones.md           ← Milestone schema, progress ticks, evaluator triggers
├── evaluator-cadence.md    ← The 3-run evaluator pattern and why it works
├── activity-states.md      ← Live node states: thinking / writing / stuck / dead
└── live-graph-animation.md ← Canvas animation implementation (the visual layer)
```

---

## Key Concepts

### The Graph Is the Spec

The milestone graph is a PRD fleshed out across nodes. Each capability node is a unit of authoring: it has an end vision, acceptance criteria, and optionally a set of milestones that stake out the expected path through the work. The orchestration runtime reads this and executes against it.

### Agents Are Oblivious

The agents doing the work don't know when the evaluator runs. The orchestration runtime manages that. The agent gets a task; the runtime watches for milestone triggers, fires the evaluator, and either continues or hands back a retry.

### The One Critical Wiring Job (visual layer)

```
LiveFleetPanel  →  GraphNodeData.activity  (matched by node_id)
```

Everything visual is decoration on this join. One CSS class + one edge flag is all the canvas needs.

---

## Resolved Decisions

| Decision | Resolution |
|---|---|
| Progress ticks source | **Milestones authored into the node** (`milestones:` YAML field, optional, zero to N). See [`milestones.md`](./milestones.md). |
| Evaluator cadence | **Three runs per node**: early, near-end, final. See [`evaluator-cadence.md`](./evaluator-cadence.md). |
| Agent awareness of evaluator | **None.** The orchestration runtime owns evaluator dispatch. Agents are oblivious. |
| Activity in node YAML | **Never.** Live state is a machine projection, never persisted to YAML. |

---

## See Also

- [`docs/transition/live-graph-observability.md`](../transition/live-graph-observability.md) — Original Grok draft
