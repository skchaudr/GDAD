"""Boundary and recovery checks; synthetic fixtures never enter live samples."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import shadow


def response(request, model):
    answers = {}
    for qid, question in request["questions"].items():
        options = question["criteria"]
        selected = "insufficient" if "insufficient" in options else next(iter(options))
        answers[qid] = {"type": "choice", "choice": selected, "confidence": 1,
                       "probabilities": {k: int(k == selected) for k in options}}
    return {"model": "test-only", "answers": answers, "usage": {}, "latency_ms": 0}


class ShadowChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.graph = self.root / "graphs" / "demo" / "project.yaml"
        self.graph.parent.mkdir(parents=True)
        self.graph.write_text("project_id: demo\nnodes:\n  - id: bridge\n    milestones:\n      - A request is recorded once.\n")
        self.receipts = self.root / "verification"
        self.receipt_path = self.receipts / "demo" / "bridge" / "attempt.json"
        self.receipt_path.parent.mkdir(parents=True)
        self.receipt = {"project_id": "demo", "node_id": "bridge", "verdict": "pass",
                        "execution_attempt_id": "attempt-1"}
        self.receipt_path.write_text(json.dumps(self.receipt))
        self.output = self.root / "shadow"
        self.args = argparse.Namespace(graph=[str(self.graph)], receipts=[str(self.receipts)],
            output=str(self.output), model="test-only", once=True, interval=.01)

    def test_receipt_capture_restart_and_no_source_mutation(self):
        before = {p: p.read_bytes() for p in (self.graph, self.receipt_path)}
        with patch.object(shadow, "ask", side_effect=response) as api:
            self.assertEqual(shadow.watch(self.args), 0)
            self.assertEqual(shadow.watch(self.args), 0)
            self.assertEqual(api.call_count, 1)
        rows = [json.loads(x) for x in (self.output / "answers.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(x["human_label"] is None for x in rows))
        self.assertTrue(all(x["execution_attempt_id"] == "attempt-1" for x in rows))
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_service_failure_keeps_input_and_does_not_mark_processed(self):
        with patch.object(shadow, "ask", side_effect=RuntimeError("Hosted Jev HTTP 503")):
            self.assertEqual(shadow.watch(self.args), 1)
        self.assertEqual(json.loads((self.output / "watch-state.json").read_text())["processed"], [])
        self.assertEqual(len(list((self.output / "samples").glob("*/request.json"))), 1)
        self.assertFalse((self.output / "answers.jsonl").exists())

    def test_resume_response_without_repeating_api_call(self):
        request = shadow.packet(self.graph, "bridge", "final", self.receipt)
        sample_id = shadow.sample(request, self.output, "test-only", response)
        # Simulate interruption after the first answer was appended.
        log = self.output / "answers.jsonl"
        log.write_text(log.read_text().splitlines()[0] + "\n")
        with patch.object(shadow, "ask", side_effect=AssertionError("must reuse saved response")):
            self.assertEqual(shadow.sample(request, self.output, "test-only"), sample_id)
        rows = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertEqual(len({x["question_id"] for x in rows}), 4)
        self.assertEqual(len(rows), 4)

    def test_separate_node_file_and_malformed_receipt(self):
        nodes = self.graph.parent / "nodes"
        nodes.mkdir()
        (nodes / "bridge.yaml").write_text("node_id: bridge\nacceptance_criteria:\n  - id: unique\n    criterion: Each request has one record.\n")
        request = shadow.packet(self.graph, "bridge", "card")
        self.assertEqual(len(request["questions"]), 5)
        self.receipt_path.write_text('{"project_id":')
        with patch.object(shadow, "ask") as api:
            self.assertEqual(shadow.watch(self.args), 1)
            api.assert_not_called()

    def test_invalid_answer_cannot_become_a_sample(self):
        request = shadow.packet(self.graph, "bridge", "card")
        with self.assertRaises(ValueError):
            shadow.sample(request, self.output, "test-only", lambda *args: {"answers": {}})
        self.assertFalse((self.output / "answers.jsonl").exists())

    def test_other_project_receipt_is_ignored(self):
        self.receipt["project_id"] = "unrelated"
        self.receipt_path.write_text(json.dumps(self.receipt))
        with patch.object(shadow, "ask") as api:
            self.assertEqual(shadow.watch(self.args), 0)
            api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
