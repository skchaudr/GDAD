"""Tests for gdad.py. Run: python3 -m unittest discover -s tests -v"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gdad  # noqa: E402
import yaml  # noqa: E402


def write_node(root: Path, nid: str, deps=(), criteria=True, extra: dict | None = None):
    d = {"id": nid, "title": nid, "depends_on": list(deps)}
    if criteria:
        d["acceptance_criteria"] = [{"id": "ac-1", "criterion": "x"}]
    if extra:
        d.update(extra)
    (root / ".gdad" / "nodes").mkdir(parents=True, exist_ok=True)
    (root / ".gdad" / "nodes" / f"{nid}.yaml").write_text(yaml.safe_dump(d))


def make_repo(tmp: Path, nodes: dict[str, tuple]) -> Path:
    root = tmp / "proj"
    (root / ".gdad").mkdir(parents=True)
    (root / ".gdad" / "project.yaml").write_text(yaml.safe_dump({"project_id": "t", "title": "T", "nodes": list(nodes)}))
    for nid, deps in nodes.items():
        write_node(root, nid, deps)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Op", "-c", "user.email=op@x", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Op", "-c", "user.email=op@x", "commit", "-q", "-m", "seed"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Op"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "op@x"], cwd=root, check=True)
    return root


def receipt(pid: str, node: str, rid: str, verdict: str, ts: str) -> Path:
    d = gdad.receipts_dir(pid) / node
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{rid}.json"
    p.write_text(json.dumps({"id": rid, "node": node, "verdict": verdict, "ts": ts, "attempt": "a1"}))
    return p


def states(root: Path) -> dict[str, gdad.NodeState]:
    g = gdad.load_graph(root)
    out, _ = gdad.derive(g)
    return {s.node: s for s in out}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        os.environ["GDAD_STATE_DIR"] = str(self.tmp / "state")

    def tearDown(self):
        os.environ.pop("GDAD_STATE_DIR", None)


class CheckRejections(Base):
    def test_duplicate_id(self):
        root = make_repo(self.tmp, {"a": ()})
        (root / ".gdad" / "nodes" / "a2.yaml").write_text((root / ".gdad" / "nodes" / "a.yaml").read_text())
        with self.assertRaisesRegex(gdad.GdadError, "duplicate id: a"):
            gdad.load_graph(root)

    def test_unresolved_dependency(self):
        root = make_repo(self.tmp, {"a": ("ghost",)})
        with self.assertRaisesRegex(gdad.GdadError, "a: unresolved depends_on: ghost"):
            gdad.load_graph(root)

    def test_cycle(self):
        root = make_repo(self.tmp, {"a": ("b",), "b": ("c",), "c": ("a",)})
        with self.assertRaisesRegex(gdad.GdadError, "dependency cycle: .*a.*b.*c.*a"):
            gdad.load_graph(root)

    def test_missing_criteria(self):
        root = make_repo(self.tmp, {"a": ()})
        write_node(root, "a", criteria=False)
        with self.assertRaisesRegex(gdad.GdadError, "a: missing acceptance_criteria"):
            gdad.load_graph(root)

    def test_status_field_rejected(self):
        root = make_repo(self.tmp, {"a": ()})
        write_node(root, "a", extra={"status": "done"})
        with self.assertRaisesRegex(gdad.GdadError, "a: status field"):
            gdad.load_graph(root)

    def test_cli_exit_code_names_node(self):
        root = make_repo(self.tmp, {"a": ("ghost",)})
        r = subprocess.run([sys.executable, str(Path(gdad.__file__)), "--root", str(root), "check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("a: unresolved depends_on: ghost", r.stderr)


class Journal(Base):
    def test_torn_final_line_is_skipped_and_reported(self):
        root = make_repo(self.tmp, {"a": ()})
        gdad.journal_append("t", actor="x", node="a", event="dispatched", reason="r", attempt="a1")
        gdad.journal_append("t", actor="x", node="a", event="completed", reason="r")
        with gdad.journal_path("t").open("a") as fh:
            fh.write('{"ts": "2026", "actor": "x", "no')  # torn
        recs, problems = gdad.journal_read("t")
        self.assertEqual([r["event"] for r in recs], ["dispatched", "completed"])
        self.assertEqual(len(problems), 1)
        self.assertIn("torn final line 3", problems[0])
        self.assertEqual(states(root)["a"].state, "unevaluated")

    def test_append_only_fields(self):
        gdad.journal_append("t", actor="x", node="a", event="note", reason="r")
        rec = json.loads(gdad.journal_path("t").read_text().splitlines()[0])
        for k in gdad.REQUIRED_FIELDS:
            self.assertIn(k, rec)


class Derivation(Base):
    def test_dispatched_without_evidence(self):
        root = make_repo(self.tmp, {"a": ()})
        gdad.journal_append("t", actor="x", node="a", event="dispatched", reason="go")
        self.assertEqual(states(root)["a"].state, "dispatched-without-evidence")

    def test_dependency_satisfied_by_provisional_with_passing_latest_receipt(self):
        root = make_repo(self.tmp, {"a": (), "b": ("a",)})
        receipt("t", "a", "r1", "pass", "2026-01-01T00:00:00Z")
        gdad.journal_append("t", actor="eval", node="a", event="provisional", reason="pass", receipt="r1")
        s = states(root)
        self.assertEqual(s["a"].state, "provisional")
        self.assertEqual(s["b"].state, "ready")

    def test_provisional_without_resolvable_receipt_satisfies_nothing(self):
        root = make_repo(self.tmp, {"a": (), "b": ("a",)})
        gdad.journal_append("t", actor="eval", node="a", event="provisional", reason="pass", receipt="missing")
        s = states(root)
        self.assertNotEqual(s["a"].state, "provisional")
        self.assertEqual(s["b"].state, "blocked")
        self.assertTrue(any("does not resolve" in w for w in s["b"].warnings + s["a"].warnings))

    def test_provisional_receipt_superseded_by_newer_receipt(self):
        root = make_repo(self.tmp, {"a": (), "b": ("a",)})
        receipt("t", "a", "r1", "pass", "2026-01-01T00:00:00Z")
        gdad.journal_append("t", actor="eval", node="a", event="provisional", reason="pass", receipt="r1")
        receipt("t", "a", "r2", "fail", "2026-02-01T00:00:00Z")
        s = states(root)
        self.assertEqual(s["b"].state, "blocked")
        self.assertEqual(s["a"].state, "failed")

    def test_graph_action_verdict(self):
        root = make_repo(self.tmp, {"a": ()})
        receipt("t", "a", "r1", "split", "2026-01-01T00:00:00Z")
        self.assertEqual(states(root)["a"].state, "needs-graph-change")


class Gate(Base):
    def _args(self, root, **kw):
        ns = mock.Mock()
        ns.root = root
        ns.export_dir = str(self.tmp / "exports")
        for k, v in kw.items():
            setattr(ns, k, v)
        return ns

    def test_accept_refuses_without_tty(self):
        root = make_repo(self.tmp, {"a": ()})
        with mock.patch.object(gdad, "is_tty", return_value=False):
            with self.assertRaisesRegex(gdad.GdadError, "interactive TTY"):
                gdad.cmd_accept(self._args(root, node="a"))
        self.assertFalse(gdad.acceptance_path(root, "a").exists())

    def test_accept_refuses_unaccepted_dependencies(self):
        root = make_repo(self.tmp, {"a": (), "b": ("a",)})
        with mock.patch.object(gdad, "is_tty", return_value=True), mock.patch.object(gdad, "confirm", return_value=True):
            with self.assertRaisesRegex(gdad.GdadError, "b: dependencies not accepted: a"):
                gdad.cmd_accept(self._args(root, node="b"))

    def test_accept_commits_self_describing_record_and_exports(self):
        root = make_repo(self.tmp, {"a": ()})
        with mock.patch.object(gdad, "is_tty", return_value=True), mock.patch.object(gdad, "confirm", return_value=True), redirect_stdout(io.StringIO()):
            self.assertEqual(gdad.cmd_accept(self._args(root, node="a")), 0)
        rec = yaml.safe_load(gdad.acceptance_path(root, "a").read_text())
        self.assertEqual(rec["node"], "a")
        self.assertEqual(rec["evidence"], "none")
        self.assertEqual(rec["operator"], "Op <op@x>")
        self.assertRegex(rec["accepted_commit"], r"^[0-9a-f]{40}$")
        log = subprocess.run(["git", "log", "--format=%s %an", "-1"], cwd=root, capture_output=True, text=True).stdout
        self.assertIn("accept(a): evidence: none Op", log)
        self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout, "")
        self.assertEqual(states(root)["a"].state, "accepted")
        self.assertTrue(list((self.tmp / "exports").glob("t-*.tar.gz")))

    def test_accept_with_receipt_records_digest(self):
        root = make_repo(self.tmp, {"a": ()})
        p = receipt("t", "a", "r1", "pass", "2026-01-01T00:00:00Z")
        with mock.patch.object(gdad, "is_tty", return_value=True), mock.patch.object(gdad, "confirm", return_value=True), redirect_stdout(io.StringIO()):
            gdad.cmd_accept(self._args(root, node="a"))
        rec = yaml.safe_load(gdad.acceptance_path(root, "a").read_text())
        self.assertEqual(rec["receipt"]["verdict"], "pass")
        self.assertEqual(len(rec["receipt"]["digest"]), 64)
        self.assertNotIn("evidence", rec)

    def test_reject_refreezes_dependents_without_cascade(self):
        root = make_repo(self.tmp, {"a": (), "b": ("a",)})
        receipt("t", "a", "r1", "pass", "2026-01-01T00:00:00Z")
        gdad.journal_append("t", actor="eval", node="a", event="provisional", reason="pass", receipt="r1")
        gdad.journal_append("t", actor="exec", node="b", event="dispatched", reason="go", attempt="b-1")
        self.assertEqual(states(root)["b"].state, "dispatched")
        with redirect_stdout(io.StringIO()):
            gdad.cmd_reject(self._args(root, node="a", note="tests missing"))
        s = states(root)
        self.assertEqual(s["a"].state, "ready")
        self.assertIn("tests missing", s["a"].detail)
        self.assertEqual(s["b"].state, "blocked")
        # b's attempt is untouched: its journal line is still there, nothing was appended for b
        recs, _ = gdad.journal_read("t")
        self.assertEqual([r for r in recs if r["node"] == "b"][-1]["event"], "dispatched")

    def test_revoke_requires_tty_and_removes_record(self):
        root = make_repo(self.tmp, {"a": ()})
        with mock.patch.object(gdad, "is_tty", return_value=True), mock.patch.object(gdad, "confirm", return_value=True), redirect_stdout(io.StringIO()):
            gdad.cmd_accept(self._args(root, node="a"))
        with mock.patch.object(gdad, "is_tty", return_value=False):
            with self.assertRaisesRegex(gdad.GdadError, "interactive TTY"):
                gdad.cmd_revoke(self._args(root, node="a", note=None))
        with mock.patch.object(gdad, "is_tty", return_value=True), mock.patch.object(gdad, "confirm", return_value=True), redirect_stdout(io.StringIO()):
            gdad.cmd_revoke(self._args(root, node="a", note=None))
        self.assertFalse(gdad.acceptance_path(root, "a").exists())
        self.assertEqual(states(root)["a"].state, "ready")


class ExportRestore(Base):
    def test_round_trip(self):
        make_repo(self.tmp, {"a": ()})
        receipt("t", "a", "r1", "pass", "2026-01-01T00:00:00Z")
        gdad.journal_append("t", actor="eval", node="a", event="provisional", reason="pass", receipt="r1")
        before_j = gdad.journal_path("t").read_bytes()
        before_r = (gdad.receipts_dir("t") / "a" / "r1.json").read_bytes()
        archive = gdad.do_export("t", str(self.tmp / "exports"))
        import shutil
        shutil.rmtree(gdad.state_dir("t"))
        gdad.do_restore("t", archive)
        self.assertEqual(gdad.journal_path("t").read_bytes(), before_j)
        self.assertEqual((gdad.receipts_dir("t") / "a" / "r1.json").read_bytes(), before_r)


if __name__ == "__main__":
    unittest.main()
