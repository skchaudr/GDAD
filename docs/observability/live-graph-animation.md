# Live Graph Animation

This document explains what data already exists and what small changes are needed to make the GDAD canvas show live agent activity.

---

## What Already Exists (Just Not Shown)

The good news: the data and infrastructure are already there. Nothing needs to be invented — just *connected*.

| Thing | Where it lives | What's missing |
|---|---|---|
| `LiveAttempt` — tracks which agent is on which node, its state, and when it last wrote | `fleetScan.ts` (polls every 3s) | Only shown in the `LiveFleetPanel` dock. Not joined onto graph nodes. |
| SSE event stream (`events.jsonl` tail) | `/api/gddp/live/events` | Only used in the drill-in detail view, not the canvas. |
| `edge.animated` prop | `graph.ts` | Hardcoded to `false`. Just needs to be flipped to `true` for the inbound edge of an active write node. |
| Memoized cards + `onlyRenderVisibleElements` | `GDDPNode`, `GraphCanvas` | Already optimized. Can handle 1–2 animated nodes with no perf hit. |

---

## What Needs to Change

### Step 1 — Join Fleet State onto Graph Nodes

In `LiveFleetPanel`, when a `LiveAttempt` is found for a `node_id`, project an `activity` field onto the matching `GraphNodeData`:

```ts
// Inside the fleet scan result handler
const activity = deriveActivity(liveAttempt, lastEventType);
updateNodeData(liveAttempt.node_id, { activity });
```

This is the **only** structural change. Everything else is CSS and a flag flip.

---

### Step 2 — CSS Class on the Node Card

In `GDDPNode`, read `data.activity.state` and apply a CSS class:

```tsx
<div className={`gdad-node ${activity?.state ?? ''}`}>
  ...
  <StatusDot className={activity?.state === 'thinking' ? 'pulse' : ''} />
</div>
```

```css
/* Already exists for the Live radio — reuse it */
.pulse {
  animation: status-pulse 1.5s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .pulse { animation: none; }
}
```

---

### Step 3 — Animate the Inbound Edge

In the edge data for a node whose `activity.state === 'writing'`, set `animated: true`.

```ts
// When projecting activity onto graph data
if (activity.state === 'writing') {
  setEdgeAnimated(nodeId, true);  // flips the inbound edge
} else {
  setEdgeAnimated(nodeId, false);
}
```

React Flow handles the animated dashed line via the GPU compositor — no JS animation loop needed.

---

## Performance Budget

Grok's explicit constraint: **animate 0–2 nodes at a time**.

- Canvas reads only `fleet.state` + `fleet.last_write` + last event *type* (3 fields)
- Full `events.jsonl` parsing stays in the drill-in panel only
- No layout animations
- No per-node canvas
- No force-directed physics tree

---

## Data Flow Diagram

```
fleetScan.ts (3s poll)
    │
    ▼
LiveFleetPanel
    │  join on node_id
    ▼
GraphNodeData.activity
    ├─→ GDDPNode CSS class   (thinking → pulse dot)
    └─→ inbound edge flag    (writing  → animated: true)
```

The `events.jsonl` SSE feed is only used to determine *which type* of event happened last (read vs write). The full log stays in drill-in.
