# reader/ — graph reader

Reads a directory of node YAMLs, validates the dependency graph, prints status and the frontier. Read-only. Nothing else.

## Invariants that bind this folder

Rule text is verbatim from `../AGENTS.md`.

**1 Human authority.** "Humans retain authority over project intent, canonical node definitions, dependencies, acceptance criteria, and acceptance of completed work." The reader never writes to the node directory. Not a status flip, not a repaired edge, not a reformatted file.

**3 Independent evaluation.** "The evaluator records drift as evidence rather than halting execution." A graph finding (missing target, unreciprocated edge, complete atop planned, cycle) is printed as a finding. The reader does not refuse to print the graph because of one, and does not fix it.

**4 Evidence-backed progress.** "Evidence supporting progress must remain inspectable, attributable, and recoverable." Every finding names the node ids involved. No finding is collapsed into a count or a summary flag.

**7 Bounded role.** "Executor lifecycle, dispatch mechanics, workspace management, and process supervision remain outside GDAD's ownership." The frontier is eligibility, not an instruction to run. The reader does not dispatch, launch, or pick a node.

**8 Human control accessible.** "Exercising authority must not require understanding internal machinery or depending on an agent as the sole interpreter or operator." Output is plain text a human reads without the agent explaining it.

**9 Bounded failure.** "A failure blocks only the operations whose correctness or safety depends on the failed condition." One bad edge does not stop the rest of the graph from being read and printed. The single hard stop is a duplicate node id, because the graph is ambiguous with two nodes claiming one id and nothing downstream can be trusted.

## Enduring vs replaceable

Enduring:
- Read-only against the node directory.
- Frontier = status not done AND every dependency done.
- All findings printed, none suppressed, none auto-fixed.
- Cycles reported, not broken.

Replaceable (change freely when the node schema or tooling changes):
- Python, pyyaml.
- Field names looked up: node id, `depends_on`, `unlocks`, `status`.
- `DONE = {"complete"}`.
- Directory-path argument, text output format, exit code.

## Failure patterns to recognize before reproducing them

- Loader grows into the UI. GDDP's `gddp.py` was 4877 lines because the graph loader, the TUI, and the status writer shared a file. The reader stays a reader.
- Frontier treated as permission. In GDDP, "eligible" slid into "dispatched." Here the frontier is a list, and whatever dispatches reads it as a list.
- Silent reconciliation. Unreciprocated edges and complete-atop-planned were "fixed" in place by GDDP's reconciler (1935 lines). Here they are findings for the human.
- Schema pinning. The reader must not become the reason the node schema can't change. Four field lookups, nothing more.
