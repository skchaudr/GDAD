---
title: "Contract scenarios"
date: 2026-10-24
tags: []
---

Completely unapproved none of this is authoritative or is binding in anyway or representative of my intent - Sab 10.24.26

# Contract scenarios

We are testing the proposed GDAD data contract with XState. The review model now lives in `model/gdad.machine.ts`; Stately is one visualization tool of possibly many that will utilized to ensure the contract and schema are coherent BEFORE code starts landing. 

## Run

Stately walkthrough — copy the JavaScript simulation:

```sh
pbcopy < /Users/sab-mini/repos/GDAD/.pr-lens/gdad-explained/gdad.machine.js
```

1. Open https://sketch.stately.ai.
2. In **Code**, select all, paste, then click **Update**.
3. Open **Simulation → Start**.
4. Select a scenario event below. Reset the simulation between scenarios.

All automated checks:

```sh
npm run typecheck
npm test
npm run simulate
```

Local inspection: `npm run simulate -- pass` prints the state sequence and records. Available scenarios: `pass`, `accept`, `reject`, `fail`, `pending`, `mismatch`, `unevaluated`. See `model/README.md`.

The earlier JavaScript model, browser walkthrough and tests remain in the local, Git-ignored `.pr-lens/gdad-explained/` folder as the source of this port. Browser import of the TypeScript model still needs verification.

## Results

2026-10-24, sab-air.local: 17 tests passed. These check record handling and state transitions; real execution and evaluation remain the next step. The reported Sketch RUN_PASS discrepancy remains unresolved.

The TypeScript port passes typechecking and 19 tests: the original 17 plus two characterization checks for the model's existing criterion-completeness/consistency limitation. All seven local scenarios run. These results do not adopt the example record shapes as a contract.

## 1. Passing evaluation

Run: `RUN_PASS`. Expected: `Provisional`, with no human decision.

Why: Establish the successful executor → evaluator handoff.

Review: Automated check passes. You confirmed that passing evaluation makes work provisional. Keep the existing result-commit identity and receipt verdict.

Commentary:


## 2. Human acceptance

Run: `RUN_PASS`, then `HUMAN_ACCEPTED`. Expected: `Accepted`.

Why: Distinguish your acceptance from the evaluator's passing judgment.

Review: Automated check passes. You confirmed acceptance stays undecided until you accept. Record that decision against the reviewed work as an input to computed status, outside the node definition.

Commentary:


## 3. Human rejection

Run: `RUN_PASS`, then `HUMAN_REJECTED`. Expected: `Rejected`; passing receipt remains.

Why: Preserve your authority to reject evaluated work.

Review: Automated check passes. Keep the evaluator's judgment and your decision separately visible. This exercises existing human authority.

Commentary:


## 4. Evaluated failure

Run: `RUN_FAIL`. Expected: `EvaluatedFail`, with work and findings preserved.

Why: Exercise the contract's fail verdict.

Review: Automated check passes. GDDP had 30 failing receipt files across 16 nodes. The existing verdict and findings express this outcome. Retry policy adds nothing to this contract check.

Commentary:


## 5. Evaluation pending or unfinished

Run: `RUN_NO_RECEIPT`. Expected: `AwaitingEvaluation`; commit exists, receipt is absent.

Why: Show completed work accurately while evaluation is pending.

Review: Automated checks pass for both an absent receipt and an explicit unevaluated verdict. GDDP timeouts and authentication failures establish unfinished evaluation as a real outcome. The existing unevaluated outcome expresses this; recovery and retry remain outside this review.

Commentary:


## 6. Different commit

Run: `RUN_OTHER_COMMIT`. Expected: `UnmatchedReceipt`; both records remain visible.

Why: Check the existing receipt-to-work identity relationship.

Review: Automated check passes. The historical investigation found no evaluated-commit/diff-tip mismatch. Deprioritize this as a failure scenario; retain the simple identity check. No additional machinery.

Commentary:


## Historical cross-check

- Starting commit A → result B: 116 receipts correctly evaluated the result commit. Existing SHA fields express that result identity. The current model does not represent A or Git HEAD.
- New commit with no changes: 14 receipt files recorded empty diffs. Evaluation can judge missing work using the existing criteria and findings.
- Unavailable commit: one recorded case. Evaluation remains unfinished; no new recovery mechanism follows.
- Different verdicts for the same work, including unsuccessful reevaluation after a pass: observed. Reconciliation is a separate policy question; leave it outside this contract review.

Source: `/Users/sab-mini/repos/gddp-config/verification/`, inspected across 152 receipt files representing 144 attempts.

## Start here

The basic outcomes are expressible: pending evaluation, pass/provisional, fail, unevaluated, and a separate human decision. Keep status computed outside node definitions.

What stands out: the sample assigns an attempt in dispatch but leaves its executor-side encoding unspecified. Resolve that connection with the chosen executor in the first integration.

Next: run one real node through executor output → independent evaluator receipt → computed progress → human decision. Carry these checks into that implementation.
