---
title: Graph engineering — frameworks, code, and the mix
date: 2026-09-09
status: draft
tags: [graph-engineering, langgraph, architecture, agents]
---

# Graph engineering — frameworks, code, and the mix

Third companion to [[gddp-rebuild-roadmap]] and [[gddp-resources-keep-or-drop]].

Premise: graph engineering is knowing which properties of a graph runtime you actually
need, and that each one is separable and purchasable in plain code. Adopting a graph
framework is one way to buy several at once, at a fixed price.

Sources are primary where cited. Claims I could not verify are marked.

---

## 1. What LangGraph actually is, decomposed

Worth knowing because these are the concepts, and they predate the framework.

**A Pregel runtime.** The `StateGraph` you write is a developer-facing API; `compile()`
converts it into a `Pregel` instance. From LangGraph's own reference: *"The Pregel class is
the core runtime engine of LangGraph, implementing a message-passing graph computation
model inspired by Google's Pregel system,"* featuring *"message passing between nodes in
discrete 'supersteps'."* The reference confirms channels map to `BaseChannel` /
`ManagedValueSpec` implementations, and that compiling a `StateGraph` yields a
`CompiledGraph` extending `Pregel`. The tidier "state keys → channels, nodes →
PregelNodes, edges → channel routing" mapping is from secondary write-ups, not the
reference — treat it as approximately right rather than quoted. Google's Pregel is a BSP
(bulk-synchronous parallel) system —
computation phases separated by communication barriers. LangGraph's docs name the Pregel
lineage; they don't use the term BSP, so read that framing as mine.

**Supersteps.** Nodes activate when a channel receives a message, run, and emit updates.
A node with nothing incoming halts. The barrier at the end of each superstep is what makes
concurrent execution deterministic. (The activate/halt detail is from secondary summaries
of the conceptual docs; "votes to halt" is original Pregel-paper vocabulary. The primary
reference states only the discrete-superstep message passing.)

**Reducers.** Per-state-key merge functions. Nodes return *partial* updates and the
runtime merges them; there is no global mutation. The framing worth stealing: a reducer is
a **concurrency policy for one state key.** Two nodes writing the same key in one
superstep is not a race — it's a merge whose rule you declared in advance.

**Checkpointers.** A snapshot after every superstep. This is what buys durability, resume,
and time travel: `get_state_history()` gives you the checkpoint list; invoking with a past
checkpoint's config **replays** (nodes before it are skipped, nodes after it re-execute,
including LLM calls); `update_state()` on a past checkpoint **forks** a new branch.

**Interrupts.** `interrupt(payload)` inside a node pauses the run and surfaces the payload;
you resume with `Command(resume=value)`. This is the human-in-the-loop mechanism.

**Runtime routing.** Conditional edges pick the next node from state at execution time.

---

## 2. What each concept costs to build yourself

The useful exercise: price each property separately. **These prices are my estimates,
not sourced** — argue with them.

| Property | What it buys | Cost in plain code |
|---|---|---|
| Superstep barrier | Deterministic concurrency | Low. A loop: collect ready work, run it, apply results, repeat. |
| Reducer | Declared merge policy per key | Low as code, real as thinking. A `dict[key, merge_fn]`. The framework doesn't decide the policy for you either. |
| Checkpoint | Durability, resume | Low if state is small and serializable: write it after each barrier. |
| Time travel / fork | Branch from any past state, queryable history | **High.** Ordered history, forked lineages, and re-entry into a partial run. |
| Interrupt | Pause mid-node, resume later | **High if you want a suspended stack.** Near-zero if you make waiting a *state* — see §4. |
| Runtime routing | Dynamic next-step | Trivial. It's an `if`. |
| Streaming through nested graphs | Token/event plumbing across subgraphs | High and tedious. |
| Visualization | Debugging and shared vocabulary | Medium, and genuinely valuable for teams. |

Two of these are expensive: **queryable branching history** and **streaming plumbing**.
Everything else is cheaper than adopting the framework that carries it.

---

## 3. The counter-position, from both sides

**Vercel's.** The AI SDK defines an agent as *"large language models (LLMs) that use tools
in a loop to accomplish tasks"* — three parts: the model decides, tools extend, the loop
manages context and stopping. The primitives are `ToolLoopAgent` with `stopWhen`,
`prepareStep`, `runtimeContext`, `toolsContext`. The loop is the abstraction; there is no
topology to declare.

The part that matters most is that their own abstraction is opt-out: for complex
structured workflows needing predictability, the docs point you at the core functions
(`generateText`, `streamText`) with **explicit control flow** rather than at the agent
class. The escape hatch is the recommended path for the hard case, which is the opposite
of how frameworks usually behave.

**LangGraph's.** It ships a **Functional API** beside the Graph API, on the same runtime.
Its docs recommend the Functional API for *"minimal code changes to existing procedural
code,"* *"standard control flow (if/else, loops, function calls),"* *"rapid prototyping
with less boilerplate,"* and *"linear workflows without complex state sharing"* — and
reserve the Graph API for complex visualization, explicit shared state across many nodes,
multiple decision points, and parallel paths.

So the framework agrees the graph DSL isn't always the win. That's the strongest available
evidence that "framework vs. code" is the wrong axis.

---

## 4. The axis that replaces it

Ask which layer is declarative.

**Position 1 — declarative topology.** The graph is data; a runtime walks it. LangGraph's
Graph API, Airflow-style DAGs. You get visualization, deterministic parallelism, and
checkpointing. You pay boilerplate for small flows and you debug through the runtime.

**Position 2 — imperative control flow, durable primitives.** Control flow is ordinary
code; durability is an annotation or a wrapper. Temporal, DBOS, the AI SDK loop,
LangGraph's own Functional API. You keep language-native branching and lose the topology
as an artifact.

**Position 3 — declarative *intent*, imperative execution.** The graph is not a program.
It's a human-authored statement of what must be true before what, and the work inside each
node is opaque and replaceable.

**GDDP is position 3, and it is not a variant of 1.** Worth being blunt about why, because
it decides how much of §1 applies:

- **No data flows along the edges.** `depends_on` means "don't start this until that is
  accepted." Nothing is passed. There are no channels because there are no messages.
- **Nodes aren't functions.** A node is a contract — `why`, criteria, constraints. It is
  satisfied by an agent, a human, or a different agent on retry. It has no signature.
- **The topology is the deliverable, not the implementation.** A human reads it. It exists
  to be reviewed and amended, which is why only a human writes `accepted`.
- **There is exactly one query:** given progress, which nodes are eligible? That's a
  topological readiness check, not a runtime.

The nearest relatives — my analogy, not a sourced claim — are build systems and package
resolvers: dependency graphs where edges are ordering constraints and nodes are opaque
work, rather than LLM computation graphs.

---

## 5. What to steal anyway

The concepts transfer even though the framework doesn't. And in several cases the
file-based version is *better* for this problem, which is worth noticing rather than
treating as a compromise.

**Superstep barrier → the tick.** Evaluate the frontier, dispatch everything ready,
collect results, apply, repeat. One barrier per tick makes concurrent dispatch
deterministic and makes "what did the system see when it decided that" answerable.

**Reducer → name the one concurrency policy you have.** There's a single concurrent-write
surface: the progress file. Two ticks, or a tick and a human, can write the same node.
Declare the merge rule once — *human writes beat system writes; `accepted` is terminal
against a system write* — instead of discovering it as a race.

**Checkpointer → you already have the pieces, split differently.** Correcting an
overclaim: a receipt is *not* a checkpoint. A checkpoint is the complete state needed to
resume; a receipt is immutable evidence about one node. In your design the **progress file
is the checkpoint** and the receipt is the evidence it points at. That split is an
advantage — evidence stays immutable and inspectable without loading a runtime, while the
resumable state is one small file — but it's a different shape, not a better version of
the same thing.

**Time travel → you already have it, and it's called git.** The expensive property in §2 —
queryable branching history — is free here because intent and progress are files under
version control. Fork is a branch. History is a log.

**Interrupt → make waiting a state, not a resumable position.** Sharpening a claim I
first overstated: with a checkpointer, LangGraph is *not* holding a live suspended stack
either — the checkpoint is durable and `Command(resume=...)` restarts from it. The real
difference is **re-execution cost**. Resuming a LangGraph run replays from the checkpoint,
and nodes after it execute again, LLM calls included. `provisional` + `human_gate` has
nothing to replay: the node reached a status, the tick ended, a human acts whenever, the
next tick reads the file and proceeds. For a gate measured in hours or days rather than
seconds, waiting-as-status is the better fit — and it's the same insight, arrived at from
your side, that the roadmap's §4 split makes structural.

---

## 6. The decision rule

> Use a graph runtime when data flows along the edges and the topology is the program.
> Write plain code when the edges express ordering and eligibility, and the nodes are
> opaque work.

GDDP is unambiguously the second. That's why adopting LangGraph would have been a mistake,
and why knowing what's inside it is still worth the afternoon: the tick, the merge policy,
and interrupt-as-state are the three ideas that survive the translation.

---

## Sources

- [Pregel — LangGraph.js API reference](https://langchain-ai.github.io/langgraphjs/reference/classes/langgraph.Pregel.html)
- [Choosing APIs — LangGraph docs](https://docs.langchain.com/oss/python/langgraph/choosing-apis)
- [Interrupts — LangGraph docs](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Time travel — LangGraph docs](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
- [Agents overview — AI SDK](https://ai-sdk.dev/docs/agents/overview)

---

## Audit record

Reviewed against sources after drafting, adversarially. What changed:

1. **Corrected an overclaim (§5):** "every receipt is a checkpoint" was wrong. A checkpoint
   is resumable state; a receipt is evidence about one node. The progress file is the
   checkpoint. Rewritten.
2. **Corrected a comparative claim (§5):** "no suspended execution anywhere" implied
   LangGraph holds a live suspended stack. With a checkpointer it doesn't — its checkpoint
   is durable too. The honest difference is re-execution cost on resume. Rewritten.
3. **Downgraded provenance (§1):** the channels/nodes/edges mapping triplet and the
   activate/vote-to-halt detail came from secondary write-ups, not the primary reference.
   Both now labeled.
4. **Labeled judgment as judgment (§2, §4):** the cost table and the build-system analogy
   are my estimates, not sourced.

**Deliberately excluded.** Search surfaced two quotable-sounding claims — "a 2026 survey of
500+ developers found 80% struggle to select among these frameworks" and "LangChain's
abstractions require traversing seven layers of code" — from aggregator blogs with no
traceable primary source. Also several arXiv PDFs asserting that orchestration degrades
performance relative to in-context prompting, which would be the strongest possible
evidence for §3 if it holds up. I did not read the papers, so none of it is here. If you
want that line of argument, those are worth chasing yourself.

**Still unverified.** The Pregel/BSP lineage rests on LangGraph's own "inspired by Google's
Pregel system" plus my knowledge of the 2010 Malewicz et al. paper; I did not open the
paper this session.
