# tests/schema-validation/test_dry_run_plan_schema.py
import json, os, pytest
import jsonschema

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_schema():
    with open(os.path.join(SKILL, "schemas/dry-run-plan-v1.schema.json")) as f:
        return json.load(f)

def load_fixture(name):
    with open(os.path.join(SKILL, f"tests/schema-validation/fixtures/{name}.json")) as f:
        return json.load(f)

def test_valid_dry_run_plan_passes():
    jsonschema.validate(load_fixture("valid_dry_run_plan"), load_schema())

def test_count_mismatch_fixture_has_mismatch():
    doc = load_fixture("invalid_dry_run_plan_count_mismatch")
    ts = doc["triage_summary"]
    computed = ts["tier_1_count"] + ts["tier_2_count"] + ts["tier_3_count"] + ts["deferred_at_triage"]
    assert ts["total_findings"] != computed, "fixture should encode a count mismatch"

def test_flags_must_include_dry_run():
    schema = load_schema()
    bad = load_fixture("valid_dry_run_plan")
    bad["flags"] = ["verbose"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_count_sum_invariant_valid_fixture():
    doc = load_fixture("valid_dry_run_plan")
    ts = doc["triage_summary"]
    expected = ts["tier_1_count"] + ts["tier_2_count"] + ts["tier_3_count"] + ts["deferred_at_triage"]
    assert ts["total_findings"] == expected, f"count mismatch: {ts['total_findings']} != {expected}"

def test_count_sum_invariant_invalid_fixture_catches_mismatch():
    doc = load_fixture("invalid_dry_run_plan_count_mismatch")
    ts = doc["triage_summary"]
    expected = ts["tier_1_count"] + ts["tier_2_count"] + ts["tier_3_count"] + ts["deferred_at_triage"]
    assert ts["total_findings"] != expected, "expected fixture to have a mismatch"
