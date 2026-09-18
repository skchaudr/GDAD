# Activity States

An occupied node can be in exactly one of three states. These are computed at runtime from fleet data — they are **never stored in YAML**.

---

## The Three States

### 1. 🟢 Thinking / Reading

**What it means:** The agent process is alive and its last logged event was a read, grep, search, or reasoning step.

**Visual:** Gently pulse the status dot that already exists on the card (same CSS pulse used on the Live radio indicator).

**Data source:** `LiveAttempt.state === 'running'` + last event type is `read` / `grep` / `search` / `think`

---

### 2. 🔵 Writing

**What it means:** The agent's most recent action was a file write — `apply_patch`, a direct file write, or `search_replace`.

**Visual:** Flip the inbound edge (the arrow pointing *into* this node) to `animated: true`. React Flow renders this as a moving dashed line handled by the GPU compositor — essentially free.

**Data source:** `LiveAttempt.state === 'running'` + last event type is `apply_patch` / `write` / `search_replace`

---

### 3. 🔴 Stuck / Dead

Two sub-cases:

| Sub-case | Condition | Visual |
|---|---|---|
| **Stuck** | `state === 'running'` but `last_write` is older than ~90 seconds | Freeze the pulse, turn amber, show age string (e.g. "stalled 2m ago") |
| **Dead** | PID is gone but the node is still marked in-progress in the graph | Solid red dot, no animation |

**Why ~90s?** That's the heuristic Grok chose as "something has gone wrong." It's adjustable.

---

## What "Wrong Path" Is NOT

If an agent is going down a bad reasoning path (evaluator drift, bad output), that is **not** a new color. It's already handled by clicking into the attempt detail view (`AttemptSection` / `CursorInspector` / `drift` badge on the evaluator). Don't invent a 4th state for "bad reasoning."

---

## Data Shape

Fleet state is joined onto the graph node at render time:

```ts
// Pseudocode — projection only, never persisted
interface GraphNodeActivity {
  state: 'thinking' | 'writing' | 'stuck' | 'dead' | null;
  lastWrite: Date | null;         // from LiveAttempt.last_write
  ageString?: string;             // e.g. "stalled 2m ago"
}

// GraphNodeData gets a new optional field:
interface GraphNodeData {
  // ...existing fields...
  activity?: GraphNodeActivity;   // injected by LiveFleetPanel join
}
```

---

## Accessibility

When `prefers-reduced-motion` is enabled, replace all CSS animations with plain text glyphs:

| State | Glyph |
|---|---|
| Thinking | `●` |
| Writing | `▶` |
| Stuck | `⏱` |
| Dead | `■` |
