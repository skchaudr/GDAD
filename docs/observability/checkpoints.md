# Intra-Node Checkpoints

How to show *progress within* a single node while an agent is working on it.

---

## The Concept

When an agent is working on a capability node, you want to see not just "it's running" but *how far through the work it is*. This is done with a row of small checkboxes (ticks) shown directly on the node card.

Think of it like a checklist on a Trello card or a mission progress bar in a game.

---

## Two Levels of Review Gates — Don't Confuse Them

| Thing | What it is | Lives where |
|---|---|---|
| **`type: milestone` graph nodes** | Big review gates *between* capabilities in the DAG | Graph-level, stays as-is |
| **Intra-node checkpoints** | Small checkboxes *within* a single capability card | On the card, during live work |

Milestone nodes don't change. This doc is only about what happens *inside* a capability node while it's being worked on.

---

## Where the Tick Data Comes From

Each node already has `acceptance_criteria` authored in its YAML. Those IDs are the natural checkpoints.

**Example node YAML:**
```yaml
id: cap-auth-login
title: Implement login flow
acceptance_criteria:
  - ac-1: User can log in with email/password
  - ac-2: Invalid credentials show an error
  - ac-3: Session persists on refresh
```

The tick row on the card would show three boxes. They fill in as the evaluator emits receipts confirming each criterion is met.

---

## Rendering the Tick Row

```tsx
// Inside GDDPNode, when activity is present
{activity && acceptanceCriteria.length > 0 && (
  <div className="tick-row">
    {acceptanceCriteria.map(ac => (
      <span
        key={ac.id}
        className={`tick ${completedCriteria.has(ac.id) ? 'filled' : 'empty'}`}
        title={ac.label}
      />
    ))}
  </div>
)}
```

The `completedCriteria` set is populated by evaluator receipt events from the SSE stream — same stream already used for the drill-in panel.

---

## The Open Question (from Grok)

> **"Ticks = existing acceptance ids, or a new `checkpoints:` list?"**

There are two options:

### Option A — Use existing `acceptance_criteria` (simpler)
- No new YAML fields
- Works immediately
- May be too coarse for long-running nodes (only 2–4 criteria)

### Option B — Add a `checkpoints:` list (Droid-style)
- Authors define 7–12 mission stops, like Droid missions do
- More granular progress feedback
- Requires a new YAML field + authoring discipline

**Grok's recommendation:** Start with Option A. Add `checkpoints:` later if `acceptance_criteria` is too coarse.

---

## What Ticks Are NOT

Ticks show movement *along* a node (progress through work). They are **not**:
- Particles flying through space (that's Dream RSI)
- A replacement for milestone review gates
- A signal that the agent is on a correct path (that's the evaluator drift badge)

The metaphor is a checklist, not a progress bar or animation.
