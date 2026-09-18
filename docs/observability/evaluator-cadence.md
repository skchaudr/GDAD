# Evaluator Cadence

How many times the evaluator runs during a node execution, when it runs, and why.

---

## The Pattern: Three Runs Per Node

Every node gets three evaluator runs across its execution: **early**, **near-end**, and **final**.

```
Node starts
    │
    ├──── [Early evaluator run]       ← ~first milestone, or first third
    │
    ├──── [Near-end evaluator run]    ← ~last milestone, or ~75–80% through
    │
    └──── [Final evaluator run]       ← at completion, always
```

---

## Why Three, Not Two

Two runs — early and final — leaves a blind spot. Here is what each run actually buys you:

### Early run
**Catches gross misalignment fast.**

The work has just begun. Is the agent building the right thing? Is it reading the right files, working in the right part of the codebase, moving toward the right output shape? If the early evaluator flags a problem here, you've saved the entire remaining run — potentially 30–45 minutes of agent work headed in the wrong direction.

### Near-end run
**Catches subtle drift while there's still room to correct. This is the most valuable run.**

The work is 70–80% done. The early run passed, so the direction was right. But over a long run, agents can drift — a sequence of individually reasonable decisions that compound into something slightly wrong. By the time the final evaluator runs, correcting that drift means a full retry. The near-end run catches it while the agent can still course-correct without torching the run.

Without this run, you go from "are we aligned?" directly to "did we make it?" — with no intervention window between them.

### Final run
**The formal gate.**

Definitive pass/fail against all `acceptance_criteria`. This run always happens, regardless of how many milestones were hit or what the earlier runs returned. It is the only run that can close the node.

---

## How Milestones Map to Evaluator Runs

When milestones are authored into a node, they become the natural trigger points:

| Evaluator run | Milestone trigger |
|---|---|
| Early | First milestone hit |
| Near-end | Last milestone hit (or second-to-last if there are many) |
| Final | Node completion (always, regardless of milestones) |

If a node has **zero milestones**, the runtime uses time or event count to approximate the same proportions. The 3-run pattern holds either way — milestones just make the trigger points explicit and meaningful rather than estimated.

---

## What the Runtime Does with Each Result

The orchestration runtime receives a result from each evaluator run:

| Result | Runtime action |
|---|---|
| **Pass** | Continue agent execution |
| **Flag (correctable)** | Pass context back to agent, continue with course-correction |
| **Flag (off-track)** | Pause agent, surface to orchestrator for retry decision |
| **Hard fail** | Stop node, escalate |

The agent is **oblivious** to all of this. It receives a task and produces work. The runtime manages the evaluator loop entirely.

---

## What the Evaluator Checks

The evaluator is not checking everything every time. Each run has a scope:

- **Early run** — alignment check. Is the work moving toward the right output shape? Is it touching the right artifacts?
- **Near-end run** — integrity check. Is the work going to satisfy the acceptance criteria? Will it play nicely with what downstream nodes expect?
- **Final run** — full `acceptance_criteria` evaluation. Definitive.

The early and near-end runs are lighter, faster checks. The final run is the full one.

---

## Cost

- 2–3 evaluator calls per node is the expected range
- Early and near-end runs are scoped (not full evaluations) — they're cheaper
- The final run is always a full evaluation
- For a node with no milestones and a short run, the runtime may collapse early + near-end into a single mid-run check, making the total 2
