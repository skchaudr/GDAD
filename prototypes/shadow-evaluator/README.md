# Hosted Jev shadow evaluator — prototype

Observe GDDP's Pi/DeepSeek receipts while the real graph runs. Jev answers closed
questions about the node outcomes, intent alignment, graph integrity, and whether
the intent is concrete enough to test. Each answer is appended to JSONL with its
probabilities, exact question, model, attempt identity, and saved input reference.

This is a receipt-evidence classifier, not a replacement verdict. It does not run
the product's behavioral tests, independently inspect cited files, or generate
test code. It compiles the authored criteria/milestones into runnable Jev questions.
It never calls GDDP mutation APIs, controls executors, accepts nodes, or trains Laya.
The first five nodes are review samples; `human_label` starts null.

## Start

Python 3.11+ and PyYAML, or `uv run` (reads the inline dependency declaration):

```sh
uv run prototypes/shadow-evaluator/shadow.py watch \
  --graph ../gddp-config/graphs/agentos-core/project.yaml
```

Use `TYPESAFE_API_KEY` or `JEV_API_KEY` in the environment. Requests go only to
`https://api.typesafe.ai/v1/systemone`; see the
[TypeSafe API contract](https://docs.typesafe.ai/api).
Model defaults to `JEV_MODEL` or `jev-latest`; returned model IDs are retained.

`--graph` and `--receipts` are repeatable. Default receipt roots are the graph's
config checkout `verification/` and `~/.gddp/receipts/`, restricted to that project.
Both inline nodes and separate `nodes/<id>.yaml` definitions are supported.
The watcher reads current and subsequently written receipts; it deduplicates
receipt contents across restarts. It polls every five seconds. `--once` scans once.

## Evidence and outputs

Default output is `.shadow/` in GDAD (gitignored):

- `answers.jsonl`: one row per closed question, suitable for later reviewed labeling.
- `samples/<hash>/request.json`: exact node, graph, receipt, questions, and supplied evidence.
- `samples/<hash>/response.json`: exact hosted response plus measured round-trip latency.
- `samples/<hash>/complete.json`: request-level usage and completion record.
- `status.json`: watcher PID, last scan time, processed receipt count, and current errors.
- `errors.jsonl`: visible capture/service failures. Failed requests retry after five minutes.

The canonical node version is the version **at capture time**. Historical receipts
may refer to older node definitions; the prototype cannot reconstruct a missing
historical node version. The receipt's work/attempt identifiers remain intact in
the saved request. Receipt claims are explicitly labeled as reported evidence;
`supported` means supported by supplied evidence, not independently reproduced.

The full response is saved before answers are appended. An interrupted append can
resume without repeating the API call. Invalid responses stay explicit and do not
become completed samples. Truncated JSONL lines require repair before continuing;
inputs and responses remain available. One watcher may own an output directory.

## Early / near-end checkpoints

The existing adapter events contain no milestone event. Final receipt collection
is automatic; an actual milestone checkpoint currently needs an explicit call:

```sh
uv run prototypes/shadow-evaluator/shadow.py checkpoint \
  --graph ../gddp-config/graphs/agentos-core/project.yaml \
  --node skill-backbone-automation --phase near-end \
  --attempt-id ACTUAL_ATTEMPT_ID --evidence /path/to/observed-results.json
```

`--evidence` is repeatable. Files are copied into the saved request with hashes,
not merely referenced by a path that can change. Supply observed results, not
executor narration. A `--phase card` call collects a pre-execution baseline.
An optional `--receipt` must match the requested project/node/attempt.

## What to assess

Compare each question's probabilities with the receipt and what actually happened.
Record correct findings, false flags, missed problems, and whether an early finding
would have helped. A confident answer is not a verified label. Retain raw responses
so future Laya work can use human-reviewed examples without treating Pi or Jev as truth.

## Verification

```sh
python3 -m unittest discover -s prototypes/shadow-evaluator -p 'test_*.py'
```

Tests use temporary synthetic receipts and no network. Live validation belongs in
a separate output directory and marks synthetic requests explicitly.

## Runtime seams inspected

- `scripts/runtime/verification/bridge.py`: executor-return entry, Pi/DeepSeek defaults,
  receipt root under the config checkout's `verification/`.
- `orchestrator.py`: deterministic checks, criteria lane, separate integrity lane,
  combined receipt with work/attempt provenance.
- `semantic/pi_runner.py` and `integrity_runner.py`: existing read-only Pi investigators.
- `schemas.py` and `receipt_sink.py`: typed recommendations and persisted receipt layout.
- `scripts/adapters/executor_events.py`: canonical tool/turn events, no milestone event.
- `cursor_cli_adapter.py`, `pi_rpc_adapter.py`, and `runtime/local_attempt.py`:
  packet, events, worktree pointer, exit/result files shared by local attempts.

These are inspected integration boundaries; the prototype imports none of them.

## Active installation on sab-mini

The login service `ai.sab.gdad-shadow` watches `agentos-core`. Its local launcher
and plist are in `.shadow/`; the installed plist is in `~/Library/LaunchAgents/`.
It loads the existing TypeSafe Keychain credential through the local
`~/.config/zsh/ai-routing.zsh` helper. No key is stored in this project or the plist.
It starts at login after reboot and keeps running through evaluator API failures.

```sh
cat .shadow/status.json
tail -f .shadow/answers.jsonl
launchctl print gui/$(id -u)/ai.sab.gdad-shadow
```

To stop the shadow service:

```sh
launchctl bootout gui/$(id -u)/ai.sab.gdad-shadow
```

Validation on 2026-09-28: six automated boundary/recovery tests passed; hosted Jev
distinguished synthetic duplicate bridge records from a correct record count
(271/312 ms observed request times). A live synthetic receipt scan also verified
API-to-JSONL capture and restart deduplication. Synthetic evidence lives separately
in `.shadow/validation/` and is marked `synthetic: true`. These checks validate the
plumbing and those narrow cases, not general evaluator accuracy.
