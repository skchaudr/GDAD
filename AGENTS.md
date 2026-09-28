1. The mantra for this project repository is extreme minimalism. Creating is always easier than destroying when it comes to AI agents. That is paradoxical, because surely writing and editing and creating ought to be harder than running deletion commands. In practice, it's the opposite: the simplicity of deletion makes it dangerous, while the complexity of creation makes it safe. 

Likewise, preserving prior work is also safer, than rightfully acknowledging flawed work, and then deleting it or discarding large portions of it. 

The end result is that bad architecture and assumptions get built upon and never destroyed. Hence the necessity for extreme minimalism, and not being afraid to call out bad work. 

2. The project should be machine-agnostic; the ideal goal is cross-platform, portable to different operating systems. Crucially, cross-platform could achieved easily, but deployment  could be a tedious endeavor; it should be portable enough that less than 10 mins setup is required to get it running on a new machine. That doesn't mean that it's going to be working at its full luxury niceties, that's on the user and the config environment, but the core loop and core capability is non-negotiable. 


--- 

# GDAD invariants

```json
{
  "invariants": [
    {
      "id": 1,
      "name": "Human authority over intent and acceptance",
      "rules": [
        "Humans retain authority over project intent, canonical node definitions, dependencies, acceptance criteria, and acceptance of completed work.",
        "Agents may propose changes and implement within explicitly delegated scope. Authorship does not confer decision authority, and human authority does not require humans to write the implementation themselves.",
        "Tests, execution results, and evaluator verdicts inform human judgment; none can accept a node or authorize a change to project intent on its own.",
        "Given eligible work and sufficient human-authored intent, GDAD supports continued, independently evaluated provisional progress without requiring human review between nodes. Continuation preserves dependency correctness and recoverability; it never confers acceptance authority."
      ]
    },
    {
      "id": 2,
      "name": "Intent preservation and node integrity",
      "rules": [
        "Implementation and retries remain within the target node's declared intent and scope. A retry addresses findings against the same node definition; it does not rewrite the criteria to make the attempt pass.",
        "Discovered out-of-scope work and proposed graph changes remain proposals until authorized by a human. They do not silently become executable work.",
        "Evidence may justify revising, splitting, replacing, or abandoning a node. Preserve the human's intent rather than treating the current node shape as an obligation to finish it unchanged."
      ]
    },
    {
      "id": 3,
      "name": "Independent evaluation",
      "rules": [
        "Evaluation judges project intent and relevant evidence independently of the executor's operational instructions, self-assessment, and persuasive framing.",
        "The evaluator follows the graph to whatever canonical context and evidence are needed to judge intent and graph integrity. Distinguish whether the attempt satisfied its node from whether the evidence warrants revising the graph; a graph defect is not automatically an executor failure.",
        "Evaluation may recommend changes to nodes, criteria, or dependencies beyond the current node. Those recommendations remain human decisions, not automatic graph mutations.",
        "Tests, policy checks, and admission gates may supply evidence and govern subsequent admission or merge. They must not substitute for, suppress, or preempt independent evaluation of the execution result, including failures.",
        "Preventive constraints do not prove their own observance. Evaluation remains necessary even when no guard reports a violation.",
        "The evaluator records drift as evidence rather than halting execution. Execution control belongs to the human and the executor, not the evaluator; findings remain available for judgment rather than triggering machinery that destroys or conceals the evidence."
      ]
    },
    {
      "id": 4,
      "name": "Evidence-backed progress",
      "rules": [
        "A claim that work is evaluated or provisional requires durable evaluation evidence bound to the actual work and attempt being judged. A stale verdict, unrelated result, or success flag is not a substitute.",
        "Missing, interrupted, or failed evaluation remains explicit unfinished evaluation; it must not be presented as work merely awaiting human acceptance.",
        "Evidence supporting progress must remain inspectable, attributable, and recoverable independently of the executor's live session. Derived views must not become the sole surviving record of that evidence.",
        "Evaluator-triggered retries require concrete, cited evidence. Unsupported findings call for human judgment rather than automatic corrective action.",
        "Provisional work remains reviewable and correctable or discardable. Humans can reject the work, override evaluator judgments, or revise the graph without treating automated progress as accepted project truth."
      ]
    },
    {
      "id": 5,
      "name": "Evidence and intent over architectural attachment",
      "rules": [
        "Treat architectural choices as revisable hypotheses. Retain, revise, or remove them according to evidence and project intent—not their existing investment or familiarity.",
        "Justify complexity by the requirement or demonstrated risk it addresses. Prefer removing an unnecessary mechanism to building machinery that exists only to preserve it.",
        "Prove the smallest working design against real work before expanding and hardening it. Additional machinery answers concrete requirements or evidenced risks, not speculative completeness. This does not require allowing a known preventable failure to occur first."
      ]
    },
    {
      "id": 6,
      "name": "Prevention where work happens",
      "rules": [
        "Make the relevant invariants available at the site of work before implementation begins. Constrain how work proceeds rather than relying on an evaluator to reconstruct intent and discover every violation afterward.",
        "Operational guidance keeps enduring rules distinguishable from replaceable implementation choices and names the failure patterns an agent should recognize before reproducing them.",
        "Placed guidance preserves the meaning of the canonical rules. Local convenience or existing code does not create an exception to project intent."
      ]
    },
    {
      "id": 7,
      "name": "A bounded role in development",
      "rules": [
        "GDAD represents intent as a dependency graph, places constraints on work, evaluates evidence, and preserves the human completion gate.",
        "Execution is delegated to replaceable executors. GDAD does not become the agent harness or rebuild its execution loop to compensate for executor behavior. Executor lifecycle, dispatch mechanics, workspace management, and process supervision remain outside GDAD's ownership. Requesting execution or recommending a retry does not transfer ownership of those mechanisms to GDAD.",
        "GDAD keeps execution eligibility, evaluation, and human acceptance distinct. Integrating an executor does not transfer authority over project intent to it."
      ]
    },
    {
      "id": 8,
      "name": "Human control must be accessible",
      "rules": [
        "GDAD makes its intent, progress, evidence, and available decisions understandable and actionable by the human operator, at a manageable cognitive and interaction cost. Exercising authority must not require understanding internal machinery or depending on an agent as the sole interpreter or operator."
      ]
    },
    {
      "id": 9,
      "name": "Failure consequences stay bounded",
      "rules": [
        "A mechanism's authority to block or mutate must be explicitly assigned and justified by the requirement it protects; participation in an operation grants neither authority.",
        "A failure blocks only the operations whose correctness or safety depends on the failed condition. Ancillary failures remain visible without invalidating completed work or preventing unrelated progress.",
        "Preserve useful work and evidence. Retrying or discarding work requires justification beyond a surrounding mechanism's failure; recovery must account for the work already done and the finite resources required to repeat it.",
        "Missing evaluation evidence prevents claiming evaluated or provisional progress, not preserving the attempt. Recover the failed evaluation where possible rather than automatically discarding the work and restarting execution."
      ]
    }
  ]
}
```
```
