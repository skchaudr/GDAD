# Stage 1 formats

The data contract for the smallest loop that closes once: graph and nodes, an append-only progress journal, a receipt, a verdict, and a human acceptance line.

These are documents and schemas. There is no reader, executor, or accept command in this tree.

Invariants in force: all nine in [docs/invariants/invariants.md](../invariants/invariants.md). The formats below name the ones they exist to keep. [AGENTS.md](AGENTS.md) is the placed note for this directory.

| Record | Document | Where it lives | Git |
|---|---|---|---|
| Graph and node | [graph.md](graph.md) | `<project>/.gddp/project.yaml`, `<project>/.gddp/nodes/<node_id>.yaml` | yes |
| Human acceptance | [graph.md](graph.md) | `<project>/.gddp/accepted.jsonl` | yes |
| Progress journal | [journal.md](journal.md) | `~/.gddp/state/<project_id>/progress.jsonl` | no |
| Receipt | [receipt.md](receipt.md) | `~/.gddp/state/<project_id>/receipts/<node_id>/<attempt_id>.json` | no |
| Verdict | [verdict.md](verdict.md) | the `verdict` object inside a receipt | no |

Ready-work is not a file. [journal.md](journal.md) states the arithmetic. The check is `ready_work` in [contracts/stage1/test_formats.py](../../contracts/stage1/test_formats.py).

Schemas: [docs/formats/schemas/](schemas/).

## Shared syntax

- **Slug:** one or more lowercase letters or digits, then zero or more `-` plus more lowercase letters or digits. Pattern: `^[a-z0-9]+(-[a-z0-9]+)*$`.
- **UTC timestamp:** `YYYY-MM-DDThh:mm:ssZ`. No fractional seconds, no numeric offset.

## Check

```sh
python3 -m pip install -r contracts/stage1/requirements.txt
python3 -m pytest contracts/stage1
```

The shadow prototype under `prototypes/shadow-evaluator` stays on `unittest` and is a different tool.

## Open questions

The roadmap leaves these unspecified. Each line is the smallest rule this contract uses.

1. **Where `accepted` is stored.** It cannot be a node field, and the machine journal does not carry it. Choice: `<project>/.gddp/accepted.jsonl`, git-tracked, one JSON object per line, actor kind fixed as `human`. Ready-work reads `depends_on`, this log, and the journal. It is not a function of the journal and dependencies alone.
2. **Revocation.** The roadmap defers acceptance-invalidation semantics. This format has no revoke line. A second acceptance line for the same node is rejected.
3. **Stage 1 journal vocabulary.** The only status is `dispatched`. `provisional`, and a transition back to ready, belong to Stage 2. A `fail` receipt leaves the last status `dispatched`, so the node stays out of the ready set.
4. **What satisfies a dependency.** An acceptance line does. A `pass` receipt does not, and it does not clear `dispatched`.
5. **Fields dropped from older notes.** `unlocks`. `type`, `priority`, `allowed_execution_modes`. A graph blueprint beyond optional `intent` and `repo` strings. Old receipt booleans, criteria judgments, and git or pull-request fields. `draft_node_yaml` on a graph action.
6. **Acceptance cites an attempt and does not require `pass`.** `attempt_id` is required. The schema does not read that receipt's verdict, so a human override stays expressible. Whether the accept command refuses a missing file is command behavior, still unwritten.
7. **One shape for all eight graph actions.** `affected_node_ids` has at least one id. Evidence is a list of strings. Per-action fields are unspecified.
8. **Cycles and a second dispatch.** A cycle is not rejected; those nodes are not ready. A self-dependency is rejected. A second `dispatched` line for one node is allowed. A second acceptance line is not.
9. **Journal receipt ref.** The roadmap describes progress as node, status, receipt ref, time, and reason, and also says an attempt is found on disk and never registered. These lines carry time and an optional reason, and no receipt ref. The receipt path is the ref.
