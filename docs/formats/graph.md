# Graph, node, and acceptance

Human-owned intent for one project, plus the only git-tracked status: human acceptance.

Invariants: [1 Human authority](../invariants/invariants.md#1-human-authority-over-intent-and-acceptance), [2 Node integrity](../invariants/invariants.md#2-intent-preservation-and-node-integrity), [8 Accessible control](../invariants/invariants.md#8-human-control-must-be-accessible).

Slugs and timestamps are defined in [README.md](README.md).

## Paths

| File | Role |
|---|---|
| `<project>/.gddp/project.yaml` | Graph |
| `<project>/.gddp/nodes/<node_id>.yaml` | One node |
| `<project>/.gddp/accepted.jsonl` | Human acceptance, append-only |

The roadmap's earlier `graphs/<project>/` path is the same records under `<project>/.gddp/`. Machine progress and receipts stay in `~/.gddp/state/<project_id>/`.

## Graph

| Field | Required | Contents |
|---|---|---|
| `project_id` | yes | Slug |
| `intent` | no | One string |
| `repo` | no | One string, the project repository |

```yaml
project_id: close-loop
```

Schema: [graph.schema.json](schemas/graph.schema.json).

## Node

The file name is the id. `nodes/record-acceptance.yaml` contains `node_id: record-acceptance`.

| Field | Required | Contents |
|---|---|---|
| `node_id` | yes | Slug, equal to the file stem |
| `why` | yes | The intent an evaluation can judge |
| `depends_on` | yes | Node ids. An empty list means the node can start |
| `acceptance_criteria` | yes | At least one `{id, criterion}`. Ids are unique within the node |
| `title` | no | Short label |
| `constraints` | no | Node-local limits. Project invariants stay in `AGENTS.md` |
| `required_artifacts` | no | Paths a cheap check can look for |

`depends_on` does not contain the node's own id. Ready-work reads this list and no other node field.

```yaml
node_id: record-acceptance
why: A human can accept this node from a separate acceptance line.
depends_on: []
acceptance_criteria:
  - id: recorded
    criterion: A human acceptance line names this node.
```

Schema: [node.schema.json](schemas/node.schema.json).

A `status` field is rejected. A `ready` field is rejected. Unique criterion ids and the ban on a self-dependency are cross-field rules; JSON Schema does not see them. The contract tests do.

## Acceptance

One JSON object per line in `accepted.jsonl`. Appending a line is the write. A node has at most one line. There is no revoke line.

| Field | Required | Contents |
|---|---|---|
| `project_id` | yes | Slug |
| `node_id` | yes | Slug |
| `status` | yes | The value `accepted` |
| `at` | yes | UTC timestamp |
| `actor.kind` | yes | The value `human` |
| `actor.id` | yes | Slug |
| `attempt_id` | yes | Slug of the receipt this line cites |

```json
{"project_id":"close-loop","node_id":"record-acceptance","status":"accepted","at":"2026-10-02T00:06:00Z","actor":{"kind":"human","id":"operator"},"attempt_id":"attempt-1"}
```

Schema: [acceptance-event.schema.json](schemas/acceptance-event.schema.json).

An actor kind of `system` or `evaluator` is rejected. The journal schema rejects `status` `accepted`, including when the actor is human. Binding `actor.id` to an interactive TTY and the operator's identity is the accept command, which this format does not define. The schema also does not read the cited receipt, so the line can cite an attempt whose verdict is `fail`.
