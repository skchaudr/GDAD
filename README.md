---
title: "GDAD"
date: 2026-09-15
tags: []
---

# GDAD

Graph Driven Agentic Development - taking the lessons away from the first attempt at doing this with the advent of agents in software. The early attempt was 'human determine
s what, agents determine how' but the unforessen pitfall was that the agent's 'how' ended up modifying and determining the 'what.' With that established, this attempt is now changing up the entire approach; the driving principles this time will be around disciplined ownership over the human-in-the-loop review time, and investing early in improving observability and ending the black box relationship between when an agent starts and finishes its work.

**The goal: make it safe to not be watching.**

## Running it

One file, no database, no daemon. Needs `uv`, or python3 with PyYAML.

```sh
./gdad.py check          # validate .gdad/: ids, depends_on, cycles, criteria
./gdad.py status -v      # derive every node's state; nothing derivable is stored
./gdad.py accept <node>  # human gate; TTY only; commits .gdad/acceptance/<node>.yaml
./gdad.py reject <node> --note "fix-list"
./gdad.py revoke <node>  # the only way to undo an acceptance
./gdad.py export         # journal + receipts → ~/.gdad/exports/<project>-<ts>.tar.gz
./gdad.py restore <archive>
./gdad.py journal <node> dispatched --actor pi --reason "..." --attempt <id>
```

Machine state lives in `~/.gdad/state/<project>/` (`GDAD_STATE_DIR` overrides):
`journal.jsonl` is append-only, `receipts/<node>/*.json` are written by the
evaluator. Tests: `python3 -m unittest discover -s tests -v`.
