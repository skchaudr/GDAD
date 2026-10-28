---
title: "GDAD review model"
date: 2026-10-24
tags: []
---

None of this is authoritative and treat ALL of it as unapproved untold explicitly told otherwise. This is exactly how agents began to change what by ostensibly focusing on the just the "how" - Sab 10.24.26 


# GDAD review model

The TypeScript machine in `gdad.machine.ts` is the source for this simulation.
It runs locally with XState; Stately is an optional visualization tool.
Changes made in an editor return here for review, rather than living only in a hosted diagram.

This ports the local `.pr-lens/gdad-explained/` simulation. Records are synthetic.
The exported types describe those examples, not an adopted GDAD data contract or node schema.
The node definition remains external and human-authored.

## Run

Node.js 22 or newer:

```sh
npm install
npm run typecheck
npm test
npm run simulate
```

Inspect one scenario's state sequence and complete records:

```sh
npm run simulate -- pass
npm run simulate -- accept reject
```

Available scenarios: `pass`, `accept`, `reject`, `fail`, `pending`, `mismatch`, `unevaluated`.
The runner advances a simulated clock; it does not launch an executor or evaluator.
Its accept/reject inputs are synthetic demonstrations, not human decisions about real work.

## What is represented

- Executor commit: Git SHA and the reviewed `GDAD-Node` / `GDAD-At` trailers.
- Independent evaluator receipt: node, attempt, commit, checkpoint, verdict and evidence.
- Separate human decision, bound to the reviewed work.
- Derived progress, kept outside the node definition.

The simulation's assigned-attempt and decision objects retain their proposed status.
Executor-side attempt encoding and journal storage are still undecided here.
The two-second timers simulate record arrival; they are not GDAD scheduling policy.

## Checks and boundaries

The tests port the original 17 checks and add two characterization checks for the
known limitation that a matching pass verdict reaches provisional even with empty
criteria or an unmet criterion. Those checks describe the current model; they do
not adopt that behavior as the production contract.

The model checks identity and verdict, not criterion completeness or consistency.
It represents one node and one attempt, with human decisions only after a pass.
Dependencies, frontier calculation, milestones, retries, corrective nodes,
human override after failure, and journal replay remain outside this simulation.
The previously reported Sketch `RUN_PASS` discrepancy still needs browser verification.

## Next implementation step

Review the concrete executor result, receipt and journal examples together.
Keep their writers explicit: the executor produces the work commit and the
independent evaluator produces its receipt; GDAD reads those alongside recorded inputs.
Then write tests for the smallest pure status/frontier reader using those agreed
records, before connecting one real node. The review machine does not itself
approve the contract or replace that reader.
