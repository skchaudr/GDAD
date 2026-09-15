---
title: GDDP rebuild — day-one roadmap
date: 2026-09-09
status: draft
tags: [gddp, rebuild, roadmap, architecture]
---

# GDDP rebuild — day-one roadmap

Companion to [[gddp-resources-keep-or-drop]] and [[gddp-cli-first-principles-spec]].

Written to be read before any code exists. Fresh repo. Old repos tagged, read-only,
reference only.

---

## 1. The premise that changed

The old GDDP was built on: **agents are a black box, so gate on outcomes rather than on
how the work is done.** That's why it became a milestone graph fused with a project map,
and why its entire drift defense is *detection after the fact* — reconstruct intent from
artifacts, judge whether meaning survived.

You've dropped that premise. The replacement: **the how is where the drift lives, and it
can be constrained at the site where work happens.** A placed, implementation-agnostic
manifest is prevention. The DAG-plus-semantic-evaluator is detection.

Consequence, stated plainly so it isn't rediscovered later: **prevention is primary, the
evaluator is the exception path.** Much of the 78k lines is faithful implementation of
the old premise, not sloppiness — which is why it can't be refactored into the new one.

What the evaluator still owes you, and why it survives at all:

- Prevention can't cover everything an agent might do.
- Prevention isn't verification — a constraint being present isn't proof it was honored.
- Human acceptance of evidence is still the last gate.

The ratio inverts. The evaluator stops being the architecture and becomes one mechanism
inside it.

---

## 2. Scope — the acceptance test

GDDP is four things (`GDDP-becomes-small-and-real.md`):

1. The graph — nodes, DAG, node contracts.
2. Placed invariants — the prevention layer. *(new; this is the premise change)*
3. The typed verdict — evaluator evidence, intent/integrity-shaped.
4. The human completion gate.

GDDP is **not** the executor, **not** the agent harness, and **does not rebuild the
loop.** Dispatch, worker invocation, artifacts, heartbeat: someone else's, already
working.

Second acceptance test, and the one that actually binds: **you can state the primitives,
the state, and the transitions out loud without opening a file.** When you can't, either
something crossed the boundary or you stopped holding it. Run this check weekly, not at
postmortem time.

---

## 3. Primitives — the minimum set

**Authored, human-owned:**

- **Graph** — `graphs/<project>/project.yaml`. Intent, blueprint, repo. Rarely changes.
- **Node** — `graphs/<project>/nodes/<id>.yaml`. The atomic unit of project intent.
  `why`, `depends_on`, `acceptance_criteria`, `constraints`, `required_artifacts`,
  `unlocks`. **No `status` field** — see §4.
- **Invariant manifest** — `<subsystem>/AGENTS.md`, the schema from
  `docs/invariants/AGENTS.md`. `rule` implementation-agnostic; `current_implementation`
  explicitly mutable; `drift_pattern` names the failure shape; `is_invariant: false`
  available for present reality.

**Machine-owned:**

- **Progress** — machine journal per project (append-only, actor-attributed). Node id →
  status, receipt ref, timestamp, reason. **`accepted` is not here** — it is committed
  to the milestone graph (§4).
- **Receipt** — the typed verdict. Durable file. Immutable once written.

**Derived — nothing stores these:**

- **Frontier** — a function of progress + `depends_on`. Arithmetic, not state.
- **Timeline** — a fold over nodes, progress, receipts.
- **Attempt** — found by scanning what an executor left behind. Never registered.

Two authored shapes, one manifest shape, two machine shapes, three projections. If the
list grows, something crossed the boundary.

---

## 4. The one architectural decision to make first

**`status` moves out of the node YAML.**

Today it lives inside the node, which welds human-authored intent to machine-mutable
progress in one file. Every consequence of the old system's awkwardness traces to that:

- Publishing a status change costs a git commit and push, because status is in a tracked
  intent file.
- `complete` had to carry both "human accepted this" and "dependents may move," because
  it was the only writable signal in the graph — which is what froze the frontier
  whenever you slept.
- The provisional fix needed a writer in the reconciler, a status-history mechanism, and
  two dependency-gate call sites in different repos, all to widen one enum.
- An agent editing progress touches a file full of intent it shouldn't be editing.

Split them and most of that evaporates. Intent is authored, reviewed, git-tracked, and
boring. Progress is a machine-written file with one field-level rule — *only a human
writes `accepted`* — enforced in one place instead of spread across three modules.
`provisional` becomes a status value, not a subsystem. The frontier reads one file.

**Decided 2026-09-15** — model council, three debaters, verdict confidence 80%
(run dir `~/.pi/agent/council/2026-09-15T11-54-34-825Z`). The prior read of
`docs/learning/One Truth, Two Representations.md` held up: kill the duplication, keep
detection separate from reconciliation, and green requires receipt evidence.

The council refined the split one level deeper — **"status" is two things with opposite
storage requirements:**

- **Machine progress** (`dispatched` / `provisional` / etc.) — churny, machine-owned,
  stays out of git. Append-only, actor-attributed journal; rides on whatever execution
  state Stage 1 builds, never a second state artifact beside it.
- **Human acceptance** (`accepted`) — rare, irreversible, attribution-critical. **It is
  committed to the milestone graph in git** — the only status write git ever sees. A
  human commit is intent, not churn.

The visual graph renders the committed backbone (topology + acceptance) always, with
live machine state as a labeled overlay, degrading honestly to "runtime unhydrated."

**Acceptance criteria of this decision** (ship with it or it fails quietly — skeptic's
dissent, adopted):

1. Journal is append-only and actor-attributed; a mutable status row surrenders the
   audit case.
2. Evaluator packets are built at one enforced construction point, enumerated committed
   fields *minus* acceptance, with a status-free contract test.
3. Journal export/restore ships day one; export bound to the accept command so it runs
   on a cadence.
4. Execution↔milestone node-id mapping validated by the node validator; one restore
   round-trip test — the first real restore must not be the drill.
5. The accept command requires an interactive TTY under the operator identity.
6. Acceptance-invalidation semantics specified before the render contract closes: what
   renders when machine activity postdates `accepted`; revocation is human-only. *(The
   smoke-alpha redispatch is the lived example — this is the first design task.)*

---

## 5. Where things live, and what triggers evaluation

Decided 2026-09-11: **one repo for the tool.** The two-repo split (`gddp-config` /
`gddp-runtime`) put one concept in two places: `provisional` needed gate changes in both
`scope_checker.py` and `frontier.py`; `node_cli.py:104` loaded a runtime file by path,
which an audit then marked orphan and authorized deleting. The intent/machine boundary the
split was protecting survives as a directory with its own manifest.

**The split that replaces it follows §4 — intent travels, progress stays home.**

| What | Where | Tracked in git |
|---|---|---|
| Graph + nodes (intent) | `<project-repo>/.gddp/` | yes, with the project |
| Progress, receipts, attempts (machine) | `~/.gddp/state/<project>/` | no |
| Project registry | `~/.gddp/projects/<project>` → symlink to `<project-repo>/.gddp` | no |

Why progress stays out of the project repo: a machine writing into a tracked repo is how
status changes became commits and how git became part of the control flow. Intent is
authored and reviewed, so it belongs to the project. Progress is local machine state, so it
belongs to the tool. Scale follows for free: the tool never holds graphs, only pointers and
state, so "can't hold every graph ever" never becomes a problem.

The one exception to "machine state stays out of git": `accepted` is committed to the
milestone graph by the human accept ceremony (§4). A human commit is intent, not churn.

**Registry = symlinks.** A symlink directory is a registry the filesystem already
understands. A moved repo leaves a dangling link, which is detectable on read — report it,
don't guess. Equivalent to a paths file; pick whichever is easier to inspect.

**When the evaluator runs — throughout the attempt, not once at the end.**

Revised 2026-09-11. An evaluator that exists to catch drift and sees nothing until the
attempt is over is detection after the fact — the premise §1 dropped. The evaluator
observes the attempt while it runs and emits a stream of typed records into the attempt
directory.

**Record types** (the type says what kind of evaluation it is). Most already exist in
`gddp-runtime/scripts/runtime/verification/schemas.py`. **No new types needed:**

| Type | Exists today | When | Authority |
|---|---|---|---|
| `GraphObservation` | yes | during or after | none — operator-visible evidence |
| `IntegrityFinding` | yes | during or after | feeds the current verdict |
| `GraphRecommendation` | yes — 8 typed actions, `evidence` min 1 | any time | none — only a human materializes |
| verdict | yes, **twice** — see below | after the run | gates `provisional` |

What changes: today these are fields nested inside one end-of-run `VerdictReceipt`. In the
rebuild each is a standalone record appended to the attempt as it happens; the receipt
becomes the record stream plus a final verdict.

**The verdict is a graph action.** *(Sab, 2026-09-11)*

`pass` / `fail` / `needs-human-review` say almost nothing. The evaluator's verdict is what
the graph should do next, drawn from the `GraphRecommendation` actions: `split` ·
`supersede` · `insert_prerequisite` · `revise_criteria` · `rewire` · `reorder` ·
`create_node` · `retire_node`. A verdict of `create_node` tells the human more than any
pass/fail could. This replaces both existing verdict vocabularies.

**`pass` means the graph is in integrity** — no action needed. It is exclusive of every
action above: if execution surfaced a deficiency the graph has to change for, the verdict
is that change, never `pass`.

Why this set: every verdict names a forward move (momentum), and every move is a graph
change only the human materializes (intent). None of them stops work.

**`fail` is preserved alongside it.** The graph is sound, the attempt fell short → retry
the same node unchanged, findings as the fix-list.

Verdict set: `pass` · `fail` · the eight graph actions. `pass` and `fail` judge the attempt
against a sound graph; an action says the graph itself has to change.

**Cadence — cheap checks continuously, judgment sparingly.**

- **Executor hooks emit events** (per turn / tool call, and a final hook on completion)
  into `attempts/<id>/events`. The final hook is the gold-standard signal for "the run is
  over."
- **The deterministic lane runs on every event.** Scope checks are cheap: files touched
  outside the node's paths, any write to `.gddp/`, required artifacts appearing.
- **The semantic lane runs at milestones** — commits, a time or turn interval — and on
  the final hook.
- **The tick is the guarantee.** It catches attempts whose executor died without a final
  hook, so a crash still ends in a `verdict`.

**Rules that survive the change.**

- Records are append-only. A later `verdict` supersedes an earlier one; nothing is
  overwritten. Progress reads the latest `verdict`.
- The evaluator observes **artifacts and events** — diffs, files, tool calls — never the
  executor's transcript or reasoning. Watching mid-run makes context separation easier to
  break, so it gets stated here rather than rediscovered.
- **The evaluator never stops execution.** Drift mid-run is recorded, not halted. The
  worst case is recoverable without machinery: no history rewrite, just a new node — a
  `GraphRecommendation` (`create_node`, `supersede`, `insert_prerequisite`) the human
  materializes. The old system halted on `expected_base_commit_sha` mismatches and
  destroyed the evidence a human needed; agents answered a human-in-the-loop question with
  machinery. Runaway cost is bounded by the executor's timeout and budget, not by the
  evaluator.
- **Mechanical mismatches are observations.** Base SHAs, hashes, branch state, missing
  bookkeeping become `GraphObservation`s for the human.
- An evaluator-triggered retry needs cited evidence; uncited findings stay observations.
- Staging: Stage 1 ships the final `verdict` only. Mid-run records arrive in Stage 2,
  once there are real attempts to watch.

**Worktree rule.** Executors work in a worktree of the project repo, which contains a copy
of `.gddp/`. Executors may not modify `.gddp/`; the evaluator reads intent from the
project's main checkout, never from the worktree under evaluation.

---

## 6. The loop

```
author node  →  dispatch to executor  →  executor works under placed invariants
             →  evidence returns  →  deterministic + semantic evaluation  →  receipt
             →  progress = provisional  →  human reviews  →  accepted | ready | deferred
```

Human authority is unchanged and unchanged-able: only a human writes `accepted`.
Provisional advancement means execution continues while you sleep; it never means
acceptance.

---

## 7. Transitions

The complete list of ways the system changes the world. Keep this list short; every
addition needs a justification recorded where the code lives.

| # | Transition | Writes | Who may cause it |
|---|---|---|---|
| 1 | Set progress → `provisional` | progress file + receipt ref | system, on pass verdict |
| 2 | Commit `accepted` to the milestone graph | graph (committed) | **human only** |
| 3 | Set progress → `ready` (reject/retry) | progress file, fix-list | human, or evaluator with cited evidence |
| 4 | Write receipt | receipt file | evaluator |
| 5 | Dispatch | spawns executor; attempt appears on disk | system or human |
| 6 | Materialize a continuation proposal into the graph | node YAML | **human only** |

Not on this list, deliberately: anything that mutates a repo under evaluation, anything
that merges, anything that pushes. Those belong to the loop, and GDDP doesn't rebuild the
loop.

---

## 8. Day-one rules

1. **Nothing enters that you didn't decide.** Agents do work; they don't choose. Use them
   where output is completely and cheaply checkable — reading the old tree, tests against
   a contract you specified, mechanical translation, edge adapters. Write the core
   yourself: the graph model, the verdict contract, what progress means, what GDDP
   refuses to do. Where the decision *is* the code, you write the code.
2. **Invariants get placed before there's code worth protecting.** The early window is
   the dangerous one — whatever exists while the volume is small becomes canon for every
   session after. Root manifest first, including "none of the architecture is sacred."
3. **`rule` never names an implementation.** The moment it does, it stops being
   distinguishable from the code it governs and gets absorbed.
4. **Before adding a layer, name what it compensates for.** If the answer is an earlier
   layer, remove that instead. Prefer deleting a mechanism to guarding one. *(This is the
   `GDDP-rebuild.md` standing rule, relocated from a decisions doc to every site.)*
5. **Files are truth.** A fact that exists only in a database isn't a fact. Any index
   must be purgeable with nothing of architectural value lost.
6. **Minimal, then working, then hardened — and not completeness.** Optimizing for
   completeness at every step is the specific failure that produced 78k lines. A
   subsystem gets hardened after the architecture has survived contact with real nodes,
   never before. Incomplete-but-running beats complete-but-unproven, because you don't
   yet know this is the persistent architecture.
7. **A retry re-attempts the same node unchanged.** Findings are a fix-list. Discovered
   scope becomes a frontier-invisible proposal only a human materializes.
8. **The evaluator never reads executor framing.** Its context is built independently
   from canonical docs, the DAG neighborhood, and evidence.

---

## 9. Staging

**Stage 0 — evidence, in parallel, starting now.**
Run the existing GDDP with your cheapest executors (DeepSeek Flash et al.) against real
nodes, purely to gather evidence. Worst case is that it's abandonable, which has already
happened and costs nothing. Best case it's more workable than expected and encodes
lessons the rebuild would otherwise learn the hard way. Either way you get receipts to
test the new verdict contract against, and one live example of every transition. This
track does not block, and does not receive investment.

**Stage 1 — the smallest thing that closes the loop once.**
Reader (graph + node + progress + receipt), frontier as arithmetic, one executor, one
deterministic lane, a receipt, a human accept. No TUI beyond a picker and a list. No
retry logic, no concurrency, no heartbeat, no second lane. Done when a real node goes
author → dispatch → receipt → accepted, and you can state the primitives from memory.

**Stage 2 — the semantic lane and provisional flow.**
The intent/integrity lane with graph-neighborhood context. `provisional` in the progress
file, dependency gates widened to `{accepted, provisional}`. Retry with fix-list
injection. Done when the frontier advances while you sleep and rejection re-freezes
downstream without a cascade mechanism.

**Stage 3 — hardening, chosen deliberately.**
Concurrency, second executor, recovery, observability. Each one justified against a
failure you actually hit, recorded in the manifest at the site. Anything here that can't
name its failure doesn't get built.

---

## 10. What would tell you this is going wrong

- The primitive list in §3 grows and you can't say which projection it replaced.
- A `rule` in a manifest names a file, function, or flag.
- You add a mechanism whose justification is another mechanism.
- Something gets marked frozen.
- A stage-3 concern shows up during stage 1 because it felt incomplete without it.
- You can't state the transitions out loud.

Any one of those is the same failure the old system had, arriving early enough to stop.
