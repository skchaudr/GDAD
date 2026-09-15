---
title: gddp CLI — first-principles spec (rebuild)
date: 2026-09-09
status: draft
tags: [gddp, cli, rebuild, spec]
---

# gddp CLI — first-principles spec

Drafted outside `gddp-config` on purpose. This is the spec the rebuild is written
*against*; it is not a work order for the existing tree.

Source material: `gddp-config@a206b99` → `docs/gddp-cli-reduction.plan.md` (§2 is the
honest inventory of current behavior), `scripts/gddp.py` at 6672 lines, and the graph /
verification trees as they exist on disk today.

---

## 0. Correction to the number you were working from

You remembered the audit as "6000+ lines down to ~2500." That is not what it says.

- `scripts/gddp.py` is **6672** lines. `scripts/` total is **21672**.
- Plan §7: *"Phase 2 done when `gddp.py` roughly 2800–3200 lines."* That is reached by
  **moving** code into seven new files (`cli_dispatch.py`, `cli_watch.py`, `cli_eval.py`,
  `cli_heartbeat.py`, `cli_status.py`, `cli_parser.py`, `graph_io.py`).
- Same section, stated plainly: *"interactive path across modules stays ~2800–3800.
  `test_gddp.py` 2689 stays. This is not a 500-line product."*

So the plan is a **redistribution**, not a reduction. Total system LOC after all three
phases is roughly what it is now. The 2500 was one file's line count, not the system's.

This matters for the decision: the reduction path was never going to produce a smaller
system. It produces the same system in more files.

---

## 1. Primitives — the nouns that actually exist

Four authored, everything else derived.

### Authored (a human or agent writes these; they are the source of truth)

**Graph** — `graphs/<project_id>/project.yaml`
: `project_id`, `project_name`, `description`, `repo`, `blueprint`
  (`vision`, `architecture_notes`, `major_capabilities`), `execution_policy`.
  Intent. Written at charting time, rarely after.

**Node** — `graphs/<project_id>/nodes/<node_id>.yaml`
: The unit of work, and the *only* place graph-side status lives.
  `node_id`, `title`, `type`, `why`, `depends_on[]`, `acceptance_criteria[{id, criterion}]`,
  `constraints[]`, `allowed_execution_modes[]`, `required_artifacts[]`, `status`,
  `priority`, `unlocks[]`.

**Evaluation receipt** — `verification/<project_id>/<node_id>/` + `verification/<project_id>/evaluations.yaml`
: The verdict on an attempt. Written by the evaluator, read by everything.

**Settings** — `SETTINGS_FIELDS` (`gddp.py:127`)
: Executor, model ids (cheap/expensive), thinking level, integrity on/off, lanes
  (live/deterministic), timeouts, tool allowlist. One config, flat.

### Derived (computed on read; no file is the authority)

**Frontier** — `frontier.py` (396 lines)
: A function of node `status` + `depends_on`. Nothing stores it. Ready / in-flight /
  blocked is arithmetic, not state.

**Attempt** — discovered by scanning spool roots (`_discover_attempts` `4626`,
`_scan_attempts` `4696`, `GDDP_ATTEMPT_SPOOL_DIR` `4617`)
: A directory an executor left behind. Never registered — *found*. Ephemeral by design.

**Timeline** — `timeline.py` (594 lines)
: A fold over nodes + receipts + attempts, ordered.

**Graph truth block** — `_print_graph_truth` `3638`
: nodes / warnings / recent events. A render of the three above.

**Job** — a dispatch record; thin, and mostly a handle onto an attempt.

> The load-bearing observation: **two authored data shapes (graph, node), one verdict
> shape (receipt), one config.** Frontier, timeline, truth, attempts, warnings — all
> projections. A tool over this should be mostly a *reader* with a small number of
> writers.

---

## 2. State transitions — the complete list

Every way this tool can change the world. Eight.

| # | Transition | Writes what | Where it lives today |
|---|---|---|---|
| 1 | Set node status (+ reason) | `nodes/<id>.yaml:status` | `interactive_nodes` `2913`, status write `2901` |
| 2 | Reject + retry | node status → ready, then re-dispatch | `_confirm_reject_and_retry` `2781` |
| 3 | Dispatch | spawns executor process; creates an attempt dir | `build_dispatch_plan` `289`, `cmd_dispatch` `544`, `_confirm_dispatch` `468` |
| 4 | Run evaluation | writes a receipt | `_run_live_eval`, `cmd_eval*` (`4009`–`4380`, `5483`–`5892`) |
| 5 | Publish graph status | `git commit` + `push` | `_offer_publish_graph_status` `2259` |
| 6 | Acceptance merge | `git merge` | `_offer_acceptance_merge` `2450` |
| 7 | Deliver | branch delivery (git) | `cmd_deliver`, `6132`/`6139` |
| 8 | Arm/disarm heartbeat | launchd plist / systemd unit | `_launchd_status` `3743` … `interactive_heartbeat` `3892` |

Grouped by mechanism:

- **In-repo data writes:** 1, 2 (node YAML), 4 (receipt) — plus settings.
- **Git operations:** 5, 6, 7.
- **Process spawn:** 3.
- **OS service:** 8.

Everything else in 6672 lines is reading, projecting, or drawing.

---

## 3. Mechanism — how a transition happens

One shape, and the rebuild should make it literal:

```
pick a target  →  show its current truth  →  confirm the change  →  apply  →  re-render
```

Two rules the current tool breaks often enough that they belong in the spec (both are
plan §4 findings, restated as invariants rather than fixes):

1. **A known value is never typed.** If the set of legal inputs is enumerable — a node
   id, a status, a model, a lane, a graph — it is a picker. Free text is for prose only
   (reject fix-lists, status reasons), and then only after a picker of recent values.
2. **No screen dead-ends.** Every screen either offers a next action or goes back. `Esc`
   is back, `q` is quit, and a "press any key" is legal *only* as an acknowledgment
   immediately after a mutation.

And one bug worth carrying forward as a deliberate decision, not an accident:

> `_menu_choice` `1822`: Esc → `b` if present, else `q`, else **the default**. Confirms
> that register neither `b` nor `q` therefore treat **Esc as yes** — including dispatch
> (`468`), acceptance merge (`2450`, default `y`), and publish (`2259`, default `p` =
> commit **and push**).

In the rebuild, Esc cancels. Universally, structurally, not per-screen. Write it into
the input layer so no individual confirm can opt out.

---

## 4. What the tool is, in one sentence

> A terminal reader over a directory of graph and node YAML plus verification receipts,
> which projects frontier / timeline / truth, and which can cause eight state changes —
> three of them git, one a process spawn, one an OS service, and three writes to files it
> already knows how to read.

If the rebuild ends up much larger than that sentence implies, the sentence was wrong and
should be corrected before more code is written.

---

## 5. Rebuild boundary

**In:** the reader (graph / node / receipt load + validate), the four projections
(frontier, timeline, truth, attempt scan), the input layer (picker, menu, pager, confirm),
and the eight transitions.

**Out, and stays out:**
- Authoring. `new_node.py` (662), `rapid_add.py` (382), `import_node.py` (428),
  `graphify_to_nodes.py` (391), `obsidian_export.py` (392) are their own tools and stay
  callable as themselves. They were never part of the operator loop.
- `node_cli.py` (2122) rich show/list formatting — plan §5 is right that this is the
  product, not fat. Decide separately whether to port it or call it.
- Anything in `gddp-runtime`.

**Kept runnable throughout:** the existing `gddp`, under its current entry point. The new
one ships beside it. Nothing is deleted until you'd rather use the new one.

**Parity oracle:** `scripts/test_gddp.py` (2689). Point it at the rebuild and treat every
failure as a question — *did I mean to change this?* Expect many yesses (see §3). The
value is that each divergence becomes a decision instead of a silent drop.

---

## 6. Open questions — these are yours, not mine

1. **Does the frontier need to be a stored artifact?** Today it is pure arithmetic. If it
   stays derived, `frontier_auto_advance` (seen in `project.yaml` history) is a policy
   evaluated on read, not a state machine. Confirm that's what you want.
2. **Are attempts really discoverable-only?** Scanning spool roots means an attempt that
   moves or is cleaned up vanishes from the timeline. Intentional, or accreted?
3. **One receipt shape or two?** `verification/` and `verification-runtime/` and
   `verification-runtime-live/` all exist at the repo root. Whether that's three shapes or
   one shape in three places decides whether the reader has one loader or three.
4. **Is `status` on the node the right home?** It couples intent (authored) and progress
   (mutable) in one file, which is why publishing a status change is a git commit. A
   separate progress file would decouple them — and would change transitions 1, 2, and 5.
   Worth deciding *before* writing the reader.
5. **Language.** Rebuilding in Python inherits the test suite as a free oracle. Anything
   else, and §5's parity oracle stops working and you need a different one.

Question 4 is the one that actually shapes the architecture. Answer it first.
