# tests/schema-validation/test_graph_schema.py
import json, os, pytest
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load(name):
    with open(os.path.join(SKILL, name)) as f:
        return json.load(f)

def test_valid_graph_passes():
    jsonschema.validate(load("tests/schema-validation/fixtures/valid_graph.json"), load("graph.schema.json"))

def test_missing_nodes_fails():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"version": "1.0.0", "edges": []}, load("graph.schema.json"))

def test_missing_edges_fails():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"version": "1.0.0", "nodes": []}, load("graph.schema.json"))
