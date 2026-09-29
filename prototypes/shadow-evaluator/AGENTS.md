# Shadow evaluator prototype

Read [the canonical invariants](../../docs/invariants/invariants.md).

This prototype observes existing GDDP work. It writes only its own samples,
checkpoints, errors, and review labels. It has no dispatch, cancellation,
acceptance, graph-mutation, or local model-server authority.

Keep the exact node, questions, receipt, evidence, and hosted-model response
recoverable. A receipt is another evaluator's account, not independently
verified behavior. Missing evidence and service failures stay explicit.
Probabilities are candidate judgments, never automatic training labels.

Do not import the old runtime to observe it: read its existing files.
