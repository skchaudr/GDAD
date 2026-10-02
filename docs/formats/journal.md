# Progress journal

Append-only machine progress for one project. One JSON object per line. A later line does not edit an earlier line. The last line for a `node_id` is that node's progress.

Invariants: [1 Human authority](../invariants/invariants.md#1-human-authority-over-intent-and-acceptance), [4 Evidence-backed progress](../invariants/invariants.md#4-evidence-backed-progress), [7 Bounded role](../invariants/invariants.md#7-a-bounded-role-in-development), [9 Bounded failure](../invariants/invariants.md#9-failure-consequences-stay-bounded).

Path: `~/.gddp/state/<project_id>/progress.jsonl`. This file is not committed. Slugs and timestamps are defined in [README.md](README.md).

## Event

| Field | Required | Contents |
|---|---|---|
| `project_id` | yes | Slug |
| `node_id` | yes | Slug |
| `status` | yes | The value `dispatched` |
| `at` | yes | UTC timestamp |
| `actor.kind` | yes | `human` or `system` |
| `actor.id` | yes | Slug |
| `reason` | no | One string |

```json
{"project_id":"close-loop","node_id":"record-acceptance","status":"dispatched","at":"2026-10-02T00:01:00Z","actor":{"kind":"system","id":"gdad"}}
```

Schema: [journal-event.schema.json](schemas/journal-event.schema.json).

`accepted`, `provisional`, and `ready` are rejected as statuses. An actor kind of `evaluator` is rejected. A `ready` property on the line is rejected. Blank lines are rejected.

Stage 1 has this one status. A second `dispatched` line for the same node is legal; the node stays dispatched. The line has no receipt ref. The receipt file is the ref. See open question 9 in [README.md](README.md).

## Ready-work

Ready-work is a set computed at read time. Nothing stores it.

Inputs are the node `depends_on` lists, the acceptance log, and this journal. A receipt is not an input.

A node is ready when all three hold:

1. No acceptance line names it.
2. Its last journal line is absent, or that line's status is not `dispatched`. Under this schema the only status is `dispatched`, so any journal line leaves the node in flight.
3. Every `depends_on` id has an acceptance line. An unknown id is unsatisfied. It does not remove other nodes from the graph.

Acceptance and the journal stay independent. A dispatched node that a human has accepted is accepted, and the journal line remains. Dependents become ready from the acceptance log.

A `pass` receipt does not accept a node and does not remove `dispatched`. A `fail` receipt does not return the node to the ready set.

A cycle has no acceptance to satisfy it, so every node on it stays out of the ready set. The format does not also reject the cycle at authoring time.

The worked example is [contracts/stage1/fixtures/ready](../../contracts/stage1/fixtures/ready). `root` is accepted, `sibling` is dispatched and has a `pass` receipt, `child` depends only on `root`, and `later` depends on `sibling`. The ready set is `child`. The function that checks this is `ready_work` in [contracts/stage1/test_formats.py](../../contracts/stage1/test_formats.py).
