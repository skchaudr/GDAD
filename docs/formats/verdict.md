# Verdict

The evaluator's judgment of one attempt. It is the `verdict` object inside a [receipt](receipt.md). Stage 1 does not store it as its own file. The fixtures under `contracts/stage1/fixtures/valid/` exist so the object can be checked on its own.

Invariants: [2 Node integrity](../invariants/invariants.md#2-intent-preservation-and-node-integrity), [3 Independent evaluation](../invariants/invariants.md#3-independent-evaluation), [4 Evidence-backed progress](../invariants/invariants.md#4-evidence-backed-progress).

Vocabulary: `pass`, `fail`, and eight graph actions: `split`, `supersede`, `insert_prerequisite`, `revise_criteria`, `rewire`, `reorder`, `create_node`, `retire_node`.

`pass` and `fail` judge the attempt against a graph that can stay as written. A graph action says the graph is what has to change. The action does not edit the graph. A human materializes it. `pass` is exclusive of every action: the object carries `kind` and nothing else.

A `fail` carries a fix-list. Each finding has a `summary` and at least one evidence string. An uncited finding is rejected.

All eight actions share one shape: `kind`, `affected_node_ids` (at least one slug), `rationale`, and `evidence` (at least one string).

Schema: [verdict.schema.json](schemas/verdict.schema.json).

## `pass`

```json
{"kind": "pass"}
```

## `fail`

```json
{
  "kind": "fail",
  "findings": [
    {
      "summary": "The recorded acceptance was not written by a human.",
      "evidence": [
        "actor.kind on the acceptance line is system."
      ]
    }
  ]
}
```

## Graph action

`create_node` stands in for the other seven, which use the same fields.

```json
{
  "kind": "create_node",
  "affected_node_ids": [
    "record-acceptance"
  ],
  "rationale": "The attempt found work outside this node's criteria.",
  "evidence": [
    "The diff adds a module the criteria do not name."
  ]
}
```

Retired names are rejected, including `needs-human-review`, `blocked`, `needs-more-evidence`, `out-of-scope-change-detected`, `drift`, `insufficient`, `contradicted`, and `unknown`.
