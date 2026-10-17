#!/usr/bin/env python3
"""GDAD graph reader.
Unfortunately this was not approved to be written, uses an old unapproved schema, and in general assumes a lot. 
It can still be used, but it should be treated as canonical or foundational (yet). 
Usage: gdad.py NODE_DIR

Reads a directory of GDDP-schema node YAML files as they sit, validates the
dependency graph, and prints status and the frontier. Read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

DONE = {"complete"}


def load(node_dir: Path) -> dict[str, dict]:
    nodes: dict[str, dict] = {}
    for path in sorted(node_dir.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        node_id = doc.get("node_id") or doc.get("id") or path.stem
        doc["_path"] = path
        doc.setdefault("depends_on", [])
        doc.setdefault("unlocks", [])
        doc.setdefault("status", "")
        if node_id in nodes:
            raise SystemExit(f"duplicate node_id {node_id}: {path} and {nodes[node_id]['_path']}")
        nodes[node_id] = doc
    return nodes


def validate(nodes: dict[str, dict]) -> list[str]:
    findings: list[str] = []
    for nid, n in nodes.items():
        for dep in n["depends_on"]:
            if dep not in nodes:
                findings.append(f"{nid}: depends_on {dep} does not exist")
            elif nid not in nodes[dep]["unlocks"]:
                findings.append(f"{nid}: depends_on {dep}, but {dep} does not list {nid} in unlocks")
        for u in n["unlocks"]:
            if u not in nodes:
                findings.append(f"{nid}: unlocks {u} does not exist")
            elif nid not in nodes[u]["depends_on"]:
                findings.append(f"{nid}: unlocks {u}, but {u} does not list {nid} in depends_on")
        if n["status"] in DONE:
            for dep in n["depends_on"]:
                if dep in nodes and nodes[dep]["status"] not in DONE:
                    findings.append(f"{nid}: status {n['status']} atop {dep} with status {nodes[dep]['status']}")

    # cycles, via DFS over depends_on
    WHITE, GREY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in nodes}

    def visit(nid: str, stack: list[str]) -> None:
        color[nid] = GREY
        stack.append(nid)
        for dep in nodes[nid]["depends_on"]:
            if dep not in nodes:
                continue
            if color[dep] == GREY:
                cyc = stack[stack.index(dep):] + [dep]
                findings.append("cycle: " + " -> ".join(cyc))
            elif color[dep] == WHITE:
                visit(dep, stack)
        stack.pop()
        color[nid] = BLACK

    for nid in nodes:
        if color[nid] == WHITE:
            visit(nid, [])
    return findings


def frontier(nodes: dict[str, dict]) -> list[str]:
    return [
        nid
        for nid, n in nodes.items()
        if n["status"] not in DONE
        and all(nodes.get(dep, {}).get("status") in DONE for dep in n["depends_on"])
    ]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    node_dir = Path(argv[1])
    nodes = load(node_dir)
    findings = validate(nodes)
    front = frontier(nodes)

    width = max((len(nid) for nid in nodes), default=0)
    for nid, n in nodes.items():
        mark = "*" if nid in front else " "
        print(f"{mark} {nid:<{width}}  {n['status'] or '-':<14} deps={len(n['depends_on'])}")
    print(f"\n{len(nodes)} nodes, {len(front)} on frontier (*), {len(findings)} findings")
    for f in findings:
        print(f"  ! {f}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
