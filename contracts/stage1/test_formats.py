"""Stage 1 format contract.

Schemas live in docs/formats/schemas. These tests are the check, not the
product: there is no reader, executor, or accept command here.

    python3 -m pip install -r contracts/stage1/requirements.txt
    python3 -m pytest contracts/stage1
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "docs" / "formats" / "schemas"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
DOCS = ROOT / "docs" / "formats"
READY = FIXTURES / "ready"

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"
TIMESTAMP = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
ACTIONS = [
    "split",
    "supersede",
    "insert_prerequisite",
    "revise_criteria",
    "rewire",
    "reorder",
    "create_node",
    "retire_node",
]
RETIRED_VERDICTS = [
    "blocked",
    "needs-human-review",
    "needs-more-evidence",
    "out-of-scope-change-detected",
    "drift",
    "insufficient",
    "contradicted",
    "unknown",
]

VALID_FILES = sorted(path for path in (FIXTURES / "valid").rglob("*") if path.is_file())
INVALID_FILES = sorted(path for path in (FIXTURES / "invalid").rglob("*") if path.is_file())
QUOTED = [
    ("graph.md", FIXTURES / "valid" / "project.yaml"),
    ("graph.md", FIXTURES / "valid" / "nodes" / "record-acceptance.yaml"),
    ("graph.md", FIXTURES / "valid" / "acceptance.jsonl"),
    ("journal.md", FIXTURES / "valid" / "journal.jsonl"),
    ("receipt.md", FIXTURES / "valid" / "receipt-pass.json"),
    ("verdict.md", FIXTURES / "valid" / "verdict-pass.json"),
    ("verdict.md", FIXTURES / "valid" / "verdict-fail.json"),
    ("verdict.md", FIXTURES / "valid" / "verdict-create-node.json"),
]


def files(directory):
    return sorted(path for path in directory.rglob("*") if path.is_file())


@pytest.fixture(scope="module")
def contract():
    schemas = {}
    resources = []
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schemas[path.name] = schema
        resources.append((schema["$id"], DRAFT202012.create_resource(schema)))
    return schemas, Registry().with_resources(resources)


def validate(instance, schema_name, contract):
    schemas, registry = contract
    Draft202012Validator(schemas[schema_name], registry=registry).validate(instance)


def rejects(instance, schema_name, contract):
    with pytest.raises(ValidationError):
        validate(instance, schema_name, contract)


def load_yaml(path):
    documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    if len(documents) != 1 or documents[0] is None:
        raise ValueError("expected one YAML document")
    return documents[0]


def instances(path):
    if path.suffix == ".jsonl":
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or any(not line.strip() for line in lines):
            raise ValueError("blank journal or acceptance line")
        return [json.loads(line) for line in lines]
    if path.suffix == ".json":
        return [json.loads(path.read_text(encoding="utf-8"))]
    if path.suffix in {".yaml", ".yml"}:
        return [load_yaml(path)]
    raise ValueError(f"unsupported fixture {path.name}")


def schema_for(path):
    if path.parent.name == "nodes":
        return "node.schema.json"
    prefixes = (
        ("project", "graph.schema.json"),
        ("graph", "graph.schema.json"),
        ("node", "node.schema.json"),
        ("journal", "journal-event.schema.json"),
        ("progress", "journal-event.schema.json"),
        ("acceptance", "acceptance-event.schema.json"),
        ("accepted", "acceptance-event.schema.json"),
        ("receipt", "receipt.schema.json"),
        ("verdict", "verdict.schema.json"),
    )
    for prefix, schema_name in prefixes:
        if path.name.startswith(prefix):
            return schema_name
    raise AssertionError(f"no schema for {path}")


def node_rules(path, node):
    if path.parent.name == "nodes" and path.stem != node["node_id"]:
        raise ValueError("filename must equal node_id")
    if node["node_id"] in node["depends_on"]:
        raise ValueError("self-dependency")
    criterion_ids = [item["id"] for item in node["acceptance_criteria"]]
    if len(criterion_ids) != len(set(criterion_ids)):
        raise ValueError("duplicate criterion id")


def acceptance_rules(events):
    node_ids = [event["node_id"] for event in events]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("duplicate acceptance")


def receipt_rules(path, receipt):
    if "receipts" not in path.parts:
        return
    if path.parent.name != receipt["node_id"]:
        raise ValueError("receipt directory must equal node_id")
    if path.stem != receipt["attempt_id"]:
        raise ValueError("receipt filename must equal attempt_id")


def ready_work(nodes, journal, acceptance):
    """Nodes ready to dispatch.

    ``nodes`` maps a node id to its ``depends_on`` list. ``journal`` and
    ``acceptance`` are event lists in file order. A node is ready when no
    acceptance line names it, its last journal status is not ``dispatched``,
    and every dependency has an acceptance line.
    """
    accepted = {event["node_id"] for event in acceptance}
    latest = {}
    for event in journal:
        latest[event["node_id"]] = event["status"]
    ready = []
    for node_id in sorted(nodes):
        if node_id in accepted or latest.get(node_id) == "dispatched":
            continue
        if all(dependency in accepted for dependency in nodes[node_id]):
            ready.append(node_id)
    return ready


def patterns(value, found):
    if isinstance(value, dict):
        pattern = value.get("pattern")
        if isinstance(pattern, str):
            found.append(pattern)
        for item in value.values():
            patterns(item, found)
    elif isinstance(value, list):
        for item in value:
            patterns(item, found)


def verdict_kinds(schema):
    constants = []
    enumerated = []
    for branch in schema["oneOf"]:
        kind = branch["properties"]["kind"]
        if "const" in kind:
            constants.append(kind["const"])
        if "enum" in kind:
            enumerated.extend(kind["enum"])
    return constants, enumerated


def receipt_for(verdict, node_id="record-acceptance", attempt_id="attempt-1"):
    return {
        "project_id": "close-loop",
        "node_id": node_id,
        "attempt_id": attempt_id,
        "generated_at": "2026-10-02T00:04:00Z",
        "actor": {"kind": "evaluator", "id": "deterministic"},
        "evidence": ["The attempt directory contains the cited artifact."],
        "verdict": verdict,
    }


def load_nodes(directory):
    nodes = {}
    for path in sorted(directory.glob("*.yaml")):
        node = load_yaml(path)
        nodes[node["node_id"]] = node["depends_on"]
    return nodes


def test_schema_field_sets(contract):
    schemas, _registry = contract
    graph = schemas["graph.schema.json"]
    node = schemas["node.schema.json"]
    journal = schemas["journal-event.schema.json"]
    acceptance = schemas["acceptance-event.schema.json"]
    receipt = schemas["receipt.schema.json"]
    assert graph["required"] == ["project_id"]
    assert set(graph["properties"]) == {"project_id", "intent", "repo"}
    assert node["required"] == ["node_id", "why", "depends_on", "acceptance_criteria"]
    assert set(node["properties"]) == {
        "node_id", "title", "why", "depends_on", "acceptance_criteria",
        "constraints", "required_artifacts",
    }
    assert "status" not in node["properties"]
    assert journal["properties"]["status"]["const"] == "dispatched"
    assert journal["required"] == ["project_id", "node_id", "status", "at", "actor"]
    assert set(journal["properties"]) == {
        "project_id", "node_id", "status", "at", "actor", "reason",
    }
    assert acceptance["properties"]["status"]["const"] == "accepted"
    assert acceptance["properties"]["actor"]["properties"]["kind"]["const"] == "human"
    assert receipt["properties"]["actor"]["properties"]["kind"]["const"] == "evaluator"
    assert receipt["properties"]["verdict"]["$ref"] == schemas["verdict.schema.json"]["$id"]
    assert "evidence" in receipt["required"]
    found = []
    for schema in schemas.values():
        patterns(schema, found)
    assert found
    assert set(found) <= {SLUG, TIMESTAMP}
    constants, enumerated = verdict_kinds(schemas["verdict.schema.json"])
    assert constants == ["pass", "fail"]
    assert enumerated == ACTIONS
    names = {path.name for path in SCHEMAS.iterdir()}
    assert not any("ready" in name or "frontier" in name for name in names)


def test_documented_examples_are_the_valid_fixtures():
    for document, fixture in QUOTED:
        text = fixture.read_text(encoding="utf-8").strip()
        assert text, fixture
        assert text in (DOCS / document).read_text(encoding="utf-8")


@pytest.mark.parametrize("path", VALID_FILES, ids=lambda path: path.relative_to(FIXTURES).as_posix())
def test_valid_fixture(path, contract):
    documents = instances(path)
    schema_name = schema_for(path)
    for document in documents:
        validate(document, schema_name, contract)
    if schema_name == "node.schema.json":
        node_rules(path, documents[0])
    if schema_name == "acceptance-event.schema.json":
        acceptance_rules(documents)


@pytest.mark.parametrize("path", INVALID_FILES, ids=lambda path: path.name)
def test_invalid_fixture_is_rejected(path, contract):
    try:
        documents = instances(path)
        for document in documents:
            validate(document, schema_for(path), contract)
    except (ValidationError, ValueError, json.JSONDecodeError):
        return
    raise AssertionError(f"{path.name} was accepted")


def test_node_yaml_with_status_is_rejected(contract):
    schemas, _registry = contract
    assert "status" not in schemas["node.schema.json"]["properties"]
    node = load_yaml(FIXTURES / "invalid" / "node-with-status.yaml")
    assert node["status"] == "accepted"
    rejects(node, "node.schema.json", contract)
    rejects(load_yaml(FIXTURES / "invalid" / "node-with-ready.yaml"), "node.schema.json", contract)
    rejects(load_yaml(FIXTURES / "invalid" / "graph-with-status.yaml"), "graph.schema.json", contract)


def test_only_a_human_can_produce_accepted(contract):
    accepted = instances(FIXTURES / "valid" / "acceptance.jsonl")[0]
    validate(accepted, "acceptance-event.schema.json", contract)
    rejects(accepted, "journal-event.schema.json", contract)
    without_attempt = {key: value for key, value in accepted.items() if key != "attempt_id"}
    rejects(without_attempt, "journal-event.schema.json", contract)
    rejects(instances(FIXTURES / "invalid" / "journal-accepted.jsonl")[0], "journal-event.schema.json", contract)

    for kind in ("system", "evaluator"):
        forged = json.loads(json.dumps(accepted))
        forged["actor"]["kind"] = kind
        rejects(forged, "acceptance-event.schema.json", contract)

    dispatched = instances(FIXTURES / "valid" / "journal.jsonl")[0]
    dispatched["actor"] = {"kind": "human", "id": "operator"}
    validate(dispatched, "journal-event.schema.json", contract)
    rejects(dispatched, "acceptance-event.schema.json", contract)
    rejects(instances(FIXTURES / "invalid" / "receipt-with-status.json")[0], "receipt.schema.json", contract)


@pytest.mark.parametrize("name,match", [
    ("self-dependency.yaml", "self-dependency"),
    ("duplicate-criteria.yaml", "duplicate criterion"),
    ("mismatched.yaml", "filename"),
])
def test_schema_valid_nodes_still_fail_cross_field_rules(name, match, contract):
    path = FIXTURES / "rules" / "nodes" / name
    node = load_yaml(path)
    validate(node, "node.schema.json", contract)
    with pytest.raises(ValueError, match=match):
        node_rules(path, node)


def test_duplicate_acceptance_line_is_rejected(contract):
    events = instances(FIXTURES / "rules" / "accepted-twice.jsonl")
    for event in events:
        validate(event, "acceptance-event.schema.json", contract)
    with pytest.raises(ValueError, match="duplicate acceptance"):
        acceptance_rules(events)


@pytest.mark.parametrize("path,match", [
    (FIXTURES / "rules" / "receipts" / "wrong" / "attempt-1.json", "directory"),
    (FIXTURES / "rules" / "receipts" / "record-acceptance" / "wrong-attempt.json", "filename"),
])
def test_receipt_path_must_match_ids(path, match, contract):
    receipt = json.loads(path.read_text(encoding="utf-8"))
    validate(receipt, "receipt.schema.json", contract)
    with pytest.raises(ValueError, match=match):
        receipt_rules(path, receipt)


def test_optional_fields_and_each_graph_action(contract):
    node = load_yaml(FIXTURES / "valid" / "nodes" / "record-acceptance.yaml")
    node["title"] = "Record acceptance"
    node["constraints"] = ["Leave status off the node file."]
    node["required_artifacts"] = ["docs/formats/graph.md"]
    validate(node, "node.schema.json", contract)
    graph = load_yaml(READY / "project.yaml")
    validate(graph, "graph.schema.json", contract)

    validate({"kind": "pass"}, "verdict.schema.json", contract)
    fail = json.loads((FIXTURES / "valid" / "verdict-fail.json").read_text(encoding="utf-8"))
    validate(receipt_for(fail), "receipt.schema.json", contract)
    for action in ACTIONS:
        verdict = {
            "kind": action,
            "affected_node_ids": ["record-acceptance"],
            "rationale": "The graph has to change before another attempt.",
            "evidence": ["The attempt diff falls outside the node criteria."],
        }
        validate(verdict, "verdict.schema.json", contract)
        validate(receipt_for(verdict), "receipt.schema.json", contract)


@pytest.mark.parametrize("kind", RETIRED_VERDICTS)
def test_retired_verdict_names_are_rejected(kind, contract):
    rejects({"kind": kind}, "verdict.schema.json", contract)


def test_journal_rejects_a_blank_line(tmp_path, contract):
    path = tmp_path / "progress.jsonl"
    path.write_text(
        '{"project_id":"close-loop","node_id":"root","status":"dispatched",'
        '"at":"2026-10-02T00:01:00Z","actor":{"kind":"system","id":"gdad"}}\n\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="blank"):
        instances(path)
    line = instances(FIXTURES / "valid" / "journal.jsonl")[0]
    line["at"] = "2026-10-02T00:01:00+00:00"
    rejects(line, "journal-event.schema.json", contract)


def test_ready_fixture_files_match_their_schemas(contract):
    validate(load_yaml(READY / "project.yaml"), "graph.schema.json", contract)
    project_id = load_yaml(READY / "project.yaml")["project_id"]
    for path in sorted((READY / "nodes").glob("*.yaml")):
        node = load_yaml(path)
        validate(node, "node.schema.json", contract)
        node_rules(path, node)
        assert "status" not in node
        assert "ready" not in node
    journal = instances(READY / "progress.jsonl")
    acceptance = instances(READY / "accepted.jsonl")
    for event in journal:
        validate(event, "journal-event.schema.json", contract)
        assert event["project_id"] == project_id
    for event in acceptance:
        validate(event, "acceptance-event.schema.json", contract)
        assert event["project_id"] == project_id
    acceptance_rules(acceptance)
    receipts = {}
    for path in sorted((READY / "receipts").rglob("*.json")):
        receipt = json.loads(path.read_text(encoding="utf-8"))
        validate(receipt, "receipt.schema.json", contract)
        receipt_rules(path, receipt)
        assert receipt["project_id"] == project_id
        receipts[receipt["node_id"]] = receipt
    for event in acceptance:
        cited = receipts[event["node_id"]]
        assert cited["attempt_id"] == event["attempt_id"]
    names = {path.name for path in files(READY)}
    assert "ready.yaml" not in names
    assert "frontier.yaml" not in names


def test_ready_work_is_derived_from_dependencies_acceptance_and_journal():
    nodes = load_nodes(READY / "nodes")
    journal = instances(READY / "progress.jsonl")
    acceptance = instances(READY / "accepted.jsonl")
    assert ready_work(nodes, journal, acceptance) == ["child"]
    assert ready_work(nodes, [], []) == ["root", "sibling"]
    assert ready_work(nodes, journal, []) == []
    assert ready_work(nodes, [], acceptance) == ["child", "sibling"]

    sibling = json.loads((READY / "receipts" / "sibling" / "attempt-2.json").read_text(encoding="utf-8"))
    assert sibling["verdict"] == {"kind": "pass"}
    assert "sibling" not in ready_work(nodes, journal, acceptance)
    assert "root" not in ready_work(nodes, journal, acceptance)

    twice = journal + [dict(journal[0])]
    assert ready_work({"root": []}, twice, []) == []
    assert ready_work({"a": ["b"], "b": ["a"]}, [], []) == []
    assert ready_work({"root": [], "child": ["missing"]}, [], []) == ["root"]
    assert ready_work({}, [], []) == []
