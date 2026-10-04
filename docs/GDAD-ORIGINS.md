# GDAD origins and intent

## Source and scope

This is the durable record of the project owner's origin account in the Delta
conversation accompanying this file's creation. The events are reported history,
not independently reconstructed execution logs. Exact event dates were not
provided.

This account concerns GDAD. Its relationship to MyGraph is unresolved here; this
file does not replace or amend MyGraph's root product contract.
See [the terminology index](GDAD-TERMINOLOGY.md).

## The motivating experience: useful progress while the human is away

The owner discovered Jules, a remote asynchronous coding agent, and OpenClaw,
used as a local always-on agent. The possibility was not simply parallel coding:
one agent could produce work while another received, reviewed, and evaluated it.

During a two-hour break, the owner received a proactive OpenClaw message that a
Jules result was available and could be merged when they returned. OpenClaw then
proactively followed up that the branch had significant issues and should not
yet be merged. That combination of initiative and review was the formative
experience: progress need not stop while the human is away, nor should progress
mean uncritically accepting generated work.

## The failed overnight run

In the lead-up to a previous Santa Cruz New Tech event, the owner and agents
planned an overnight workflow:

1. Dispatch Jules tasks.
2. Receive the resulting work.
3. Evaluate it and accept sufficient work.
4. Ideally, redispatch insufficient or failed work for correction so it could
   earn acceptance before morning.

After the owner gave the go-ahead, OpenClaw did not actually dispatch the tasks.
The owner discovered this the next morning. Planning and apparent readiness had
not translated into execution, and the lack of observability concealed that.

The owner's explicit lesson: black boxes and null observability are no longer
acceptable.

## The event-day rush

The owner subsequently dispatched a flurry of Jules tasks, with two other agents
helping with infrastructure and landing work. A substantial amount was
accomplished in a few hours, but the process was rudimentary and difficult to
follow. The owner was relying on faith in the outcome rather than a visible
system of evaluations, tests, and fast functional sanity checks.

The lesson is not to slow everything down. It is to make rapid progress legible
and grounded enough that the human does not lose the project while agents race
ahead.

## Intended product role

The owner describes GDAD as a project-legibility tool, not an agent/execution
lifecycle owner or session lifecycle owner. Its stated goals are:

- Preserve intent.
- Detect and correct drift.
- Maintain functional and semantic integrity.
- Preserve agent momentum rather than impose slow governance.

The proposed organizing surface is a human- and machine-legible milestone
graph: a statement of intent whose nodes carry acceptance criteria. Completing
the full graph should yield the intended working product, feature, or tool.
The result can be visually rough while still functionally valid.

Demonstrable completion should unlock subsequent eligible work, like progression
through a game map. The earlier project also considered provisional passing;
its precise semantics are not established by this account.

## Why the evaluator matters

The owner reports that the evaluator was the part of the previous project that
repeatedly held up when other parts failed. Jev's reported typed outputs and
per-decision confidence ratings opened new possibilities for that harness.
Laya was identified as a potentially viable local alternative.

The intended balance is to exploit AI capability without overrelying on it.
Neither a detailed evaluator contract nor acceptance thresholds are specified
yet. Confidence must not be represented in these notes as an already-established
guarantee of correctness.

## Questions deliberately left open

- How GDAD relates to MyGraph.
- How preservation of intent, drift detection, and correction are implemented.
- How milestone criteria establish whole-product functionality, including
  integration across nodes.
- What provisional passing permits and what still requires final acceptance.
- Which components dispatch, retry, merge, or manage sessions, and how GDAD
  exchanges evidence and progression decisions with them.
- How observability is presented; the owner has further ideas to discuss.
- The evaluator's typed output contract, confidence interpretation, and evidence
  requirements.

These are open questions, not requests to invent or freeze an architecture
before the owner has finished explaining the approach.
