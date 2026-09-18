---
title: Live graph observability — minimal motion
date: 2026-09-17
status: draft
tags: [gddp, viewer, observability, shape-shifter]
---

# Live graph observability — minimal motion

Dream RSI (search-tree replay) vs GDDP Viewer (intent DAG) are different graphs.
Steal the *signal*, keep the DAG.

- Dream RSI: particles travel a recorded rollout tree. The tree *is* the computation.
- GDDP: the DAG is authored intent. Computation sits *on* a node. Liveliness belongs on the occupied card + its inbound edge.

shape-shifter-graph already has the data. It is not painted on the canvas.

| Already there | Where | Gap |
|---|---|---|
| `LiveAttempt`: `node_id`, `state`, `last_write` | `fleetScan.ts`, 3s poll | Docked `LiveFleetPanel` only |
| SSE tail of `events.jsonl` | `/api/gddp/live/events` | Drill-in only |
| React Flow `edge.animated` | `graph.ts` hardcoded `false` | Unused |
| Memoized cards, `onlyRenderVisibleElements` | `GDDPNode`, `GraphCanvas` | Ready for one live node |

## Three activity classes (projection, never YAML)

Join fleet onto `GraphNodeData`. Typical occupancy: 0–2 nodes.

1. **Think / read** — process alive, last event is thinking or a read/grep. Status-dot CSS pulse (already used on the Live radio).
2. **Write** — last event is `apply_patch` / write / search_replace. Flip inbound edge `animated: true` (React Flow dash, GPU compositor).
3. **Stuck / dead** — `running` + `last_write` older than ~90s → freeze pulse, amber, age string. `dead` while the node is still in progress → solid red, no motion.

Wrong-path is click-through (existing `AttemptSection` / `CursorInspector` / evaluator `drift` badge). Do not invent a color for “bad reasoning.”

Activity is a machine projection, same rule as progress vs intent: it never lands in node YAML.

## Intra-node checkpoints (Droid-style)

Graph `type: milestone` nodes stay graph-level review gates.

Inside a live capability: a tick row on the card, one tick per `acceptance_criteria` id (already authored). Fill as receipts/evaluator events land. Optional later: a `checkpoints:` list when acceptance is too coarse for 7–12 mission stops.

Ticks are the movement *along* a node. Particles through space are the wrong metaphor here.

## Cost ceiling

- Animate only occupied nodes. Idle cards stay static.
- Canvas uses fleet `state` + `last_write` + last event *type*. Full jsonl parse stays in drill-in.
- No layout animation, no per-node canvas, no force-directed tree.
- `prefers-reduced-motion` → static glyphs (● thinking, ▶ writing, ⏱ stuck, ■ dead).

## First seam

`LiveFleetPanel` → `GraphNodeData.activity` on the matching `node_id`. One CSS class + one edge flag. That is the stuck/crash detector. Everything else is decoration on that join.
