# Bootstrap and first integrated proof

The loop (dispatch → evaluate → accept) cannot build itself before it exists.
This file says which nodes are built outside the loop, how they are accepted
honestly, and which attempt proves the loop works. Rules that code must honor
live in the node criteria; this file only sequences them.

## 1. Bootstrap set — built outside the loop

`graph-reader` → `accept` → `evaluator` (final verdict only) → `dispatch` (one executor)

- Built in-session, committed normally, with no dispatch record and no receipt.
- **Never provisional.** Provisional requires a passing receipt (invariant 4);
  these have none.
- Accepted with `gdad accept` once it exists. The record says `evidence: none`
  and you confirm against that statement. Human authority covers this; nothing
  pretends an evaluation happened.
- Once `evaluator` exists, run `gdad eval` over each bootstrap node's commit
  range. Those receipts are after-the-fact observations: a non-pass is something
  for you to judge, and it never changes acceptance by itself.

No `bootstrap` flag or special-case code. "Accept with no evidence, stated
plainly" is the general rule, and bootstrap is just its first use.

## 2. Dependency rule

A dependency is satisfied by evidence only:

- **accepted**: a committed `.gdad/acceptance/<node>.yaml`, or
- **provisional**: a journal event whose receipt file exists, is a pass, and is
  the node's latest receipt.

Dispatch requires a base commit that contains every dependency's evidenced SHA.
GDAD checks ancestry and refuses a base that fails; it never merges or builds
one. Acceptance requires every dependency to be accepted already. When a
provisional dependency is rejected, its dependents derive back to blocked, and
attempts already running are left alone.

## 3. Recovery

| Failure | What remains | Recovery |
|---|---|---|
| Executor never creates `attempt/<id>` | journal dispatch line | shows dispatched-without-evidence; you `ready` it again or leave it |
| Executor dies mid-run | commits on the attempt ref | final verdict on idle/exit tick, or `gdad eval` by hand on those commits |
| Evaluation errors or is interrupted | attempt, `eval-error` journal line, no receipt | rerun `gdad eval` on the same SHA; never re-dispatch for this |
| Torn journal line | every earlier line | skipped with a warning |
| Journal/receipts lost | committed acceptance records (self-describing) | `gdad restore` from the archive written at each accept |

GDAD never retries, kills, or discards an attempt by itself (invariant 9).

## 4. Observation boundary

GDAD sees **git objects reachable from `attempt/<id>`**, plus its own journal and
receipts. It does not see the executor's process, transcript, logs, packet
echo, uncommitted files, or what the executor claims about itself. Milestone
progress is an evaluator judgment over committed work. The executor is never
told the milestones and never receives beat results.

## 5. First integrated proof

**Node:** `align-observability-docs`, held undispatched until the bootstrap set
is accepted.

It is a real defect: those docs currently authorize the evaluator behavior that
invariants 3 and 7 forbid, and the defect blocks `milestone-beat`. It is small,
its scope is two files, and its criteria need a semantic judgment, so it
exercises every Stage 1 transition:

1. `gdad status` shows it ready.
2. `gdad dispatch align-observability-docs` → packet, executor run, ref `attempt/<id>`.
3. `gdad eval` → deterministic lane (scope = two files) + semantic verdict → receipt.
4. Pass → provisional, derived on read. Fail → `gdad reject --note`, re-dispatch the same node unchanged.
5. `gdad accept` → acceptance record committed, export written.

Done when the acceptance record for this node cites a receipt SHA that matches
the commit you merge. `milestone-beat` is the second integrated attempt and the
first code attempt.

`node-drafter` and a second executor are later work, outside this proof.
