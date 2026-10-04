# GDAD terminology

## Status and authority

This index records the project owner's definitions and account supplied in the
Delta conversation accompanying its creation. It preserves vocabulary, not a
completed architecture or independently verified vendor specification.

GDAD's relationship to MyGraph is not yet established in this conversation.
This document does not supersede MyGraph's root product documents. The expansion
of the acronym GDAD has not been supplied; do not invent one.

See [origins and intent](GDAD-ORIGINS.md) for the motivating history.

## Terms

| Term | Meaning in this discussion |
| --- | --- |
| **GDAD** | A project-legibility tool whose stated goals are to preserve intent, detect and correct drift, and maintain functional and semantic integrity while preserving agent momentum. It is not intended to own agent/execution lifecycles or session lifecycles. How it achieves these goals remains to be discussed. |
| **Project map / milestone graph** | A human- and machine-legible statement of project intent. Nodes represent sets of acceptance criteria. Fulfilling the full graph is intended to yield a working product, feature, or tool; visual polish is not inherently required. |
| **Acceptance criteria** | The requirements represented by a node that must be fulfilled for it to be valid or accepted. The precise evidence requirements and acceptance protocol are not yet defined here. |
| **Agent momentum** | Continued useful progress without unnecessary waits for a human to return. The originating example is a remote agent producing work and a local agent proactively reviewing it, enabling correction or onward progress. Not a license to continue without evidence. |
| **Unlocking** | Progression to the next eligible node after demonstrable completion of the current work, analogous to unlocking a level or region in a game. Dependency and eligibility rules remain unspecified. |
| **Provisionally passing** | A provisional progression concept from the earlier project, recalled by the owner. Its exact meaning, permitted downstream actions, and difference from final acceptance remain unspecified. |
| **Evaluator / evaluation harness** | The mechanism for assessing work against intent and acceptance requirements. The owner reports that the earlier evaluator was unusually reliable relative to other parts of the project. This is historical experience, not a measured reliability guarantee. |
| **Observability / legibility** | Making actual work and evaluation progress visible and understandable to humans and machines. A request to dispatch must not be confused with evidence that dispatch occurred. Black-box operation and silent non-execution are motivating failures. |
| **Jules** | Google's asynchronous remote coding agent. As described by the owner, each task starts a cloud machine, performs the task, and completes through a remote branch or pull request. Other uses exist; this is the relevant working definition. |
| **OpenClaw** | The local, always-on agent in the owner's originating workflow. It was expected to dispatch work, receive results, and proactively evaluate or review them. This describes its role in that setup, not a universal deployment requirement. |
| **Hermes** | Another agent mentioned by the owner as part of the growing range of available agents. No specific GDAD role or interface has been defined. |
| **Jev** | Described by the owner as TypeSafe AI's general-purpose intelligent classifier, producing typed classifications/decisions with confidence ratings. These capabilities motivate reconsidering the evaluator; the exact API and confidence semantics have not been verified here. |
| **Laya** | Described by the owner as a weaker but potentially viable local alternative to Jev, already available on their Mac mini. Its capabilities and deployment have not been inspected here. |

## Distinctions to retain

- Preserving momentum is not equivalent to maximizing dispatch volume.
- A branch or PR exists does not mean its work has earned acceptance.
- A dispatch request is not evidence of actual execution.
- Provisional passing must not silently become final acceptance.
- Typed evaluator output and confidence are relevant capabilities; no acceptance
  thresholds, calibration guarantees, or automatic merge policy have been agreed.
- A legibility and integrity tool need not own the workers or their sessions.
  The integration boundary remains open.
