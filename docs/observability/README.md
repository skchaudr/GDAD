# GDAD Observability

This directory documents how the GDAD graph viewer communicates **live agent activity** — which node an AI is currently working on, what it's doing, and whether it's healthy or stuck.

---

## The Core Idea

The GDAD graph shows a plan (a DAG of intentions). At any given moment, 0–2 of those boxes (nodes) are being actively worked on by an agent. The goal of observability is to make those live nodes *visually distinct* from idle ones — using subtle, cheap animations — without turning the graph into a particle show.

> **Key rule:** All live state is a machine projection. It never gets written into node YAML.

---

## Directory Structure

```
docs/observability/
├── README.md                   ← You are here (overview + plain English)
├── live-graph-animation.md     ← How to animate live nodes on the canvas
├── activity-states.md          ← The 3 states: thinking, writing, stuck/dead
└── checkpoints.md              ← Intra-node progress ticks (Droid-style)
```

---

## Key Concepts

### Two Different Graphs — Don't Confuse Them

| Graph | What it is | Animation style |
|---|---|---|
| **Dream RSI** | Playback of a recorded search tree | Flying particles — movement IS the data |
| **GDDP Viewer** | A plan (DAG of authored intentions) | Subtle pulses on occupied nodes only |

Dream RSI's particle animations don't belong in GDAD. The GDAD graph is a *map*, not a playback. Animation belongs on the card that is currently being worked on.

---

## The One Critical Wiring Job

Everything else in this system is decoration. The single seam that makes it all work:

```
LiveFleetPanel  →  GraphNodeData.activity  (matched by node_id)
```

Once fleet state is joined onto graph node data, you get stuck/crash detection for free. One CSS class + one edge flag is all the canvas needs.

---

## See Also

- [`docs/transition/live-graph-observability.md`](../transition/live-graph-observability.md) — Original Grok draft this was derived from
