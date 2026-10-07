#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""gdad — graph reader, journal, frontier, and the human gate.

Single entry point. No database, no daemon. Intent lives in <repo>/.gdad/
(committed). Machine progress is an append-only journal under
~/.gdad/state/<project>/ (never committed). The only status ever committed is
`accepted`, written by `gdad accept` from an interactive TTY.

Nothing derivable is stored: `gdad status` computes every node's state on read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

GRAPH_ACTIONS = {
    "split", "supersede", "insert_prerequisite", "revise_criteria",
    "rewire", "reorder", "create_node", "retire_node",
}
VERDICTS = {"pass", "fail"} | GRAPH_ACTIONS


class GdadError(Exception):
    pass


# ----------------------------------------------------------------- paths ---
def repo_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for cand in (p, *p.parents):
        if (cand / ".gdad" / "project.yaml").exists():
            return cand
    raise GdadError("no .gdad/project.yaml found here or in any parent")


def state_dir(project_id: str) -> Path:
    base = Path(os.environ.get("GDAD_STATE_DIR") or Path.home() / ".gdad" / "state")
    return base / project_id


def journal_path(project_id: str) -> Path:
    return state_dir(project_id) / "journal.jsonl"


def receipts_dir(project_id: str) -> Path:
    return state_dir(project_id) / "receipts"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ----------------------------------------------------------------- graph ---
@dataclass
class Node:
    id: str
    title: str
    depends_on: list[str]
    acceptance_criteria: list[dict]
    path: Path


@dataclass
class Graph:
    root: Path
    project_id: str
    title: str
    nodes: dict[str, Node]
    order: list[str]
    warnings: list[str] = field(default_factory=list)


def load_graph(root: Path) -> Graph:
    """Load and validate. Raises GdadError naming the offending node."""
    gdir = root / ".gdad"
    project = yaml.safe_load((gdir / "project.yaml").read_text()) or {}
    pid = project.get("project_id")
    if not pid:
        raise GdadError("project.yaml: missing project_id")
    listed = list(project.get("nodes") or [])
    nodes: dict[str, Node] = {}
    warnings: list[str] = []
    for f in sorted((gdir / "nodes").glob("*.yaml")):
        data = yaml.safe_load(f.read_text()) or {}
        nid = data.get("id")
        if not nid:
            raise GdadError(f"{f.name}: node has no id")
        if nid in nodes:
            raise GdadError(f"duplicate id: {nid} ({nodes[nid].path.name} and {f.name})")
        if "status" in data:
            raise GdadError(f"{nid}: status field in node YAML; status is derived, never stored")
        crit = data.get("acceptance_criteria")
        if not crit:
            raise GdadError(f"{nid}: missing acceptance_criteria")
        deps = list(data.get("depends_on") or [])
        nodes[nid] = Node(nid, data.get("title", nid), deps, crit, f)
    for nid, n in nodes.items():
        for d in n.depends_on:
            if d not in nodes:
                raise GdadError(f"{nid}: unresolved depends_on: {d}")
    cycle = find_cycle(nodes)
    if cycle:
        raise GdadError("dependency cycle: " + " -> ".join(cycle))
    for nid in listed:
        if nid not in nodes:
            warnings.append(f"project.yaml lists {nid} but nodes/{nid}.yaml is missing")
    for nid in nodes:
        if nid not in listed:
            warnings.append(f"nodes/{nid}.yaml exists but project.yaml does not list it")
    order = topo_order(nodes, listed)
    return Graph(root, pid, project.get("title", pid), nodes, order, warnings)


def find_cycle(nodes: dict[str, Node]) -> list[str] | None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    stack: list[str] = []

    def visit(n: str) -> list[str] | None:
        color[n] = GRAY
        stack.append(n)
        for d in nodes[n].depends_on:
            if color[d] == GRAY:
                return stack[stack.index(d):] + [d]
            if color[d] == WHITE:
                r = visit(d)
                if r:
                    return r
        stack.pop()
        color[n] = BLACK
        return None

    for n in nodes:
        if color[n] == WHITE:
            r = visit(n)
            if r:
                return r
    return None


def topo_order(nodes: dict[str, Node], preferred: list[str]) -> list[str]:
    seen: list[str] = []

    def visit(n: str) -> None:
        if n in seen:
            return
        for d in nodes[n].depends_on:
            visit(d)
        seen.append(n)

    for n in [*preferred, *nodes]:
        if n in nodes:
            visit(n)
    return seen


# --------------------------------------------------------------- journal ---
REQUIRED_FIELDS = ("ts", "actor", "node", "event", "reason")


def journal_append(project_id: str, *, actor: str, node: str, event: str, reason: str, **extra) -> dict:
    rec = {"ts": now_iso(), "actor": actor, "node": node, "event": event, "reason": reason, **extra}
    p = journal_path(project_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return rec


def journal_read(project_id: str) -> tuple[list[dict], list[str]]:
    """Every well-formed line, in order. A torn final line is reported, not fatal."""
    p = journal_path(project_id)
    if not p.exists():
        return [], []
    raw = p.read_bytes()
    lines = raw.split(b"\n")
    records: list[dict] = []
    problems: list[str] = []
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            missing = [k for k in REQUIRED_FIELDS if k not in rec]
            if missing:
                raise ValueError(f"missing {missing}")
            records.append(rec)
        except ValueError as e:
            last = i == len(lines) or all(not l.strip() for l in lines[i:])
            kind = "torn final line" if last else "malformed line"
            problems.append(f"journal {kind} {i} skipped: {e}")
    return records, problems


# -------------------------------------------------------------- receipts ---
def load_receipts(project_id: str, node: str) -> list[dict]:
    d = receipts_dir(project_id) / node
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.json")):
        try:
            r = json.loads(f.read_text())
        except ValueError:
            continue
        r["_path"] = str(f)
        r["_digest"] = hashlib.sha256(f.read_bytes()).hexdigest()
        out.append(r)
    out.sort(key=lambda r: r.get("ts", ""))
    return out


def latest_receipt(project_id: str, node: str) -> dict | None:
    rs = load_receipts(project_id, node)
    return rs[-1] if rs else None


def resolve_receipt(project_id: str, node: str, ref: str | None) -> dict | None:
    if not ref:
        return None
    for r in load_receipts(project_id, node):
        if r.get("id") == ref or r["_path"].endswith(ref):
            return r
    return None


# ---------------------------------------------------------------- derive ---
@dataclass
class NodeState:
    node: str
    state: str
    detail: str = ""
    warnings: list[str] = field(default_factory=list)


def acceptance_path(root: Path, node: str) -> Path:
    return root / ".gdad" / "acceptance" / f"{node}.yaml"


def is_accepted(root: Path, node: str) -> bool:
    return acceptance_path(root, node).exists()


def is_provisional(g: Graph, node: str, events: list[dict], warnings: list[str]) -> bool:
    """A provisional event counts only with a resolvable, passing, latest receipt."""
    # A rejection voids any earlier provisional claim; only look after it.
    cut = max((i for i, e in enumerate(events) if e["event"] in ("rejected", "revoked")), default=-1)
    prov = [e for e in events[cut + 1:] if e["event"] == "provisional"]
    if not prov:
        return False
    e = prov[-1]
    r = resolve_receipt(g.project_id, node, e.get("receipt"))
    latest = latest_receipt(g.project_id, node)
    if r is None:
        warnings.append(f"{node}: provisional event references receipt {e.get('receipt')!r} which does not resolve; satisfies nothing")
        return False
    if r.get("verdict") != "pass":
        warnings.append(f"{node}: provisional event cites receipt with verdict {r.get('verdict')!r}; satisfies nothing")
        return False
    if latest and latest["_path"] != r["_path"]:
        warnings.append(f"{node}: provisional receipt is not the node's latest receipt; satisfies nothing")
        return False
    return True


def dep_satisfied(g: Graph, dep: str, by_node: dict[str, list[dict]], warnings: list[str]) -> bool:
    return is_accepted(g.root, dep) or is_provisional(g, dep, by_node.get(dep, []), warnings)


def derive(g: Graph) -> tuple[list[NodeState], list[str]]:
    records, problems = journal_read(g.project_id)
    by_node: dict[str, list[dict]] = {}
    for r in records:
        by_node.setdefault(r["node"], []).append(r)
    out: list[NodeState] = []
    for nid in g.order:
        n = g.nodes[nid]
        st = NodeState(nid, "ready")
        events = by_node.get(nid, [])
        if is_accepted(g.root, nid):
            st.state = "accepted"
            out.append(st)
            continue
        unmet = [d for d in n.depends_on if not dep_satisfied(g, d, by_node, st.warnings)]
        if unmet:
            st.state, st.detail = "blocked", "waiting on " + ", ".join(unmet)
            out.append(st)
            continue
        if is_provisional(g, nid, events, st.warnings):
            st.state = "provisional"
            out.append(st)
            continue
        receipt = latest_receipt(g.project_id, nid)
        last = events[-1] if events else None
        last_ev = last["event"] if last else None
        if last_ev == "rejected":
            st.state, st.detail = "ready", f"fix-list: {last.get('reason', '')}"
        elif last_ev == "dispatched":
            if last.get("attempt"):
                st.state, st.detail = "dispatched", f"attempt {last['attempt']}"
            else:
                st.state, st.detail = "dispatched-without-evidence", "dispatch requested; no attempt recorded"
        elif last_ev == "completed" and (receipt is None or receipt.get("ts", "") < last["ts"]):
            st.state, st.detail = "unevaluated", "executor finished; no receipt yet"
        elif receipt is not None:
            v = receipt.get("verdict")
            if v == "fail":
                st.state, st.detail = "failed", receipt.get("summary", "")
            elif v in GRAPH_ACTIONS:
                st.state, st.detail = "needs-graph-change", f"evaluator recommends {v}"
            elif v == "pass":
                st.state, st.detail = "unevaluated", "passing receipt exists but no provisional event cites it"
            else:
                st.warnings.append(f"{nid}: receipt has unknown verdict {v!r}")
        out.append(st)
    return out, problems


# ------------------------------------------------------------------- git ---
def git(root: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise GdadError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def operator_identity(root: Path) -> str:
    name = git(root, "config", "user.name", check=False) or getpass.getuser()
    email = git(root, "config", "user.email", check=False)
    return f"{name} <{email}>" if email else name


def is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def require_tty(what: str) -> None:
    if not is_tty():
        raise GdadError(f"{what} requires an interactive TTY under the operator's identity")


def confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")


# ------------------------------------------------------------ commands ---
def cmd_check(args) -> int:
    g = load_graph(repo_root(args.root))
    for w in g.warnings:
        print("warning:", w)
    print(f"ok: {len(g.nodes)} nodes, {g.title}")
    return 0


def cmd_status(args) -> int:
    g = load_graph(repo_root(args.root))
    states, problems = derive(g)
    if args.json:
        print(json.dumps([s.__dict__ for s in states], indent=2))
    else:
        width = max(len(s.node) for s in states) if states else 10
        print(f"{g.title}  ({g.project_id})")
        for s in states:
            deps = ", ".join(g.nodes[s.node].depends_on) or "-"
            print(f"  {s.node:<{width}}  {s.state:<28} {s.detail}".rstrip())
            if args.verbose:
                print(f"  {'':<{width}}  depends_on: {deps}")
    for w in [w for s in states for w in s.warnings] + g.warnings + problems:
        print("warning:", w)
    return 0


def cmd_accept(args) -> int:
    require_tty("gdad accept")
    g = load_graph(repo_root(args.root))
    node = args.node
    if node not in g.nodes:
        raise GdadError(f"unknown node: {node}")
    if is_accepted(g.root, node):
        raise GdadError(f"{node} is already accepted (revoke first)")
    unaccepted = [d for d in g.nodes[node].depends_on if not is_accepted(g.root, d)]
    if unaccepted:
        raise GdadError(f"{node}: dependencies not accepted: {', '.join(unaccepted)}")
    receipt = latest_receipt(g.project_id, node)
    print(f"node:  {node} — {g.nodes[node].title}")
    if receipt:
        print(f"latest receipt: {receipt['_path']}")
        print(f"  verdict: {receipt.get('verdict')}  ts: {receipt.get('ts')}  attempt: {receipt.get('attempt')}")
        if receipt.get("summary"):
            print(f"  {receipt['summary']}")
    else:
        print("no evaluation evidence exists for this node. Accepting records evidence: none.")
    if not confirm("accept and commit?"):
        print("aborted")
        return 1
    sha = git(g.root, "rev-parse", "HEAD")
    record = {
        "node": node,
        "accepted_commit": sha,
        "operator": operator_identity(g.root),
        "ts": now_iso(),
    }
    if receipt:
        record["receipt"] = {"digest": receipt["_digest"], "verdict": receipt.get("verdict"), "path": os.path.basename(receipt["_path"])}
    else:
        record["evidence"] = "none"
    p = acceptance_path(g.root, node)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(record, sort_keys=False))
    rel = p.relative_to(g.root)
    git(g.root, "add", str(rel))
    git(g.root, "commit", "-q", "-m", f"accept({node}): {'receipt ' + record['receipt']['digest'][:12] if receipt else 'evidence: none'}", "--", str(rel))
    print(f"accepted {node} → {rel}")
    archive = do_export(g.project_id, args.export_dir)
    print(f"exported journal and receipts → {archive}")
    return 0


def cmd_reject(args) -> int:
    g = load_graph(repo_root(args.root))
    if args.node not in g.nodes:
        raise GdadError(f"unknown node: {args.node}")
    if is_accepted(g.root, args.node):
        raise GdadError(f"{args.node} is accepted; use revoke")
    journal_append(g.project_id, actor=operator_identity(g.root), node=args.node, event="rejected", reason=args.note)
    print(f"{args.node} → ready (fix-list recorded). Dependents derive back to blocked on next status.")
    return 0


def cmd_revoke(args) -> int:
    require_tty("gdad revoke")
    g = load_graph(repo_root(args.root))
    p = acceptance_path(g.root, args.node)
    if not p.exists():
        raise GdadError(f"{args.node} is not accepted")
    if not confirm(f"revoke acceptance of {args.node} and commit the removal?"):
        print("aborted")
        return 1
    rel = p.relative_to(g.root)
    git(g.root, "rm", "-q", str(rel))
    git(g.root, "commit", "-q", "-m", f"revoke({args.node}): acceptance withdrawn by operator", "--", str(rel))
    journal_append(g.project_id, actor=operator_identity(g.root), node=args.node, event="revoked", reason=args.note or "acceptance revoked")
    print(f"revoked {args.node}")
    return 0


def do_export(project_id: str, out_dir: str | None) -> Path:
    sd = state_dir(project_id)
    sd.mkdir(parents=True, exist_ok=True)
    out = Path(out_dir) if out_dir else sd.parent.parent / "exports"
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = out / f"{project_id}-{stamp}.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        for name in ("journal.jsonl", "receipts"):
            p = sd / name
            if p.exists():
                tf.add(p, arcname=name)
    return archive


def cmd_export(args) -> int:
    g = load_graph(repo_root(args.root))
    print(do_export(g.project_id, args.out))
    return 0


def do_restore(project_id: str, archive: Path) -> None:
    sd = state_dir(project_id)
    sd.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        for m in tf.getmembers():
            if m.name.startswith("/") or ".." in Path(m.name).parts:
                raise GdadError(f"refusing unsafe archive member: {m.name}")
        tf.extractall(sd, filter="data")


def cmd_restore(args) -> int:
    g = load_graph(repo_root(args.root))
    if journal_path(g.project_id).exists() and not args.force:
        raise GdadError("state already exists; pass --force to overwrite from the archive")
    do_restore(g.project_id, Path(args.archive))
    print(f"restored {args.archive} → {state_dir(g.project_id)}")
    return 0


def cmd_journal(args) -> int:
    """Append a machine event (dispatched/completed/provisional). For executors and the evaluator."""
    g = load_graph(repo_root(args.root))
    if args.node not in g.nodes:
        raise GdadError(f"unknown node: {args.node}")
    if args.event == "accepted":
        raise GdadError("accepted is never journaled; it is committed by gdad accept")
    extra = {}
    if args.attempt:
        extra["attempt"] = args.attempt
    if args.receipt:
        extra["receipt"] = args.receipt
    rec = journal_append(g.project_id, actor=args.actor, node=args.node, event=args.event, reason=args.reason, **extra)
    print(json.dumps(rec, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gdad", description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=None, help="project repo (default: find .gdad upward from cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="validate the graph").set_defaults(fn=cmd_check)
    s = sub.add_parser("status", help="derive every node's state")
    s.add_argument("--json", action="store_true")
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser("accept", help="human gate: commit .gdad/acceptance/<node>.yaml")
    s.add_argument("node")
    s.add_argument("--export-dir", default=None)
    s.set_defaults(fn=cmd_accept)
    s = sub.add_parser("reject", help="journal a node back to ready with a fix-list")
    s.add_argument("node")
    s.add_argument("--note", required=True)
    s.set_defaults(fn=cmd_reject)
    s = sub.add_parser("revoke", help="withdraw an acceptance (human only)")
    s.add_argument("node")
    s.add_argument("--note", default=None)
    s.set_defaults(fn=cmd_revoke)
    s = sub.add_parser("export", help="archive journal and receipts")
    s.add_argument("--out", default=None)
    s.set_defaults(fn=cmd_export)
    s = sub.add_parser("restore", help="restore journal and receipts from an archive")
    s.add_argument("archive")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_restore)
    s = sub.add_parser("journal", help="append a machine event")
    s.add_argument("node")
    s.add_argument("event", choices=["dispatched", "completed", "provisional", "evaluated", "note"])
    s.add_argument("--actor", required=True)
    s.add_argument("--reason", required=True)
    s.add_argument("--attempt", default=None)
    s.add_argument("--receipt", default=None)
    s.set_defaults(fn=cmd_journal)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except GdadError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
