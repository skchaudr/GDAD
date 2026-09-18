# Milestones

Milestones are **authored checkpoints staked inside a capability node**. They define the expected path through the work, give the orchestration runtime natural trigger points for evaluator runs, and provide the visual progress ticks shown on the live node card.

---

## What a Milestone Is

A milestone is a named intermediate stop in the work a node represents. It answers: **"What should be true at this point in the execution?"**

It is:
- **Authored upfront** — written when the node is defined, not generated at runtime
- **Optional** — a small or simple node may have zero milestones
- **An intent statement** — written in plain language describing what should exist or be true at that stop
- **A runtime trigger** — when the orchestration runtime detects the milestone condition is met, it fires the evaluator

It is not:
- A test assertion (that's `acceptance_criteria`)
- A graph-level milestone node (those are review gates *between* capabilities in the DAG)
- Something the agent knows about

---

## Node YAML Schema

```yaml
id: cap-auth-login
title: Implement login flow
acceptance_criteria:           # for the evaluator — pass/fail outcomes
  - id: ac-1
    description: User can log in with email/password
  - id: ac-2
    description: Invalid credentials show an error
  - id: ac-3
    description: Session persists on refresh
milestones:                    # optional, zero to N, for runtime + progress visibility
  - id: ms-1
    description: Auth module read, session handling mapped, route contract designed
  - id: ms-2
    description: Route handler scaffolded, credential lookup and bcrypt comparison implemented
  - id: ms-3
    description: Session token generation wired, all unit tests written
```

`milestones:` is optional. Omit it entirely for small nodes. Include as many as the work warrants — there is no fixed count requirement.

---

## `acceptance_criteria` vs `milestones`

These are different fields for different audiences. Both live in the node YAML. Both stay.

| | `acceptance_criteria` | `milestones` |
|---|---|---|
| **Answers** | "Did it work?" | "Where is it now?" |
| **Written for** | The evaluator (pass/fail) | The runtime + human watching |
| **When it matters** | At completion | Throughout the run |
| **Form** | Outcome assertions | Intent statements |
| **Required** | Yes | No |

A node without milestones is valid. A node without acceptance criteria is not.

---

## How the Runtime Uses Milestones

The orchestration runtime watches the agent's event stream. When it determines a milestone condition is satisfied (based on the work produced so far), it:

1. Records the milestone as hit
2. Fires an evaluator run against the work to date
3. Receives a pass or flag result
4. Either continues agent execution or issues a retry/redirect

The agent does not know any of this happened.

---

## How Milestones Drive Progress Ticks

Each milestone maps to one tick on the live node card. The tick fills when the runtime records the milestone as hit and the evaluator passes.

```
[●] ms-1  Auth module mapped, contract designed
[●] ms-2  Route scaffolded, credential logic done
[○] ms-3  Tests written
[ ] final  All acceptance criteria confirmed
```

For nodes with zero milestones, the tick row is omitted. The card shows activity state only (thinking / writing / stuck / dead).

---

## Authoring Guidance

- Write milestones as **what should exist** at that stop, not what the agent should do next
- Each milestone should represent a meaningful chunk of progress a human can verify by reading the work
- Space them so the early milestone falls roughly in the first third of expected work, and the last milestone falls in the final third
- The final evaluator run at completion fires regardless — milestones don't replace it
