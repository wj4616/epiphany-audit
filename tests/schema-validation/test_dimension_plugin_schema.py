# tests/schema-validation/test_dimension_plugin_schema.py
import json, os, pytest
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_schema():
    with open(os.path.join(SKILL, "schemas/dimension-plugin-v1.schema.json")) as f:
        return json.load(f)

def load_fixture(name):
    with open(os.path.join(SKILL, f"tests/schema-validation/fixtures/{name}.json")) as f:
        return json.load(f)

def test_valid_plugin_passes():
    jsonschema.validate(load_fixture("valid_dimension_plugin"), load_schema())

def test_missing_activation_triggers_fails():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(load_fixture("invalid_dimension_plugin_missing_triggers"), load_schema())

def test_invalid_priority_fails():
    schema = load_schema()
    bad = load_fixture("valid_dimension_plugin")
    bad["priority"] = "ultra"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
