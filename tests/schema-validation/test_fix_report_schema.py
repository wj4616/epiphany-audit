# tests/schema-validation/test_fix_report_schema.py
import json, os, pytest
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_schema():
    with open(os.path.join(SKILL, "schemas/fix-report-v1.schema.json")) as f:
        return json.load(f)

def load_fixture(name):
    with open(os.path.join(SKILL, f"tests/schema-validation/fixtures/{name}.json")) as f:
        return json.load(f)

def test_valid_fix_report_passes():
    jsonschema.validate(load_fixture("valid_fix_report"), load_schema())

def test_partial_true_requires_halt_state():
    schema = load_schema()
    bad = load_fixture("invalid_fix_report_partial_invariant")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_invalid_status_fails():
    schema = load_schema()
    bad = load_fixture("valid_fix_report")
    bad["body"][0]["status"] = "UNKNOWN"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_invalid_flags_combination_fails():
    schema = load_schema()
    bad = load_fixture("valid_fix_report")
    bad["flags"] = ["auto", "confirm-all"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
