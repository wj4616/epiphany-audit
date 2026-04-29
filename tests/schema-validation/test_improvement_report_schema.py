# tests/schema-validation/test_improvement_report_schema.py
import json, os, pytest
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_schema():
    with open(os.path.join(SKILL, "schemas/improvement-report-v1.schema.json")) as f:
        return json.load(f)

def load_fixture(name):
    with open(os.path.join(SKILL, f"tests/schema-validation/fixtures/{name}.json")) as f:
        return json.load(f)

def test_valid_improvement_report_passes():
    jsonschema.validate(load_fixture("valid_improvement_report"), load_schema())

def test_count_sum_invariant_fixture_has_mismatch():
    doc = load_fixture("invalid_improvement_report_count_mismatch")
    ts = doc
    expected_survivors = ts["notable"] + ts["quick_wins"] + ts["worthwhile"]
    assert ts["survivors"] != expected_survivors, "fixture should have mismatch"

def test_flags_must_include_improve():
    schema = load_schema()
    bad = load_fixture("valid_improvement_report")
    bad["flags"] = ["verbose"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_invalid_category_fails():
    schema = load_schema()
    bad = load_fixture("valid_improvement_report")
    bad["body"][0]["category"] = "legendary"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_count_sum_invariant_valid():
    doc = load_fixture("valid_improvement_report")
    assert doc["survivors"] == doc["notable"] + doc["quick_wins"] + doc["worthwhile"]
    assert doc["total_candidates"] == doc["filtered_out"] + doc["survivors"]
