# Receipt

The durable record of one evaluation of one attempt. Writers create the file and leave it. A later judgment is a new `attempt_id` and a new file.

Invariants: [3 Independent evaluation](../invariants/invariants.md#3-independent-evaluation), [4 Evidence-backed progress](../invariants/invariants.md#4-evidence-backed-progress), [9 Bounded failure](../invariants/invariants.md#9-failure-consequences-stay-bounded).

Path: `~/.gddp/state/<project_id>/receipts/<node_id>/<attempt_id>.json`. Not committed. The directory name is `node_id`. The file stem is `attempt_id`. Slugs and timestamps are defined in [README.md](README.md).

Stage 1 stores the final verdict only. Mid-run observation records are Stage 2.

## Fields

| Field | Required | Contents |
|---|---|---|
| `project_id` | yes | Slug |
| `node_id` | yes | Slug |
| `attempt_id` | yes | Slug |
| `generated_at` | yes | UTC timestamp |
| `actor.kind` | yes | The value `evaluator` |
| `actor.id` | yes | Slug, the checker that wrote the file |
| `evidence` | yes | One or more strings |
| `verdict` | yes | A [verdict](verdict.md) |

```json
{
  "project_id": "close-loop",
  "node_id": "record-acceptance",
  "attempt_id": "attempt-1",
  "generated_at": "2026-10-02T00:04:00Z",
  "actor": {
    "kind": "evaluator",
    "id": "deterministic"
  },
  "evidence": [
    "The node file contains why, depends_on, and acceptance_criteria."
  ],
  "verdict": {
    "kind": "pass"
  }
}
```

Schema: [receipt.schema.json](schemas/receipt.schema.json).

An empty evidence list is rejected, as is a missing evidence field. An actor kind of `human` or `system` is rejected. A `status` field is rejected. A receipt does not accept the node.

The path rule (directory equals `node_id`, file stem equals `attempt_id`) is checked when the file sits at its storage path. The schema checks the object.
