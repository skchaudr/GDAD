# Stage 1 formats

Read the [canonical invariants](../invariants/invariants.md) before editing this directory.
The short projection is [docs/invariants/AGENTS.md](../invariants/AGENTS.md).

This directory is the Stage 1 data contract: the documents and the JSON Schemas.
It is not a reader, an executor, an accept command, or a place to store ready-work.

- Human authority: `accepted` is a line in `.gddp/accepted.jsonl` whose actor kind is `human`.
- Node integrity: node YAML has no `status`. A verdict action is a proposal.
- Evidence: a receipt names the project, the node, and the attempt, and carries evidence.
- Bounded role: nothing here dispatches, merges, or supervises an executor.

Drift to refuse before copying it:

- Putting `status` back on the node file.
- Writing `accepted` into the machine journal.
- Storing the ready set.
- Treating a `pass` verdict as acceptance.
