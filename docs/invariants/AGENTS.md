# GDAD — invariant projection

Read [the canonical invariants](./invariants.md) before changing this corpus.
This file summarizes those guarantees; the linked rules govern if a summary differs.

- [Human authority](./invariants.md#1-human-authority-over-intent-and-acceptance):
  agents propose and implement within delegated scope; humans own intent and acceptance.
- [Node integrity](./invariants.md#2-intent-preservation-and-node-integrity):
  retries preserve scope; graph amendments require human authorization.
- [Independent evaluation](./invariants.md#3-independent-evaluation):
  executor framing and intermediate gates cannot replace independent judgment.
- [Evidence-backed progress](./invariants.md#4-evidence-backed-progress):
  provisional progress requires durable evidence for the actual work and attempt.
- [Architectural changeability](./invariants.md#5-evidence-and-intent-over-architectural-attachment):
  evidence and intent justify mechanisms; familiarity and speculative completeness do not.
- [Prevention at the site](./invariants.md#6-prevention-where-work-happens):
  place relevant constraints before implementation; distinguish rules from mechanisms.
- [Bounded role](./invariants.md#7-a-bounded-role-in-development):
  GDAD delegates execution rather than rebuilding the agent harness or its loop.

- [Accessible human control](./invariants.md#8-human-control-must-be-accessible):
  understanding and exercising authority must be manageable for the operator,
  without requiring internal expertise or an agent as the sole intermediary.

- [Bounded failure consequences](./invariants.md#9-failure-consequences-stay-bounded):
  block only dependent operations; preserve useful work and evidence rather than
  automatically restarting execution when a surrounding mechanism fails.

## Recognize drift before acting

- Changing criteria to pass a retry turns implementation into unauthorized intent.
- Treating an executor's self-assessment as evaluation removes independent judgment.
- An evaluator automatically halting execution on a finding takes authority it does not own.
- Marking work provisional without its evaluation evidence substitutes a label for proof.
- Adding machinery to preserve a disproven assumption protects architecture over intent.
- Writing code before placing its constraints makes prevention an afterthought.
- Rebuilding dispatch or harness behavior inside GDAD expands it into the execution loop.

Keep architecture, implementation details, and unapproved proposals outside the
canonical invariant corpus. Placed subsystem `AGENTS.md` files link to the relevant
canonical rules rather than inventing new project guarantees.
