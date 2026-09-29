# Hello World

Uses the installed `@osolmaz/pi-workflows` package (verified with 0.17.5).

Open Pi in GDAD, then enter:

```text
/workflow hello Sab
```

The graph is deliberately one step:

```text
input: { task: "Sab" }
  → greet (Pi agent; 60-second timeout)
  → validate the submitted greeting
  → complete: { greeting: "Hello, Sab!" }
```

Read `hello.workflow.ts`: `startAt` selects the step, `agent` requests model
work, `expectedOutput` describes its answer, and `validate` checks it in code.
`allowedTools: []` permits workflow submission/update only. With no outgoing
edge, the accepted greeting finishes the run. `maxSteps: 1` bounds execution.

Inspect saved results with `pi-workflows runs`, then
`pi-workflows view <run-id> --once`. The package stores run state in its existing
`~/.pi/agent/workflows/state.sqlite` database.

Verified run: `20260929T063603812Z-hello-a291d6e0`, completed in 6.8 seconds;
the viewer reported `greet: ok` and `{"greeting":"Hello, Sab!"}`.

Local setup repair on the Air: the workflow package could not resolve its Pi
agent peer dependency. A package-local `node_modules/@earendil-works/pi-coding-agent`
symlink now points to the existing `/opt/homebrew/lib/node_modules/@earendil-works/pi-coding-agent`.
This is an installation repair, separate from the portable workflow definition.

The print-mode Pi session emitted persisted-entry/stale-context warnings on exit.
The workflow viewer independently confirmed the run and output were complete.
Raw session evidence is in `.shadow/pi-workflow-hello/session.jsonl`.

# Example 2: evidence and branching

Read `evidence-review.workflow.ts`, then try these separately in Pi:

```text
/workflow evidence-review complete
/workflow evidence-review missing
```

```text
prepare (code supplies a criterion and the complete example document)
  → review (LLM returns verdict, exact quote, and reason)
  → switch on verdict
      supported      → return finding and finish
      needs_evidence → return finding plus evidence request and finish
```

Both inputs are teaching fixtures. `complete` includes a next action; `missing`
contains only status information. The agent receives the actual text. Validation
checks the output shape and that a supporting quote exists verbatim in the text;
the semantic judgment remains the model's responsibility.

This introduces `compute`, passing outputs between steps, and a `switch` edge.
Each run visits three nodes, including one model step bounded to 60 seconds.
The evidence request is saved output, not an automatic retry or human checkpoint.

A later classifier integration can use an `action` node to call Jev, save its
typed response, and pass that response plus the source evidence into an `agent`
node. A switch can decide when that follow-up agent is needed.
